"""Acceptance tests: one or more pytest tests per criterion in SPEC.md Section 6.

Each test is named after its criterion (test_AC1_..., test_AC2_..., and so on)
so TESTING.md can point to it. Most tests use a fake ping with fixed answers.
The tests marked "real ping" run the operating system's ping command against
127.0.0.1 (this computer) and 192.0.2.x, a range reserved for documentation
(RFC 5737) that no real device uses, so they never ping anyone else's device.

Run with:  python -m pytest -v
"""

import csv
import time

import pytest

from network_health_checker.cli import format_report, main
from network_health_checker.exporter import CSV_COLUMNS, export_csv
from network_health_checker.loader import MAX_ENTRIES, InputFileError, load_targets
from network_health_checker.performance import (
    REQUIRED_RUNS,
    TIME_LIMIT_S,
    run_performance_test,
)
from network_health_checker.pinger import PingResult, parse_ping_output, ping
from network_health_checker.scanner import DOWN, UP, describe_response, scan, summarize
from network_health_checker.validator import INVALID

from .fakes import FakePing

# The example from SPEC.md Section 5: 2 UP, 1 DOWN, 1 INVALID.
SPEC_EXAMPLE = ["192.168.1.1", "192.168.1.10", "192.168.1.20", "192.168.1.999"]
SPEC_REPLIES = {"192.168.1.1": 2.4, "192.168.1.10": 5.8}

# 20 addresses from the documentation range: valid, and never answered.
DOCUMENTATION_ADDRESSES = [f"192.0.2.{n}" for n in range(1, 21)]


def write_targets(tmp_path, lines):
    path = tmp_path / "targets.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --- AC1: input file (R1) -------------------------------------------------


def test_AC1_loads_and_scans_a_file_with_one_address(tmp_path):
    texts = load_targets(write_targets(tmp_path, ["192.168.1.1"]))
    results = scan(texts, ping_func=FakePing())
    assert [r.address for r in results] == ["192.168.1.1"]


def test_AC1_loads_and_scans_exactly_twenty_addresses(tmp_path):
    lines = [f"10.0.0.{n}" for n in range(1, MAX_ENTRIES + 1)]
    fake = FakePing()
    results = scan(load_targets(write_targets(tmp_path, lines)), ping_func=fake)
    assert len(results) == 20
    assert sorted(fake.pinged) == sorted(lines)


def test_AC1_rejects_a_file_with_twenty_one_entries(tmp_path):
    lines = [f"10.0.0.{n}" for n in range(1, MAX_ENTRIES + 2)]
    with pytest.raises(InputFileError, match="21 entries"):
        load_targets(write_targets(tmp_path, lines))


def test_AC1_command_line_refuses_more_than_twenty_entries(tmp_path, capsys):
    lines = [f"10.0.0.{n}" for n in range(1, MAX_ENTRIES + 2)]
    fake = FakePing()
    exit_code = main([str(write_targets(tmp_path, lines))], ping_func=fake)
    assert exit_code == 1
    assert fake.pinged == []  # nothing was scanned
    assert "maximum is 20" in capsys.readouterr().err


# --- AC2: invalid addresses (R2) ------------------------------------------


def test_AC2_marks_192_168_1_999_invalid_and_does_not_ping_it(tmp_path):
    texts = load_targets(write_targets(tmp_path, SPEC_EXAMPLE))
    fake = FakePing(SPEC_REPLIES)
    results = scan(texts, ping_func=fake)

    by_address = {r.address: r for r in results}
    assert by_address["192.168.1.999"].status == INVALID
    assert "192.168.1.999" not in fake.pinged
    assert sorted(fake.pinged) == sorted(SPEC_EXAMPLE[:3])


@pytest.mark.parametrize(
    "text",
    ["10.0.0.256", "192.168.1", "1.2.3.4.5", "hello", "192.168.01.5", "-1.2.3.4", "::1"],
)
def test_AC2_other_invalid_formats_are_never_pinged(text):
    fake = FakePing()
    results = scan([text], ping_func=fake)
    assert results[0].status == INVALID
    assert fake.pinged == []


# --- AC3: reachability status (R3) ----------------------------------------


def test_AC3_responding_address_is_up_and_silent_address_is_down():
    fake = FakePing({"192.168.1.1": 2.4})
    results = scan(["192.168.1.1", "192.168.1.20"], ping_func=fake)
    assert [r.status for r in results] == [UP, DOWN]


def test_AC3_real_ping_loopback_up_and_documentation_address_down():
    # real ping: 127.0.0.1 always answers; 192.0.2.1 never does.
    results = scan(["127.0.0.1", "192.0.2.1"], timeout_ms=1000)
    assert [r.status for r in results] == [UP, DOWN]


def test_AC3_reply_slower_than_the_timeout_counts_as_down():
    # Bug 2 in TESTING.md: Windows ping prints this reply even with -w 10.
    output = "Reply from 8.8.8.8: bytes=32 time=43ms TTL=110\n"
    assert parse_ping_output(0, output, timeout_ms=10) == PingResult(False)
    assert parse_ping_output(0, output, timeout_ms=1000) == PingResult(True, 43.0)


