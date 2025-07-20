#!/usr/bin/env python3
"""
Command-line entry point for the torrent streamer.
"""
import sys

from downloader import TorrentDownloader
from engine import TorrentEngine
from player import VLCPlayer
from ui import ConsoleUI, UI
from controller import TorrentStreamerController


def main() -> int:
    # UI handles CLI args and user interactions
    ui: UI = ConsoleUI()
    magnet, save_path = ui.get_parameters()

    engine = TorrentEngine(save_path)
    downloader = TorrentDownloader(engine)
    player = VLCPlayer()
    controller = TorrentStreamerController(engine, downloader, player, ui)
    controller.stream(magnet, save_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())