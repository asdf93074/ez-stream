_This project was vibecoded with OpenAI's Codex CLI._

---

# EZ-Stream

A simple torrent streamer with a CLI and GUI.

## Features

*   Stream torrents directly from a magnet link.
*   Choose which file to stream from a torrent with multiple files.
*   Command-line and GUI interfaces.
*   Uses libtorrent for the torrent engine and VLC for playback.

## Installation

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
python cli.py "magnet:?xt=urn:btih:..."
```

### GUI

```bash
python gui.py
```
