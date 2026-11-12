# Testing — Network Health Checker (Milestone 3)

This file shows that the prototype does what SPEC.md promises. It has:

1. A test for every acceptance criterion (AC1–AC7) and its result
2. A validation of the app's output against a trusted tool, Windows' own `ping`
3. A log of the bugs found and fixed

## Test environment

| | |
|---|---|
| Computer | Windows laptop |
| Operating system | Windows 11 Home (10.0.26200) |
| Python | 3.14.5 |
| pytest | 9.2.0 |
| Network | Wi-Fi, laptop at `10.82.230.179` (not the home network) |
| Date | 12 November 2026 |

Run all tests from the repository folder:

```powershell
python -m pip install -r requirements.txt
python -m pytest -v
```

**Result:** `89 passed, 14 subtests passed in 9.85s`. The suite was run 5 more times after the fixes, and all 89 passed every time with no skips.

## 1. Acceptance criteria

All tests are in `tests/test_acceptance.py` and are named after their criterion. Tests marked *(real ping)* run the Windows `ping` command. They only ping `127.0.0.1` (this computer) and `192.0.2.x`, a range reserved for documentation (RFC 5737) that no real device uses. The other tests use a fake ping with fixed answers, so they give the same result on any network.

| Criterion | Test | Expected | Actual | Result |
|---|---|---|---|---|
| **AC1** Input file (R1) | `test_AC1_loads_and_scans_a_file_with_one_address` | 1 entry is loaded and scanned | 1 result | PASS |
| | `test_AC1_loads_and_scans_exactly_twenty_addresses` | 20 entries loaded; all 20 pinged | 20 results, 20 pinged | PASS |
| | `test_AC1_rejects_a_file_with_twenty_one_entries` | `InputFileError` mentioning "21 entries" | Raised | PASS |
| | `test_AC1_command_line_refuses_more_than_twenty_entries` | Exit code 1, nothing pinged, "maximum is 20" | Exit 1, 0 pings, message shown | PASS |
| **AC2** Invalid addresses (R2) | `test_AC2_marks_192_168_1_999_invalid_and_does_not_ping_it` | `192.168.1.999` INVALID and never pinged; the 3 valid ones pinged | INVALID; pinged only the 3 valid | PASS |
| | `test_AC2_other_invalid_formats_are_never_pinged` (7 cases: `10.0.0.256`, `192.168.1`, `1.2.3.4.5`, `hello`, `192.168.01.5`, `-1.2.3.4`, `::1`) | Each INVALID, 0 pings | All INVALID, 0 pings | PASS |
| **AC3** Reachability (R3) | `test_AC3_responding_address_is_up_and_silent_address_is_down` | UP, DOWN | UP, DOWN | PASS |
| | `test_AC3_real_ping_loopback_up_and_documentation_address_down` *(real ping)* | `127.0.0.1` UP, `192.0.2.1` DOWN | UP, DOWN | PASS |
| | `test_AC3_reply_slower_than_the_timeout_counts_as_down` | A 43 ms reply with a 10 ms timeout is DOWN; with 1000 ms it is UP | DOWN / UP | PASS (failed before the fix for Bug 2) |
| | `test_AC3_reply_exactly_at_the_timeout_still_counts_as_up` | A 1000 ms reply with a 1000 ms timeout is UP | UP | PASS |
| | `test_AC3_windows_destination_unreachable_is_down` | "Destination host unreachable" with exit code 0 is DOWN | DOWN | PASS |
| **AC4** Response time (R4) | `test_AC4_up_address_shows_a_number_in_milliseconds` | 2.4, shown as "2.4 ms" | "2.4 ms" | PASS |
| | `test_AC4_down_address_shows_response_time_unavailable` | No time; shown as "No reply" | "No reply" | PASS |
| | `test_AC4_real_ping_loopback_gives_a_numeric_time` *(real ping)* | A number between 0 and 1000 ms | 1.0 ms | PASS |
| **AC5** Performance (R5) | `test_AC5_three_scans_of_twenty_silent_addresses_each_within_five_seconds` | 3 runs of 20 addresses, each ≤ 5 s, where every fake ping waits the full 1 s timeout (the slowest case) | 3 runs of about 1.0 s each | PASS |
| | `test_AC5_real_ping_three_scans_of_twenty_addresses_within_five_seconds` *(real ping)* | 3 runs of `192.0.2.1`–`192.0.2.20`, each ≤ 5 s | 3 runs, each under 5 s | PASS |
| | Manual procedure on the home network (README.md, "Performance check") | 3 runs of `data/performance_targets.txt`, each ≤ 5 s | Linux: 1.01, 1.01, 1.00 s. Windows: 0.99, 0.80, 0.88 s | PASS |
| **AC6** CSV export (R6) | `test_AC6_export_has_required_columns_and_every_entry_with_its_status` | Columns `ip_address,status,response_time_ms`; 4 rows in order: UP 2.4, UP 5.8, DOWN (empty), INVALID (empty) | Same | PASS |
| | `test_AC6_command_line_csv_option_writes_the_same_rows` | `--csv` writes the same 5 lines | Same | PASS |
| **AC7** Summary counts (R7) | `test_AC7_counts_match_the_spec_example` | 4 entries, 3 checked, 2 UP, 1 DOWN, 1 INVALID | Same | PASS |
| | `test_AC7_displayed_counts_match_a_hand_count_of_the_sample_file` | `data/sample_targets.txt` counted by hand: 12 entries, 8 valid, 4 invalid; with 2 replies, 2 UP and 6 DOWN | Same | PASS |

