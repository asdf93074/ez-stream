"""
Controller layer for the torrent streamer: ties engine, UI, and player together.
"""
import os
import time

from model import TorrentMetadata, DownloadStats
from engine import TorrentEngine
from player import Player
from ui import UI


class TorrentStreamerController:
    """Orchestrates torrent download and playback using provided layers."""

    def __init__(
        self,
        engine: TorrentEngine,
        player: Player,
        ui: UI,
    ):
        self.engine = engine
        self.player = player
        self.ui = ui

    def stream(self, magnet: str, save_path: str) -> None:
        # add magnet and fetch metadata
        self.engine.add_magnet(magnet)
        self.ui.show_fetching_metadata()
        metadata: TorrentMetadata = self.engine.fetch_metadata()
        self.ui.show_metadata(metadata.name)

        # list files and choose one
        self.ui.list_files(metadata.files)
        choice = self.ui.prompt_file_choice(len(metadata.files) - 1)

        # instruct engine to prioritize only that file
        offset, file_size = self.engine.select_file(choice)
        rel_path = metadata.files[choice].path
        abs_path = os.path.abspath(os.path.join(save_path, rel_path))
        self.ui.show_selected_file(choice, rel_path, abs_path)

        # buffer header piece
        first_piece = offset // metadata.piece_size
        self.ui.buffering_header()
        self.engine.wait_piece(first_piece)
        self.ui.newline()

        # launch player
        self.ui.show_launching_player()
        proc = self.player.play(abs_path)

        # queue remaining pieces sequentially for streaming
        last_piece = (offset + file_size - 1) // metadata.piece_size
        self.engine.schedule_pieces(first_piece + 1, last_piece)

        # monitor download progress until player exits
        try:
            while proc.poll() is None:
                stats: DownloadStats = self.engine.get_progress(choice, file_size)
                self.ui.show_progress(stats)
                time.sleep(1)
            self.ui.newline()
        except KeyboardInterrupt:
            pass