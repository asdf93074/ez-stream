_This project was vibecoded with OpenAI's Codex CLI + Gemini + 10% manual coding._

---

# EZ-Stream

A simple torrent streamer with a CLI, GUI (Python), and a web-based GUI (WIP) now too!

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

For the GUI, ensure Tkinter is installed. On some Linux distributions, you might need to install it via your system's package manager (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu).

## Usage

### CLI

```bash
python cli.py "magnet:?xt=urn:btih:..."
```

### GUI

```bash
python gui.py
```
1. Enter the magnet link in the GUI. Set a save directory (optional).

2. Press the button to have it fetch all the files in the torrent.

3. Right click a file and press play to have it start bufferring. It will open VLC when its ready.