The older tests in `tests/test_*.py` (63 tests from Milestone 2) still run and pass. They cover the same criteria in more detail, for example Linux and German Windows ping output, Notepad's UTF-8 BOM, and the GUI buttons.

## 2. Validation against a trusted tool

**Reference:** Windows' own `ping` command and Windows' IPv4 parser (`socket.inet_pton`). The script `tests/validate_against_windows_ping.py` runs all four checks. It was run on 12 November 2026 in the test environment above. It pings `127.0.0.1`, the public DNS servers `8.8.8.8` and `1.1.1.1`, and `192.0.2.1`–`.3`. It does not ping anyone's devices on the local network.

```powershell
python tests\validate_against_windows_ping.py
```

### 2.1 Response time read by the app vs. Windows' own figure (same ping)

Windows `ping` prints the time twice: on the reply line (`time=44ms`), which the app reads, and again in its statistics block (`Average = 44ms`). Comparing the two for the same ping checks that the app reads the right number.

| Address | Pings compared | Error (app − Windows) |
|---|---|---|
| `127.0.0.1` | 20 | +1 ms every time |
| `8.8.8.8` | 20 | 0 ms every time |
| `1.1.1.1` | 19 (1 ping got no reply) | 0 ms every time |

**Error: 0 ms for every reply of 1 ms or more.** The +1 ms on `127.0.0.1` is a deliberate choice: Windows prints replies faster than 1 ms as `time<1ms`, which the app records as 1 ms (see the docstring of `parse_ping_output`), while Windows' statistics round them down to 0 ms. So for very fast replies the app overstates the time by at most 1 ms.

### 2.2 Concurrent scan vs. a separate Windows ping

The app pings all addresses at the same time. To check that this does not distort the times, each of 20 rounds ran the app's scan of all three addresses together, then a separate Windows `ping` to each address straight afterwards.

| Address | Pairs | Median app | Median Windows | Median difference | Largest difference |
|---|---|---|---|---|---|
| `127.0.0.1` | 20 | 1 ms | 0 ms | +1 ms | 1 ms |
| `8.8.8.8` | 20 | 47 ms | 44 ms | 0 ms | 22 ms |
| `1.1.1.1` | 20 | 6 ms | 7 ms | −1 ms | 16 ms |

**Error: median difference within ±1 ms of Windows ping for all three addresses.** The largest single differences (16 ms and 22 ms) come from normal internet jitter between two separate pings, not from the app. The two pings in a pair are different packets sent a moment apart.

### 2.3 UP/DOWN vs. Windows ping

Over 5 rounds, the app's status for `127.0.0.1`, `8.8.8.8`, `1.1.1.1`, `192.0.2.1`, `192.0.2.2` and `192.0.2.3` was compared with Windows ping's own statistics (`Received = 1` with a `TTL=` reply line means UP).

**Result: 30 of 30 agree.**

### 2.4 IPv4 validation vs. Windows' own parser

