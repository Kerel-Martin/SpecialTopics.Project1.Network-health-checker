"""Optional Tkinter window for the prototype.

SPEC.md treats the GUI as an optional enhancement; the command-line
interface in cli.py remains the required interface.
"""

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .loader import MAX_ENTRIES, InputFileError, load_targets
from .pinger import DEFAULT_TIMEOUT_MS, PingUnavailableError, ping
from .scanner import describe_response, scan, summarize


class CheckerWindow:
    def __init__(self, root, timeout_ms=DEFAULT_TIMEOUT_MS, ping_func=ping):
        self.root = root
        self.timeout_ms = timeout_ms
        self.ping_func = ping_func
        self.texts = []
        self.scanning = False
        # The scan runs in a background thread so the window does not freeze;
        # the thread hands its results back through this queue.
        self.outcomes = queue.Queue()

        root.title("Network Health Checker - Prototype")
        root.geometry("680x420")

        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        ttk.Button(top, text="Open address file...", command=self.choose_file).pack(side="left")
        self.scan_button = ttk.Button(top, text="Scan again", command=self.start_scan)
        self.scan_button.pack(side="left", padx=(8, 0))
        self.scan_button.state(["disabled"])
        self.file_label = ttk.Label(top, text=f"No file loaded (max {MAX_ENTRIES} addresses)")
        self.file_label.pack(side="left", padx=8)

        columns = ("address", "status", "response")
        self.table = ttk.Treeview(root, columns=columns, show="headings", height=12)
        self.table.heading("address", text="IP Address")
        self.table.heading("status", text="Status")
        self.table.heading("response", text="Response Time")
        self.table.column("address", width=150)
        self.table.column("status", width=80)
        self.table.column("response", width=420)
        self.table.pack(fill="both", expand=True, padx=8)

        self.summary_label = ttk.Label(root, text="", padding=8)
        self.summary_label.pack(fill="x")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose a text file of IPv4 addresses",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            texts = load_targets(path)
        except InputFileError as error:
            messagebox.showerror("Cannot load file", str(error))
            return
        self.texts = texts
        self.file_label.config(text=path)
        self.start_scan()

    def start_scan(self):
        if self.scanning or not self.texts:
            return
        self.scanning = True
        self.scan_button.state(["disabled"])
        self.table.delete(*self.table.get_children())
        for text in self.texts:
            self.table.insert("", "end", values=(text, "...", "Checking..."))
        self.summary_label.config(text=f"Scanning {len(self.texts)} entries...")

        thread = threading.Thread(target=self._scan_in_background, args=(list(self.texts),))
        thread.daemon = True
        thread.start()
        self.root.after(100, self._check_for_results)

    def _scan_in_background(self, texts):
        try:
            self.outcomes.put(scan(texts, self.timeout_ms, self.ping_func))
        except PingUnavailableError as error:
            self.outcomes.put(error)

    def _check_for_results(self):
        try:
            outcome = self.outcomes.get_nowait()
        except queue.Empty:
            self.root.after(100, self._check_for_results)
            return

        self.scanning = False
        self.scan_button.state(["!disabled"])
        if isinstance(outcome, Exception):
            self.summary_label.config(text="Scan failed.")
            messagebox.showerror("Cannot ping", str(outcome))
            return
        self.show_results(outcome)

    def show_results(self, results):
        self.table.delete(*self.table.get_children())
        for result in results:
            self.table.insert(
                "", "end", values=(result.address, result.status, describe_response(result))
            )

        counts = summarize(results)
        self.summary_label.config(
            text=(
                f"Input entries: {counts['input_entries']}    "
                f"Checked: {counts['checked']}    "
                f"UP: {counts['up']}    "
                f"DOWN: {counts['down']}    "
                f"Invalid: {counts['invalid']}"
            )
        )


def run_gui(path=None, timeout_ms=DEFAULT_TIMEOUT_MS):
    root = tk.Tk()
    window = CheckerWindow(root, timeout_ms=timeout_ms)
    if path:
        window.load_file(path)
    root.mainloop()
