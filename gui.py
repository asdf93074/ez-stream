import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from model import TorrentFile, DownloadStats, sizeof_fmt
from ui import UI
from engine import TorrentEngine
from player import VLCPlayer
from controller import TorrentStreamerController


class GUIUI(UI):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Torrent Streamer GUI")
        self.root.geometry("600x400")

        self.magnet = tk.StringVar()
        self.save_path = tk.StringVar(value=".")

        # For context-menu based file selection
        self._choice_event = threading.Event()
        self._choice = None
        self._file_list = []

        self._setup_ui()

    def _setup_ui(self):
        # Magnet link
        tk.Label(self.root, text="Magnet Link:").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(self.root, textvariable=self.magnet, width=80).pack(padx=10, pady=5)

        # Save path
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=10)
        tk.Label(frame, text="Save Path:").pack(side="left")
        tk.Entry(frame, textvariable=self.save_path, width=50).pack(side="left", padx=5)
        tk.Button(frame, text="Browse", command=self._browse_path).pack(side="left")

        # Start button
        tk.Button(self.root, text="Start Streaming", command=self._start_streaming).pack(pady=10)

        # Status area
        self._status = tk.Label(self.root, text="Idle", anchor="w")
        self._status.pack(fill="x", padx=10)

        # File listbox with context menu
        self._file_listbox = tk.Listbox(self.root)
        self._file_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self._file_listbox.bind("<Button-3>", self._on_right_click)

        self._menu = tk.Menu(self.root, tearoff=0)
        self._menu.add_command(label="Play", command=self._play_selected)

        # Progress label
        self._progress_label = tk.Label(self.root, text="", anchor="w")
        self._progress_label.pack(fill="x", padx=10, pady=(0, 10))

    def _browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path.set(path)

    def _start_streaming(self):
        if not self.magnet.get():
            messagebox.showerror("Error", "Please enter a magnet link.")
            return

        threading.Thread(target=self._run_controller, daemon=True).start()

    def _run_controller(self):
        engine = TorrentEngine(self.save_path.get())
        player = VLCPlayer()
        controller = TorrentStreamerController(engine, player, self)
        controller.stream(self.magnet.get(), self.save_path.get())

    def get_parameters(self) -> tuple[str, str]:
        return self.magnet.get(), self.save_path.get()

    def show_fetching_metadata(self) -> None:
        self._update_status("Fetching metadata...")

    def show_metadata(self, name: str) -> None:
        self._update_status(f"Metadata received: {name}")

    def list_files(self, files: list[TorrentFile]) -> None:
        self._file_list = files
        self._file_listbox.delete(0, tk.END)
        for f in files:
            self._file_listbox.insert(tk.END, f"[{f.index}] {f.path} ({sizeof_fmt(f.size)})")

    def prompt_file_choice(self, max_index: int) -> int:
        # Wait until user selects via context menu
        self._choice_event.clear()
        self._choice_event.wait()

        choice = self._choice
        if choice is None:
            raise ValueError("No selection made")
        if choice < 0 or choice > max_index:
            raise IndexError("Index out of range")
        return choice

    def _on_right_click(self, event):
        # Show context menu on right click
        try:
            idx = self._file_listbox.nearest(event.y)
            # select the clicked line
            self._file_listbox.selection_clear(0, tk.END)
            self._file_listbox.selection_set(idx)
            self._menu.post(event.x_root, event.y_root)
            self._current_idx = idx
        except tk.TclError:
            pass

    def _play_selected(self):
        # Called by context menu "Play"
        idx = getattr(self, '_current_idx', None)
        if idx is not None:
            self.buffering_header()
            self._choice = self._file_list[idx].index
            self._menu.unpost()
            self._choice_event.set()

    def show_selected_file(self, index: int, rel_path: str, abs_path: str) -> None:
        self._update_status(f"Selected file [{index}]: {rel_path}\nStreaming from: {abs_path}")

    def buffering_header(self) -> None:
        self._update_status("Buffering header...")

    def show_launching_player(self) -> None:
        self._update_status("Launching player...")

    def show_progress(self, stats: DownloadStats) -> None:
        text = (
            f"Downloaded {sizeof_fmt(stats.downloaded)} / {sizeof_fmt(stats.total)} "
            f"({stats.percent:.1f}%), rate {sizeof_fmt(stats.rate)}/s"
        )
        self._progress_label.config(text=text)

    def newline(self) -> None:
        self._update_status("")

    def _update_status(self, text: str):
        self._status.config(text=text)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ui = GUIUI()
    ui.run()