The app's validator (Python's `ipaddress` module) was compared with `socket.inet_pton`, which calls Windows' own IPv4 parser. The comparison used 18 hand-picked cases (including `192.168.1.999`, `192.168.01.5`, `0x7f.0.0.1`, `1.2.3.4/24` and a full-width digit) and 20,000 random strings of digits and dots.

**Result: 0 disagreements in 20,018 strings.**

### 2.5 Timing of AC5 against a separate stopwatch

On the home network (10 November 2026), the app's printed scan time was compared with PowerShell's `Measure-Command`, which times the whole command including Python start-up. The difference is the start-up time, and the app's own number is always smaller, as expected.

| Run | App's scan time | Measure-Command (incl. start-up) | Difference |
|---|---|---|---|
| 1 | 0.99 s | 1.19 s | 0.20 s |
| 2 | 0.80 s | 0.98 s | 0.18 s |
| 3 | 0.88 s | 1.02 s | 0.14 s |

## 3. Bug log

| # | Bug | Cause | Fix | Introduced by AI? | Found by |
|---|---|---|---|---|---|
| 1 | Under pytest, one GUI test was **skipped at random** (2–3 runs out of 6) with "no display available", although the laptop has a display. A skipped test could hide a broken GUI. | pytest's default output capture (`--capture=fd`) makes Tkinter's start-up fail at random on Windows ("couldn't read file auto.tcl", "Can't find a usable tk.tcl"). It never happened with `unittest`, with `--capture=sys` or with `--capture=no`, and Tk started 60 times out of 60 outside pytest. The skip message guessed "no display" instead of showing the real cause. | Added `pytest.ini` with `addopts = --capture=sys`. Changed the skip message in `tests/test_gui.py` to "Tkinter could not start: ..." so the real error is shown. After the fix: 5 full runs, 0 skips. | **Partly.** The misleading skip message was in AI-written test code (Milestone 2). The start-up failure itself comes from how pytest and Tkinter interact on Windows. | The AI, when switching the tests to pytest; checked by running the suite repeatedly |
| 2 | **A reply that arrived after the timeout was counted as UP.** With `--timeout 10`, `8.8.8.8` showed `UP 43 ms`. That breaks R3 ("DOWN when no reply is received before the configured timeout"). With the default 1000 ms this could happen to slow Wi-Fi devices; the README records a 397 ms reply. | `pinger.py` trusted Windows `ping -w` to drop late replies, but Windows still prints them: `ping -n 1 -w 10 8.8.8.8` gave `time=43ms` in 15 out of 15 tries. | `parse_ping_output` now takes the timeout, and a reply slower than it counts as DOWN (`src/network_health_checker/pinger.py`). Regression tests: `test_AC3_reply_slower_than_the_timeout_counts_as_down` and `test_AC3_reply_exactly_at_the_timeout_still_counts_as_up`. After the fix, `--timeout 10` gives `8.8.8.8 DOWN` and `1.1.1.1 UP 7 ms`. | **Yes.** `pinger.py` was written by Claude Code in Milestone 2 (see AI_USE.md, 28 October 2026). | The AI, while testing edge cases of AC3 by hand |

**Known limitation, not a bug:** a reply faster than 1 ms on Windows (`time<1ms`) is recorded as 1 ms, so it can be up to 1 ms too high. This was a design choice, and the validation in 2.1 measures it.

## 4. How the tests themselves were checked

- **The regression test fails on the old code.** With the original `pinger.py` from commit `7b99efe`, `test_AC3_reply_slower_than_the_timeout_counts_as_down` failed. With the fix, it passes. So the test really catches Bug 2. Two other AC3 tests also failed on the old code, but only because the old function had no `timeout_ms` parameter.
- **Expected values come from outside the code.** They come from SPEC.md (the 2 UP, 1 DOWN, 1 INVALID example and the CSV columns), from a hand count of `data/sample_targets.txt`, and from real Windows `ping` output copied into the tests. They were not copied from what the code printed.
- **Real-ping tests only use addresses with a known answer:** `127.0.0.1` always replies, and `192.0.2.x` is reserved for documentation, so it never does.
- **The suite was run repeatedly** (6 full runs) to make sure no test passes or skips by chance.
