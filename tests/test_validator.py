"""Tests for R2 / AC2: identifying invalid IPv4 addresses."""

import unittest

from network_health_checker.validator import (
    INVALID,
    VALID,
    count_summary,
    validate_entries,
    validate_entry,
)


class ValidateEntryTests(unittest.TestCase):
    def test_valid_addresses(self):
        for text in ["192.168.1.1", "10.0.0.1", "8.8.8.8", "0.0.0.0", "255.255.255.255"]:
            with self.subTest(text=text):
                self.assertEqual(validate_entry(text).status, VALID)

    def test_invalid_addresses(self):
        cases = [
            "192.168.1.999",  # the example from AC2
            "10.0.0.256",  # octet above 255
            "192.168.1",  # too few octets
            "1.2.3.4.5",  # too many octets
            "hello",  # not a number
            "192.168.01.5",  # leading zero is ambiguous
            "192.168.1.-1",  # negative octet
            "::1",  # IPv6 is out of scope
            "",
        ]
        for text in cases:
            with self.subTest(text=text):
                entry = validate_entry(text)
                self.assertEqual(entry.status, INVALID)
                self.assertTrue(entry.reason, "an invalid entry should explain why")

    def test_valid_entry_has_no_reason(self):
        self.assertEqual(validate_entry("192.168.1.1").reason, "")


class ValidateEntriesTests(unittest.TestCase):
    def test_keeps_input_order_and_marks_each_entry(self):
        entries = validate_entries(["192.168.1.1", "192.168.1.999", "10.0.0.1"])
        self.assertEqual([e.text for e in entries], ["192.168.1.1", "192.168.1.999", "10.0.0.1"])
        self.assertEqual([e.status for e in entries], [VALID, INVALID, VALID])

    def test_count_summary(self):
        entries = validate_entries(["192.168.1.1", "192.168.1.10", "192.168.1.999"])
        self.assertEqual(count_summary(entries), {"input_entries": 3, "valid": 2, "invalid": 1})


if __name__ == "__main__":
    unittest.main()
