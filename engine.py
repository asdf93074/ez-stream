"""
Torrent engine abstraction using python-libtorrent.
"""
import os
import time
import libtorrent as lt

from model import TorrentFile, TorrentMetadata, DownloadStats


class TorrentEngine:
    """Handles interaction with libtorrent for metadata and streaming."""

    def __init__(self, save_path: str):
        self.save_path = save_path
        self.resume_dir = os.path.join(save_path, ".resume")
        os.makedirs(self.resume_dir, exist_ok=True)

        settings = {
            "user_agent": "ez-stream/0.1.0",
            "listen_interfaces": "0.0.0.0:6881",
            "enable_dht": True,
            "alert_mask": lt.alert_category.all,
        }
        self.session = lt.session(settings)
        self.handle = None

    def add_magnet(self, magnet_uri: str) -> None:
        """Add a magnet URI to the session, loading resume data if available."""
        magnet_params = lt.parse_magnet_uri(magnet_uri)
        info_hash_str = str(magnet_params.info_hashes.v1)
        resume_file = os.path.join(self.resume_dir, f"{info_hash_str}.fastresume")

        if os.path.exists(resume_file):
            with open(resume_file, "rb") as f:
                resume_data = f.read()
            try:
                params = lt.read_resume_data(resume_data)
                # Add trackers from magnet link to the resumed session
                params.trackers.extend([t.url for t in magnet_params.trackers])
                params.dht_nodes.extend(magnet_params.dht_nodes)
            except Exception:
                # If resume data is corrupt, start fresh
                params = magnet_params
        else:
            params = magnet_params

        params.save_path = self.save_path
        params.storage_mode = lt.storage_mode_t.storage_mode_sparse
        self.handle = self.session.add_torrent(params)

    def fetch_metadata(self) -> TorrentMetadata:
        """Block until torrent metadata is available and return it."""
        assert self.handle, "Magnet URI must be added first"
        while not self.handle.has_metadata():
            self.session.pop_alerts() # Clear alerts to avoid buffer buildup
            time.sleep(0.1)
        info = self.handle.get_torrent_info()
        piece_size = info.piece_length()
        files = []
        storage = info.files()
        for idx in range(storage.num_files()):
            files.append(
                TorrentFile(
                    index=idx,
                    path=storage.file_path(idx),
                    size=storage.file_size(idx),
                )
            )
        return TorrentMetadata(name=info.name(), piece_size=piece_size, files=files)

    def select_file(self, index: int) -> tuple[int, int]:
        """Prioritize a single file by index; return its offset and size."""
        assert self.handle, "Magnet URI must be added first"
        info = self.handle.get_torrent_info()
        storage = info.files()
        count = storage.num_files()
        if index < 0 or index >= count:
            raise IndexError(f"file index {index} out of range")
        priorities = [0] * count
        priorities[index] = 1
        self.handle.prioritize_files(priorities)
        file_offset = storage.file_offset(index)
        file_size = storage.file_size(index)
        return file_offset, file_size

    def wait_piece(self, piece: int, timeout: float = 0.2) -> None:
        """Block until the given piece index has been downloaded."""
        self.handle.set_piece_deadline(piece, 0)
        while not self.handle.have_piece(piece):
            time.sleep(timeout)

    def schedule_pieces(self, start: int, end: int) -> None:
        """Queue the remaining pieces so they download sequentially."""
        for i, piece in enumerate(range(start, end + 1), start=1):
            self.handle.set_piece_deadline(piece, i * 1000)

    def get_progress(self, file_index: int, file_size: int) -> DownloadStats:
        """Return the current download stats for the selected file."""
        downloaded = self.handle.file_progress()[file_index]
        rate = self.handle.status().download_rate
        percent = (downloaded / file_size * 100) if file_size else 0.0
        return DownloadStats(
            downloaded=downloaded,
            total=file_size,
            percent=percent,
            rate=rate,
        )

    def save_resume_data(self):
        """Saves the resume data for the current torrent to a file."""
        if not (self.handle and self.handle.is_valid() and self.handle.has_metadata()):
            return

        self.handle.save_resume_data(lt.save_resume_flags_t.save_info_dict)

        start_time = time.time()
        while time.time() - start_time < 5:  # 5-second timeout
            alerts = self.session.pop_alerts()
            for alert in alerts:
                if isinstance(alert, lt.save_resume_data_alert):
                    entry = lt.write_resume_data(alert.params)
                    data = lt.bencode(entry)
                    info_hash_str = str(alert.params.info_hashes.v1)
                    resume_file = os.path.join(self.resume_dir, f"{info_hash_str}.fastresume")
                    with open(resume_file, "wb") as f:
                        f.write(data)
                    return
            time.sleep(0.2)

    def close(self):
        """Save resume data and clean up the session."""
        self.save_resume_data()
        if self.handle and self.handle.is_valid():
            self.session.remove_torrent(self.handle)