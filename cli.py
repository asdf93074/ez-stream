"""
Command-line interface layer for the torrent streamer.
"""
import argparse
import os
import time
import sys
import subprocess

from model import sizeof_fmt, TorrentMetadata, DownloadStats
from engine import TorrentEngine
from player import VLCPlayer, Player


def list_files(metadata: TorrentMetadata) -> None:
    """Print an indexed listing of files in the torrent."""
    for f in metadata.files:
        print(f"[{f.index}] {f.path} ({sizeof_fmt(f.size)})")


def prompt_choice(max_index: int) -> int:
    """Prompt the user to enter a valid file index."""
    try:
        choice = int(input('Select file index to stream: '))
    except ValueError:
        raise ValueError('Invalid selection')
    if choice < 0 or choice > max_index:
        raise IndexError('Index out of range')
    return choice


def monitor_progress(
    engine: TorrentEngine,
    file_index: int,
    file_size: int,
    player_proc: subprocess.Popen,
) -> None:
    """Show live download stats until the player process exits."""
    try:
        while player_proc.poll() is None:
            stats: DownloadStats = engine.get_progress(file_index, file_size)
            print(
                f"\rDownloaded {sizeof_fmt(stats.downloaded)} / "
                f"{sizeof_fmt(stats.total)} ({stats.percent:.1f}%), "
                f"rate {sizeof_fmt(stats.rate)}/s",
                end='',
                flush=True,
            )
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(
        description='Stream a file from a magnet link via a pluggable player.'
    )
    parser.add_argument('magnet', help='Magnet link to the torrent')
    parser.add_argument(
        '--save-path', '-o', default='.', help='Directory to save partial downloads'
    )
    args = parser.parse_args()

    engine = TorrentEngine(args.save_path)
    engine.add_magnet(args.magnet)
    print('Fetching metadata...')
    metadata: TorrentMetadata = engine.fetch_metadata()
    print(f"Metadata received: {metadata.name}")

    list_files(metadata)
    try:
        choice = prompt_choice(len(metadata.files) - 1)
    except (ValueError, IndexError) as e:
        print(e)
        sys.exit(1)

    offset, file_size = engine.select_file(choice)
    entry = metadata.files[choice]
    rel_path = entry.path
    full_path = os.path.join(args.save_path, rel_path)
    abs_path = os.path.abspath(full_path)
    print(f'Selected file [{choice}]: {rel_path}')
    print(f'Streaming from: {abs_path}')

    # fetch header piece for fast startup
    first_piece = offset // metadata.piece_size
    print('Buffering header', end='', flush=True)
    engine.wait_piece(first_piece)
    print()

    # play via VLC (could be swapped for another Player)
    player: Player = VLCPlayer()
    player_proc = player.play(abs_path)

    # queue remaining pieces sequentially for streaming
    last_piece = (offset + file_size - 1) // metadata.piece_size
    engine.schedule_pieces(first_piece + 1, last_piece)

    # show live download stats until playback ends
    monitor_progress(engine, choice, file_size, player_proc)


if __name__ == '__main__':
    main()