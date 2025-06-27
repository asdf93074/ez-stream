"""
Torrent engine abstraction using python-libtorrent.
"""
import time
import libtorrent as lt

from model import TorrentFile, TorrentMetadata, DownloadStats


class TorrentEngine:
    """Handles interaction with libtorrent for metadata and streaming."""

    def __init__(self, save_path: str):
        self.save_path = save_path
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.handle = None

    def add_magnet(self, magnet_uri: str) -> None:
        """Add a magnet URI to the session (async)."""
        params = {
            'save_path': self.save_path,
            'storage_mode': lt.storage_mode_t.storage_mode_sparse,
        }
        self.handle = lt.add_magnet_uri(self.session, magnet_uri, params)

    def fetch_metadata(self) -> TorrentMetadata:
        """Block until torrent metadata is available and return it."""
        assert self.handle, "Magnet URI must be added first"
        while not self.handle.has_metadata():
            time.sleep(1)
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