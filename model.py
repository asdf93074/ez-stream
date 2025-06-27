"""
Data models for the torrent streaming layers.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class TorrentFile:
    """Represents a single file within a torrent."""
    index: int
    path: str
    size: int


@dataclass
class TorrentMetadata:
    """High-level metadata for a torrent."""
    name: str
    piece_size: int
    files: List[TorrentFile]


@dataclass
class DownloadStats:
    """Live download statistics for a file."""
    downloaded: int
    total: int
    percent: float
    rate: float


def sizeof_fmt(num: int, suffix: str = 'B') -> str:
    """Human-readable file size."""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"