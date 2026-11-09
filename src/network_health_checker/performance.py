"""Repeat a scan and time each run (requirement R5 / AC5)."""

import time
from dataclasses import dataclass
from typing import List

from .pinger import DEFAULT_TIMEOUT_MS, ping
from .scanner import ScanResult, scan, summarize

# SPEC.md, AC5: 20 valid addresses, scanned 3 times, each within 5 seconds.
REQUIRED_VALID = 20
REQUIRED_RUNS = 3
TIME_LIMIT_S = 5.0


@dataclass(frozen=True)
class PerformanceReport:
    durations: List[float]  # seconds, one per run
    valid_addresses: int
    last_results: List[ScanResult]

    @property
    def all_within_limit(self):
        return all(seconds <= TIME_LIMIT_S for seconds in self.durations)

    @property
    def meets_ac5(self):
        """True only when the AC5 conditions were met and every run passed."""
        return (
            self.valid_addresses == REQUIRED_VALID
            and len(self.durations) == REQUIRED_RUNS
            and self.all_within_limit
        )


def run_performance_test(
    texts,
    runs=REQUIRED_RUNS,
    timeout_ms=DEFAULT_TIMEOUT_MS,
    ping_func=ping,
    clock=time.perf_counter,
    on_run=None,
):
    """Scan ``texts`` ``runs`` times and return a PerformanceReport.

    ``on_run(run_number, seconds)`` is called after each run, so a caller can
    show progress.
    """
    durations = []
    results = []
    for run_number in range(1, runs + 1):
        start = clock()
        results = scan(texts, timeout_ms=timeout_ms, ping_func=ping_func)
        seconds = clock() - start
        durations.append(seconds)
        if on_run is not None:
            on_run(run_number, seconds)

    return PerformanceReport(durations, summarize(results)["checked"], results)


def describe_report(report):
    """Return the feedback text shown after a performance test."""
    lines = []
    for number, seconds in enumerate(report.durations, start=1):
        verdict = "within" if seconds <= TIME_LIMIT_S else "OVER"
        lines.append(f"Run {number}: {seconds:.2f} s ({verdict} {TIME_LIMIT_S:g} s)")

    if report.meets_ac5:
        lines.append(
            f"AC5 PASSED: all {REQUIRED_RUNS} scans of {REQUIRED_VALID} valid "
            f"addresses finished within {TIME_LIMIT_S:g} s."
        )
    elif not report.all_within_limit:
        lines.append(f"AC5 FAILED: at least one scan took longer than {TIME_LIMIT_S:g} s.")
    else:
        lines.append(
            f"All runs finished within {TIME_LIMIT_S:g} s, but this is not a full AC5 "
            f"test: AC5 needs {REQUIRED_VALID} valid addresses scanned {REQUIRED_RUNS} "
            f"times (this file has {report.valid_addresses} valid)."
        )
    return "\n".join(lines)
