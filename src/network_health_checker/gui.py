"""Optional Tkinter window for the prototype.

SPEC.md treats the GUI as an optional enhancement; the command-line
interface in cli.py remains the required interface.
"""

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .loader import MAX_ENTRIES, InputFileError, load_targets
from .performance import REQUIRED_RUNS, describe_report, run_performance_test
from .pinger import DEFAULT_TIMEOUT_MS, PingUnavailableError, ping
from .scanner import describe_response, scan, summarize


class CheckerWindow:
    def __init__(self, root, timeout_ms=DEFAULT_TIMEOUT_MS, ping_func=ping):
        self.root = root
        self.timeout_ms = timeout_ms
        self.ping_func = ping_func
        self.texts = []
        self.busy = False
        # Scans run in a background thread so the window does not freeze.
        # The thread sends (kind, value) messages back through this queue.
        self.messages = queue.Queue()

        root.title("Network Health Checker - Prototype")
        root.geometry("720x500")

        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        ttk.Button(top, text="Open address file...", command=self.choose_file).pack(side="left")
        self.scan_button = ttk.Button(top, text="Scan again", command=self.start_scan)
        self.scan_button.pack(side="left", padx=(8, 0))
        self.performance_button = ttk.Button(
            top, text="Performance test (R5)", command=self.start_performance_test
        )
        self.performance_button.pack(side="left", padx=(8, 0))
        self.file_label = ttk.Label(top, text=f"No file loaded (max {MAX_ENTRIES} addresses)")
        self.file_label.pack(side="left", padx=8)
        self._set_buttons_enabled(False)

        columns = ("address", "status", "response")
        self.table = ttk.Treeview(root, columns=columns, show="headings", height=12)
        self.table.heading("address", text="IP Address")
        self.table.heading("status", text="Status")
        self.table.heading("response", text="Response Time")
        self.table.column("address", width=150)
        self.table.column("status", width=80)
        self.table.column("response", width=460)
        self.table.pack(fill="both", expand=True, padx=8)

        self.summary_label = ttk.Label(root, text="", padding=(8, 8, 8, 0))
        self.summary_label.pack(fill="x")
        self.performance_label = ttk.Label(root, text="", padding=8, justify="left")
        self.performance_label.pack(fill="x")

    def _set_buttons_enabled(self, enabled):
        state = ["!disabled"] if enabled else ["disabled"]
        self.scan_button.state(state)
        self.performance_button.state(state)

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
        self.performance_label.config(text="")
        self.start_scan()

    def _start_background(self, work, status_text):
        if self.busy or not self.texts:
            return
        self.busy = True
        self._set_buttons_enabled(False)
        self.table.delete(*self.table.get_children())
        for text in self.texts:
            self.table.insert("", "end", values=(text, "...", "Checking..."))
        self.summary_label.config(text=status_text)

        thread = threading.Thread(target=work, args=(list(self.texts),))
        thread.daemon = True
        thread.start()
        self.root.after(100, self._check_messages)

    def start_scan(self):
        self.performance_label.config(text="")
        self._start_background(
            self._scan_in_background, f"Scanning {len(self.texts)} entries..."
        )

    def start_performance_test(self):
        self.performance_label.config(text="")
        self._start_background(
            self._performance_in_background,
            f"Performance test: run 1 of {REQUIRED_RUNS}...",
        )

    def _scan_in_background(self, texts):
        try:
            self.messages.put(("scan", scan(texts, self.timeout_ms, self.ping_func)))
        except PingUnavailableError as error:
            self.messages.put(("error", error))

    def _performance_in_background(self, texts):
        def report_progress(run_number, seconds):
            self.messages.put(("progress", (run_number, seconds)))

        try:
            report = run_performance_test(
                texts,
                timeout_ms=self.timeout_ms,
                ping_func=self.ping_func,
                on_run=report_progress,
            )
            self.messages.put(("performance", report))
        except PingUnavailableError as error:
            self.messages.put(("error", error))

    def _check_messages(self):
        while True:
            try:
                kind, value = self.messages.get_nowait()
            except queue.Empty:
                self.root.after(100, self._check_messages)
                return

            if kind == "progress":
                run_number, seconds = value
                done = f"Run {run_number} of {REQUIRED_RUNS} took {seconds:.2f} s."
                if run_number < REQUIRED_RUNS:
                    done += f" Starting run {run_number + 1}..."
                self.summary_label.config(text=f"Performance test: {done}")
                continue

            self.busy = False
            self._set_buttons_enabled(True)
            if kind == "error":
                self.summary_label.config(text="Scan failed.")
                messagebox.showerror("Cannot ping", str(value))
            elif kind == "scan":
                self.show_results(value)
            elif kind == "performance":
                self.show_results(value.last_results)
                self.performance_label.config(text=describe_report(value))
            return

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
