"""
Controller layer for the torrent streamer: ties engine, UI, and player together.
"""
import time
from typing import Union

from model import DownloadStats
from downloader import TorrentDownloader
from engine import TorrentEngine
from player import Player
from ui import UI


class TorrentStreamerController:
    """Orchestrates torrent download and playback using provided layers."""

    def __init__(
        self,
        engine: TorrentEngine,
        downloader: TorrentDownloader,
        player: Player,
        ui: UI,
    ):
        self.engine = engine
        self.downloader = downloader
        self.player = player
        self.ui = ui

    def stream(self, magnet: str, save_path: str) -> None:
        # add magnet and fetch metadata
        self.engine.add_magnet(magnet)
        self.ui.show_fetching_metadata()
        metadata = self.engine.fetch_metadata()
        self.ui.show_metadata(metadata.name)

        # list files and choose one
        self.ui.list_files(metadata.files)
        choice: Union[int, str] = self.ui.prompt_file_choice(len(metadata.files) - 1)

        # download the file and get its path
        self.ui.buffering_header()
        abs_path, file_index, file_size = self.downloader.download_file(
            metadata, choice, save_path
        )
        self.ui.newline()
        self.ui.show_selected_file(
            file_index, metadata.files[file_index].path, abs_path
        )

        # launch player
        self.ui.show_launching_player()
        proc = self.player.play(abs_path)

        # monitor download progress until player exits
        try:
            while proc.poll() is None:
                stats: DownloadStats = self.engine.get_progress(file_index, file_size)
                self.ui.show_progress(stats)
                time.sleep(1)
            self.ui.newline()
        except KeyboardInterrupt:
            pass