"""Tests for the R5 / AC5 performance test (uses a fake ping and a fake clock)."""

import unittest

from network_health_checker.performance import (
    REQUIRED_RUNS,
    describe_report,
    run_performance_test,
)

from .fakes import FakePing

TWENTY = [f"10.0.0.{i}" for i in range(1, 21)]


def fake_clock(*times):
    """Return a clock that gives these times, one per call."""
    values = iter(times)
    return lambda: next(values)


class RunPerformanceTestTests(unittest.TestCase):
    def test_runs_three_scans_and_records_each_duration(self):
        fake = FakePing({"10.0.0.1": 2.0})
        clock = fake_clock(0.0, 1.0, 10.0, 11.5, 20.0, 21.25)
        report = run_performance_test(TWENTY, ping_func=fake, clock=clock)

        self.assertEqual(report.durations, [1.0, 1.5, 1.25])
        self.assertEqual(len(fake.pinged), 20 * REQUIRED_RUNS)
        self.assertEqual(report.valid_addresses, 20)
        self.assertEqual(report.last_results[0].status, "UP")

    def test_reports_progress_after_each_run(self):
        progress = []
        clock = fake_clock(0, 1, 2, 3, 4, 5)
        run_performance_test(
            TWENTY,
            ping_func=FakePing(),
            clock=clock,
            on_run=lambda number, seconds: progress.append((number, seconds)),
        )
        self.assertEqual(progress, [(1, 1), (2, 1), (3, 1)])

    def test_invalid_entries_do_not_count_as_valid(self):
        texts = TWENTY[:19] + ["192.168.1.999"]
        report = run_performance_test(texts, ping_func=FakePing(), clock=fake_clock(*range(6)))
        self.assertEqual(report.valid_addresses, 19)


class VerdictTests(unittest.TestCase):
    def report(self, texts, durations):
        times = []
        for seconds in durations:
            times += [0.0, seconds]
        return run_performance_test(
            texts, runs=len(durations), ping_func=FakePing(), clock=fake_clock(*times)
        )

    def test_pass_when_twenty_valid_and_all_runs_within_five_seconds(self):
        report = self.report(TWENTY, [1.0, 1.1, 5.0])
        self.assertTrue(report.meets_ac5)
        text = describe_report(report)
        self.assertIn("Run 3: 5.00 s (within 5 s)", text)
        self.assertIn("AC5 PASSED", text)

    def test_fail_when_one_run_is_too_slow(self):
        report = self.report(TWENTY, [1.0, 5.2, 1.0])
        self.assertFalse(report.meets_ac5)
        text = describe_report(report)
        self.assertIn("Run 2: 5.20 s (OVER 5 s)", text)
        self.assertIn("AC5 FAILED", text)

    def test_fast_but_fewer_than_twenty_valid_is_not_a_full_ac5_test(self):
        report = self.report(TWENTY[:6], [1.0, 1.0, 1.0])
        self.assertFalse(report.meets_ac5)
        text = describe_report(report)
        self.assertIn("not a full AC5 test", text)
        self.assertIn("this file has 6 valid", text)
        self.assertNotIn("PASSED", text)

    def test_fewer_than_three_runs_is_not_a_full_ac5_test(self):
        report = self.report(TWENTY, [1.0, 1.0])
        self.assertFalse(report.meets_ac5)


if __name__ == "__main__":
    unittest.main()
