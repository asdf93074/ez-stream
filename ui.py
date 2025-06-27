"""
Console UI layer for the torrent streamer.
"""
import argparse
import time
from abc import ABC, abstractmethod

from model import TorrentFile, DownloadStats, sizeof_fmt


class UI(ABC):
    """Abstract interface for all UI implementations."""

    @abstractmethod
    def get_parameters(self) -> tuple[str, str]:
        """Obtain the magnet link and save path from the user or CLI args."""
        pass

    @abstractmethod
    def show_fetching_metadata(self) -> None:
        pass

    @abstractmethod
    def show_metadata(self, name: str) -> None:
        pass

    @abstractmethod
    def list_files(self, files: list[TorrentFile]) -> None:
        pass

    @abstractmethod
    def prompt_file_choice(self, max_index: int) -> int:
        pass

    @abstractmethod
    def show_selected_file(self, index: int, rel_path: str, abs_path: str) -> None:
        pass

    @abstractmethod
    def buffering_header(self) -> None:
        pass

    @abstractmethod
    def show_launching_player(self) -> None:
        pass

    @abstractmethod
    def show_progress(self, stats: DownloadStats) -> None:
        pass

    @abstractmethod
    def newline(self) -> None:
        pass


class ConsoleUI(UI):
    """Handles all console-based user interactions and displays."""

    def get_parameters(self) -> tuple[str, str]:
        parser = argparse.ArgumentParser(
            description='Stream a file from a magnet link via a pluggable player.'
        )
        parser.add_argument('magnet', help='Magnet link to the torrent')
        parser.add_argument(
            '--save-path', '-o', default='.', help='Directory to save partial downloads'
        )
        args = parser.parse_args()
        return args.magnet, args.save_path

    def show_fetching_metadata(self) -> None:
        print('Fetching metadata...')

    def show_metadata(self, name: str) -> None:
        print(f"Metadata received: {name}")

    def list_files(self, files: list[TorrentFile]) -> None:
        for f in files:
            print(f"[{f.index}] {f.path} ({sizeof_fmt(f.size)})")

    def prompt_file_choice(self, max_index: int) -> int:
        try:
            choice = int(input('Select file index to stream: '))
        except ValueError:
            raise ValueError('Invalid selection')
        if choice < 0 or choice > max_index:
            raise IndexError('Index out of range')
        return choice

    def show_selected_file(self, index: int, rel_path: str, abs_path: str) -> None:
        print(f'Selected file [{index}]: {rel_path}')
        print(f'Streaming from: {abs_path}')

    def buffering_header(self) -> None:
        print('Buffering header', end='', flush=True)

    def show_launching_player(self) -> None:
        print('Launching player...')

    def show_progress(self, stats: DownloadStats) -> None:
        print(
            f"\rDownloaded {sizeof_fmt(stats.downloaded)} / {sizeof_fmt(stats.total)} "
            f"({stats.percent:.1f}%), rate {sizeof_fmt(stats.rate)}/s",
            end='',
            flush=True,
        )

    def newline(self) -> None:
        print()