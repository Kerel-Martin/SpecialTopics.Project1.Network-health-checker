"""Tests for scanning a list: AC2 (no ping for INVALID), AC3, AC4 and AC7."""

import time
import unittest

from network_health_checker.pinger import PingResult
from network_health_checker.scanner import (
    DOWN,
    UP,
    ScanResult,
    describe_response,
    scan,
    summarize,
)
from network_health_checker.validator import INVALID

from .fakes import FakePing


class ScanTests(unittest.TestCase):
    def test_statuses_and_order(self):
        fake = FakePing({"192.168.1.1": 2.4})
        results = scan(["192.168.1.1", "192.168.1.999", "192.168.1.20"], ping_func=fake)

        self.assertEqual([r.address for r in results], ["192.168.1.1", "192.168.1.999", "192.168.1.20"])
        self.assertEqual([r.status for r in results], [UP, INVALID, DOWN])
        self.assertEqual(results[0].response_time_ms, 2.4)
        self.assertIsNone(results[2].response_time_ms)

    def test_invalid_entries_are_never_pinged(self):
        fake = FakePing()
        scan(["192.168.1.1", "192.168.1.999", "hello", "10.0.0.256", "10.0.0.1"], ping_func=fake)
        self.assertCountEqual(fake.pinged, ["192.168.1.1", "10.0.0.1"])

    def test_file_with_only_invalid_entries_sends_no_ping(self):
        fake = FakePing()
        results = scan(["hello", "1.2.3"], ping_func=fake)
        self.assertEqual(fake.pinged, [])
        self.assertEqual([r.status for r in results], [INVALID, INVALID])

    def test_addresses_are_pinged_at_the_same_time(self):
        # 20 pings that each take 0.3 s would take 6 s one after another.
        def slow_ping(address, timeout_ms):
            time.sleep(0.3)
            return PingResult(False)

        addresses = [f"10.0.0.{i}" for i in range(1, 21)]
        start = time.perf_counter()
        scan(addresses, ping_func=slow_ping)
        self.assertLess(time.perf_counter() - start, 2.0)

    def test_timeout_is_passed_to_ping(self):
        seen = []

        def recording_ping(address, timeout_ms):
            seen.append(timeout_ms)
            return PingResult(False)

        scan(["10.0.0.1"], timeout_ms=500, ping_func=recording_ping)
        self.assertEqual(seen, [500])


class SummaryTests(unittest.TestCase):
    def test_counts_match_the_input(self):
        fake = FakePing({"192.168.1.1": 2.4, "192.168.1.10": 5.8})
        results = scan(
            ["192.168.1.1", "192.168.1.10", "192.168.1.20", "192.168.1.999"], ping_func=fake
        )
        self.assertEqual(
            summarize(results),
            {"input_entries": 4, "checked": 3, "up": 2, "down": 1, "invalid": 1},
        )


class DescribeResponseTests(unittest.TestCase):
    def test_up_shows_milliseconds(self):
        self.assertEqual(describe_response(ScanResult("10.0.0.1", UP, 2.4)), "2.4 ms")
        self.assertEqual(describe_response(ScanResult("10.0.0.1", UP, 2.0)), "2 ms")

    def test_down_shows_no_reply(self):
        self.assertEqual(describe_response(ScanResult("10.0.0.1", DOWN)), "No reply")

    def test_invalid_shows_not_checked_and_reason(self):
        text = describe_response(ScanResult("1.2.3", INVALID, details="Expected 4 octets"))
        self.assertEqual(text, "Not checked: Expected 4 octets")


if __name__ == "__main__":
    unittest.main()
