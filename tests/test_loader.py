"""Tests for R1 / AC1: loading a text file of 1-20 candidate addresses."""

import tempfile
import unittest
from pathlib import Path

from network_health_checker.loader import MAX_ENTRIES, InputFileError, load_targets

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_targets.txt"


class LoadTargetsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_file(self, content, encoding="utf-8"):
        path = Path(self.temp_dir.name) / "targets.txt"
        path.write_text(content, encoding=encoding)
        return path

    def test_loads_one_address_per_line(self):
        path = self.write_file("192.168.1.1\n192.168.1.10\n192.168.1.999\n")
        self.assertEqual(load_targets(path), ["192.168.1.1", "192.168.1.10", "192.168.1.999"])

    def test_accepts_a_single_address(self):
        path = self.write_file("10.0.0.1")
        self.assertEqual(load_targets(path), ["10.0.0.1"])

    def test_accepts_exactly_twenty_entries(self):
        lines = [f"10.0.0.{i}" for i in range(1, MAX_ENTRIES + 1)]
        path = self.write_file("\n".join(lines))
        self.assertEqual(len(load_targets(path)), 20)

    def test_rejects_more_than_twenty_entries(self):
        lines = [f"10.0.0.{i}" for i in range(1, MAX_ENTRIES + 2)]
        path = self.write_file("\n".join(lines))
        with self.assertRaisesRegex(InputFileError, "21 entries"):
            load_targets(path)

    def test_invalid_entries_count_toward_the_limit(self):
        lines = ["not-an-ip"] * (MAX_ENTRIES + 1)
        path = self.write_file("\n".join(lines))
        with self.assertRaises(InputFileError):
            load_targets(path)

    def test_skips_blank_lines_and_trims_spaces(self):
        path = self.write_file("\n  192.168.1.1  \n\n\t10.0.0.1\n   \n")
        self.assertEqual(load_targets(path), ["192.168.1.1", "10.0.0.1"])

    def test_handles_windows_line_endings_and_notepad_bom(self):
        path = Path(self.temp_dir.name) / "windows.txt"
        path.write_bytes("192.168.1.1\r\n10.0.0.1\r\n".encode("utf-8-sig"))
        self.assertEqual(load_targets(path), ["192.168.1.1", "10.0.0.1"])

    def test_rejects_empty_file(self):
        path = self.write_file("\n   \n")
        with self.assertRaisesRegex(InputFileError, "no addresses"):
            load_targets(path)

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(InputFileError, "not found"):
            load_targets(Path(self.temp_dir.name) / "missing.txt")

    def test_rejects_non_text_file(self):
        path = Path(self.temp_dir.name) / "binary.txt"
        path.write_bytes(b"\xff\xfe\x00\x81")
        with self.assertRaisesRegex(InputFileError, "UTF-8"):
            load_targets(path)

    def test_sample_data_file_loads(self):
        entries = load_targets(SAMPLE_FILE)
        self.assertGreaterEqual(len(entries), 1)
        self.assertLessEqual(len(entries), MAX_ENTRIES)


if __name__ == "__main__":
    unittest.main()
