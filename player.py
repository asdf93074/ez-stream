"""
Player abstraction and implementations for streaming.
"""
import subprocess
import sys


class Player:
    """Interface for a media player."""

    def play(self, path: str) -> subprocess.Popen:
        """Start playing the given file path, returning the process handle."""
        raise NotImplementedError


class VLCPlayer(Player):
    """Use VLC to play media files."""

    def play(self, path: str) -> subprocess.Popen:
        try:
            return subprocess.Popen(['vlc', '--play-and-exit', path])
        except FileNotFoundError:
            print('VLC not found. Please ensure VLC is installed and in your PATH.')
            sys.exit(1)