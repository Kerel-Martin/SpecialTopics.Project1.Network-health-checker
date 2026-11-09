"""Smoke tests for the optional Tkinter window (uses a fake ping).

Skipped when Tkinter is not installed or no display is available.
"""

import tempfile
import time
import unittest
from pathlib import Path

from .fakes import FakePing

try:
    import tkinter as tk
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "Tkinter is not installed")
class GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"no display available: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.temp_path = Path(temp_dir.name)
        self.path = self.temp_path / "targets.txt"
        self.path.write_text("192.168.1.1\n192.168.1.20\n192.168.1.999\n", encoding="utf-8")

    def wait_until_idle(self, window):
        deadline = time.monotonic() + 5
        while window.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.02)
        self.assertFalse(window.busy, "background work did not finish")

    def test_loading_a_file_scans_and_fills_the_table(self):
        from network_health_checker.gui import CheckerWindow

        fake = FakePing({"192.168.1.1": 2.4})
        window = CheckerWindow(self.root, ping_func=fake)
        window.load_file(str(self.path))
        self.wait_until_idle(window)

        rows = [window.table.item(item, "values") for item in window.table.get_children()]
        self.assertEqual(rows[0], ("192.168.1.1", "UP", "2.4 ms"))
        self.assertEqual(rows[1], ("192.168.1.20", "DOWN", "No reply"))
        self.assertEqual(rows[2][:2], ("192.168.1.999", "INVALID"))
        summary = window.summary_label.cget("text")
        self.assertIn("UP: 1", summary)
        self.assertIn("DOWN: 1", summary)
        self.assertIn("Invalid: 1", summary)
        self.assertCountEqual(fake.pinged, ["192.168.1.1", "192.168.1.20"])

    def test_performance_button_runs_three_scans_and_shows_feedback(self):
        from network_health_checker.gui import CheckerWindow

        path = self.temp_path / "twenty.txt"
        path.write_text("\n".join(f"10.0.0.{i}" for i in range(1, 21)), encoding="utf-8")
        fake = FakePing({"10.0.0.1": 1.5})
        window = CheckerWindow(self.root, ping_func=fake)
        window.load_file(str(path))
        self.wait_until_idle(window)
        fake.pinged.clear()

        window.start_performance_test()
        self.wait_until_idle(window)

        self.assertEqual(len(fake.pinged), 60)
        feedback = window.performance_label.cget("text")
        for number in (1, 2, 3):
            self.assertIn(f"Run {number}:", feedback)
        self.assertIn("AC5 PASSED", feedback)
        self.assertIn("UP: 1", window.summary_label.cget("text"))

    def test_buttons_are_disabled_until_a_file_is_loaded(self):
        from network_health_checker.gui import CheckerWindow

        window = CheckerWindow(self.root, ping_func=FakePing())
        self.assertTrue(window.performance_button.instate(["disabled"]))
        window.start_performance_test()
        self.assertFalse(window.busy)


if __name__ == "__main__":
    unittest.main()
