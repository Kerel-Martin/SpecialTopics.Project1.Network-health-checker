"""Tests for R6 / AC6: exporting scan results to CSV."""

import csv
import tempfile
import unittest
from pathlib import Path

from network_health_checker.exporter import CSV_COLUMNS, ExportError, export_csv
from network_health_checker.scanner import scan

from .fakes import FakePing


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.reader(file))


class ExportCsvTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.folder = Path(temp_dir.name)
        # The SPEC.md example: two UP, one DOWN, one INVALID.
        fake = FakePing({"192.168.1.1": 2.4, "192.168.1.10": 5.8})
        self.results = scan(
            ["192.168.1.1", "192.168.1.10", "192.168.1.20", "192.168.1.999"], ping_func=fake
        )

    def test_matches_spec_example(self):
        path = self.folder / "results.csv"
        export_csv(self.results, path)
        self.assertEqual(
            read_rows(path),
            [
                ["ip_address", "status", "response_time_ms"],
                ["192.168.1.1", "UP", "2.4"],
                ["192.168.1.10", "UP", "5.8"],
                ["192.168.1.20", "DOWN", ""],
                ["192.168.1.999", "INVALID", ""],
            ],
        )

    def test_header_has_required_columns(self):
        path = self.folder / "results.csv"
        export_csv(self.results, path)
        self.assertEqual(read_rows(path)[0], CSV_COLUMNS)

    def test_every_entry_is_exported_once(self):
        path = self.folder / "results.csv"
        export_csv(self.results, path)
        self.assertEqual(len(read_rows(path)) - 1, len(self.results))

    def test_no_blank_lines_between_rows(self):
        # Opening a CSV file without newline="" gives "\r\r\n" on Windows,
        # which shows up as blank rows in Excel.
        path = self.folder / "results.csv"
        export_csv(self.results, path)
        self.assertNotIn(b"\r\r\n", path.read_bytes())

    def test_text_with_comma_is_quoted_safely(self):
        results = scan(["10.0.0.1,10.0.0.2"], ping_func=FakePing())
        path = self.folder / "results.csv"
        export_csv(results, path)
        self.assertEqual(read_rows(path)[1], ["10.0.0.1,10.0.0.2", "INVALID", ""])

    def test_missing_folder_raises_export_error(self):
        with self.assertRaisesRegex(ExportError, "Could not write"):
            export_csv(self.results, self.folder / "no_such_folder" / "results.csv")


if __name__ == "__main__":
    unittest.main()
