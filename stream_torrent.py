#!/usr/bin/env python3
"""
Stream a video file from a torrent magnet link via VLC.

This script fetches torrent metadata, lists files in the torrent,
lets you select a video file, fetches the header piece for fast startup,
streams it via VLC with live download-progress updates,
and keeps downloading until VLC exits.

Requires:
    - python-libtorrent (install via pip)
    - VLC media player accessible in PATH
"""
import argparse
import libtorrent as lt
import os
import subprocess
import sys
import time

def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"

def main():
    parser = argparse.ArgumentParser(
        description="Stream a file from a magnet link via VLC. Requires VLC installed and in PATH."
    )
    parser.add_argument('magnet', help='Magnet link to the torrent')
    parser.add_argument(
        '--save-path', '-o',
        default='.', help='Directory to save partial downloads'
    )
    args = parser.parse_args()

    session = lt.session()
    session.listen_on(6881, 6891)
    params = {
        'save_path': args.save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    handle = lt.add_magnet_uri(session, args.magnet, params)
    print('Fetching metadata...')
    while not handle.has_metadata():
        time.sleep(1)

    info = handle.get_torrent_info()
    # determine piece size so we can fetch file headers piece-by-piece
    piece_len = info.piece_length()
    print(f"Metadata received: {info.name()}")

    files = info.files()
    count = files.num_files()
    for idx in range(count):
        path = files.file_path(idx)
        size = sizeof_fmt(files.file_size(idx))
        print(f"[{idx}] {path} ({size})")

    try:
        choice = int(input('Select file index to stream: '))
    except ValueError:
        print('Invalid selection')
        sys.exit(1)

    if not (0 <= choice < count):
        print('Index out of range')
        sys.exit(1)

    # only download the selected file
    priorities = [0] * count
    priorities[choice] = 1
    handle.prioritize_files(priorities)

    # calculate piece range for the chosen file
    file_offset = files.file_offset(choice)
    file_size = files.file_size(choice)
    first_piece = file_offset // piece_len
    last_piece = (file_offset + file_size - 1) // piece_len

    rel_path = files.file_path(choice)
    full_path = os.path.join(args.save_path, rel_path)
    abs_path = os.path.abspath(full_path)
    print(f'Selected file [{choice}]: {rel_path}')
    print(f'Streaming from: {abs_path}')

    # fetch the first piece containing the file header
    print('Buffering header', end='', flush=True)
    handle.set_piece_deadline(first_piece, 0)
    while not handle.have_piece(first_piece):
        print('.', end='', flush=True)
        time.sleep(0.2)
    print()  # newline

    # launch VLC and then queue the rest of the pieces for streaming
    print('Launching VLC...')
    try:
        vlc_proc = subprocess.Popen(['vlc', '--play-and-exit', abs_path])
    except FileNotFoundError:
        print('VLC not found. Please ensure VLC is installed and in your PATH.')
        sys.exit(1)

    # schedule remaining pieces sequentially so playback can continue
    for idx, piece in enumerate(range(first_piece + 1, last_piece + 1), start=1):
        handle.set_piece_deadline(piece, idx * 1000)

    # monitor download progress while VLC is playing
    try:
        while vlc_proc.poll() is None:
            # file_progress() returns downloaded bytes per file
            file_prog = handle.file_progress()[choice]
            percent = (file_prog / file_size * 100) if file_size else 0
            rate = handle.status().download_rate
            print(f"\rDownloaded {sizeof_fmt(file_prog)} / {sizeof_fmt(file_size)} "
                  f"({percent:.1f}%), rate {sizeof_fmt(rate)}/s", end='', flush=True)
            time.sleep(1)
        print()  # newline after playback ends
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()