def test_AC3_reply_exactly_at_the_timeout_still_counts_as_up():
    output = "Reply from 8.8.8.8: bytes=32 time=1000ms TTL=110\n"
    assert parse_ping_output(0, output, timeout_ms=1000) == PingResult(True, 1000.0)


def test_AC3_windows_destination_unreachable_is_down():
    # Windows exits with 0 here although the target itself did not answer.
    output = "Reply from 192.168.1.10: Destination host unreachable.\n"
    assert parse_ping_output(0, output, timeout_ms=1000) == PingResult(False)


# --- AC4: response time (R4) ----------------------------------------------


def test_AC4_up_address_shows_a_number_in_milliseconds():
    results = scan(["192.168.1.1"], ping_func=FakePing({"192.168.1.1": 2.4}))
    assert results[0].response_time_ms == 2.4
    assert describe_response(results[0]) == "2.4 ms"


def test_AC4_down_address_shows_response_time_unavailable():
    results = scan(["192.168.1.20"], ping_func=FakePing())
    assert results[0].response_time_ms is None
    assert describe_response(results[0]) == "No reply"


def test_AC4_real_ping_loopback_gives_a_numeric_time():
    # real ping
    result = ping("127.0.0.1", timeout_ms=1000)
    assert result.reachable
    assert isinstance(result.response_time_ms, float)
    assert 0 <= result.response_time_ms <= 1000


# --- AC5: performance (R5) ------------------------------------------------


class SlowestCasePing(FakePing):
    """Never answers, and waits the whole timeout first: the slowest case."""

    def __call__(self, address, timeout_ms):
        super().__call__(address, timeout_ms)
        time.sleep(timeout_ms / 1000)
        return PingResult(False)


def test_AC5_three_scans_of_twenty_silent_addresses_each_within_five_seconds():
    report = run_performance_test(
        DOCUMENTATION_ADDRESSES, timeout_ms=1000, ping_func=SlowestCasePing()
    )
    assert len(report.durations) == REQUIRED_RUNS
    assert all(seconds <= TIME_LIMIT_S for seconds in report.durations), report.durations
    assert report.meets_ac5


def test_AC5_real_ping_three_scans_of_twenty_addresses_within_five_seconds():
    # real ping, 20 documentation addresses that never answer
    report = run_performance_test(DOCUMENTATION_ADDRESSES, timeout_ms=1000)
    assert report.valid_addresses == 20
    assert len(report.durations) == REQUIRED_RUNS
    assert all(seconds <= TIME_LIMIT_S for seconds in report.durations), report.durations
    assert report.meets_ac5


# --- AC6: CSV export (R6) -------------------------------------------------


def test_AC6_export_has_required_columns_and_every_entry_with_its_status(tmp_path):
    results = scan(SPEC_EXAMPLE, ping_func=FakePing(SPEC_REPLIES))
    path = tmp_path / "results.csv"
    export_csv(results, path)

    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == CSV_COLUMNS
        rows = list(reader)

    assert rows == [
        {"ip_address": "192.168.1.1", "status": "UP", "response_time_ms": "2.4"},
        {"ip_address": "192.168.1.10", "status": "UP", "response_time_ms": "5.8"},
        {"ip_address": "192.168.1.20", "status": "DOWN", "response_time_ms": ""},
        {"ip_address": "192.168.1.999", "status": "INVALID", "response_time_ms": ""},
    ]


def test_AC6_command_line_csv_option_writes_the_same_rows(tmp_path):
    csv_path = tmp_path / "out.csv"
    exit_code = main(
        [str(write_targets(tmp_path, SPEC_EXAMPLE)), "--csv", str(csv_path)],
        ping_func=FakePing(SPEC_REPLIES),
    )
    assert exit_code == 0
    lines = csv_path.read_text(encoding="utf-8-sig").splitlines()
    assert lines == [
        "ip_address,status,response_time_ms",
        "192.168.1.1,UP,2.4",
        "192.168.1.10,UP,5.8",
        "192.168.1.20,DOWN,",
        "192.168.1.999,INVALID,",
    ]


# --- AC7: summary counts (R7) ---------------------------------------------


def test_AC7_counts_match_the_spec_example():
    results = scan(SPEC_EXAMPLE, ping_func=FakePing(SPEC_REPLIES))
    assert summarize(results) == {
        "input_entries": 4,
        "checked": 3,
        "up": 2,
        "down": 1,
        "invalid": 1,
    }


def test_AC7_displayed_counts_match_a_hand_count_of_the_sample_file():
    # data/sample_targets.txt counted by hand: 12 lines, 4 malformed
    # (192.168.1.999, 10.0.0.256, hello, 192.168.01.5), so 8 valid.
    # With this fake ping 2 of the 8 valid answer, so 2 UP and 6 DOWN.
    from pathlib import Path

    sample = Path(__file__).resolve().parent.parent / "data" / "sample_targets.txt"
    results = scan(load_targets(sample), ping_func=FakePing({"8.8.8.8": 40.0, "192.168.18.132": 1.0}))
    report = format_report(results)
    assert "Input entries: 12" in report
    assert "Valid addresses checked: 8" in report
    assert "UP: 2" in report
    assert "DOWN: 6" in report
    assert "Invalid: 4" in report
