"""
Downloader service for handling the torrent session and file download.
"""
import os
from typing import Union

from model import TorrentMetadata, TorrentFile
from engine import TorrentEngine


class TorrentDownloader:
    """A service to manage downloading a specific file from a torrent."""

    def __init__(self, engine: TorrentEngine):
        self.engine = engine

    def download_file(
        self, metadata: TorrentMetadata, file_choice: Union[int, str], save_path: str
    ) -> tuple[str, int, int]:
        """
        Selects a file from the torrent, starts downloading it, and returns the
        absolute path to the file on disk, its index, and its size.
        """
        file_index = self._resolve_file_choice(metadata.files, file_choice)
        chosen_file = metadata.files[file_index]

        offset, file_size = self.engine.select_file(file_index)

        # Buffer header piece
        first_piece = offset // metadata.piece_size
        self.engine.wait_piece(first_piece)

        # Queue remaining pieces sequentially for streaming
        last_piece = (offset + file_size - 1) // metadata.piece_size
        self.engine.schedule_pieces(first_piece + 1, last_piece)

        abs_path = os.path.abspath(os.path.join(save_path, chosen_file.path))
        return abs_path, file_index, chosen_file.size

    def _resolve_file_choice(
        self, files: list[TorrentFile], choice: Union[int, str]
    ) -> int:
        """Resolves a user's file choice (int or str) to a file index."""
        if isinstance(choice, int):
            if 0 <= choice < len(files):
                return choice
            else:
                raise IndexError(f"File index {choice} is out of range.")

        if isinstance(choice, str):
            for file in files:
                if choice in file.path:
                    return file.index
            raise FileNotFoundError(f"No file found matching '{choice}'.")

        raise TypeError("File choice must be an integer index or string name.")
