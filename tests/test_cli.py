"""End-to-end tests of the command-line prototype (uses a fake ping)."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from network_health_checker.cli import main
from network_health_checker.pinger import PingUnavailableError

from .fakes import FakePing


def run_cli(*args, ping_func=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args), ping_func=ping_func or FakePing())
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_file(self, lines):
        path = Path(self.temp_dir.name) / "targets.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    def test_report_matches_spec_example(self):
        path = self.write_file(["192.168.1.1", "192.168.1.10", "192.168.1.20", "192.168.1.999"])
        fake = FakePing({"192.168.1.1": 2.4, "192.168.1.10": 5.8})
        code, out, _ = run_cli(path, ping_func=fake)

        self.assertEqual(code, 0)
        rows = [line.split(None, 2) for line in out.splitlines()[1:5]]
        self.assertEqual(rows[0], ["192.168.1.1", "UP", "2.4 ms"])
        self.assertEqual(rows[1], ["192.168.1.10", "UP", "5.8 ms"])
        self.assertEqual(rows[2], ["192.168.1.20", "DOWN", "No reply"])
        self.assertEqual(rows[3][:2], ["192.168.1.999", "INVALID"])
        self.assertTrue(rows[3][2].startswith("Not checked"))

        for line in [
            "Input entries: 4",
            "Valid addresses checked: 3",
            "UP: 2",
            "DOWN: 1",
            "Invalid: 1",
        ]:
            self.assertIn(line, out)
        self.assertIn("Scan time:", out)

    def test_too_many_entries_prints_error(self):
        path = self.write_file([f"10.0.0.{i}" for i in range(1, 22)])
        code, out, err = run_cli(path)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("maximum is 20", err)

    def test_missing_file_prints_error(self):
        code, _, err = run_cli("does_not_exist.txt")
        self.assertEqual(code, 1)
        self.assertIn("File not found", err)

    def test_missing_ping_command_prints_error(self):
        def no_ping(address, timeout_ms):
            raise PingUnavailableError("The 'ping' command was not found on this computer.")

        code, _, err = run_cli(self.write_file(["10.0.0.1"]), ping_func=no_ping)
        self.assertEqual(code, 1)
        self.assertIn("ping", err)

    def test_rejects_zero_timeout(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main([self.write_file(["10.0.0.1"]), "--timeout", "0"])


if __name__ == "__main__":
    unittest.main()
