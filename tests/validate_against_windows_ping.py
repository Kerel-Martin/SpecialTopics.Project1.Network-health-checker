"""Validate the app against a trusted tool: Windows' own ping command (and inet_pton).

Not a pytest test (the file name does not start with "test_"), because the
results depend on the network. Run it on Windows from the repository folder:

    python tests/validate_against_windows_ping.py

It prints three checks, which are recorded in TESTING.md:

1. Response time read by the app vs. the "Average = Xms" that Windows ping
   prints in its statistics block for the same ping (same output, different
   line, so this checks the app's parsing against Windows' own number).
2. Response time measured by the app's concurrent scan vs. a separate Windows
   ping sent straight afterwards (checks that pinging at the same time does
   not distort the times).
3. UP/DOWN reported by the app vs. "Received = 1" / "Received = 0" in the
   Windows ping statistics.
4. IPv4 validation vs. Windows' own parser (socket.inet_pton), on hand-picked
   and random strings.

Only 127.0.0.1, public DNS servers and the documentation range 192.0.2.x are
pinged, so no one else's device on a local network is contacted.
"""

import platform
import random
import re
import socket
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from network_health_checker.pinger import parse_ping_output  # noqa: E402
from network_health_checker.scanner import UP, scan  # noqa: E402
from network_health_checker.validator import validate_entry  # noqa: E402

RESPONDING = ["127.0.0.1", "8.8.8.8", "1.1.1.1"]
SILENT = ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
ROUNDS = 20
TIMEOUT_MS = 1000

_AVERAGE = re.compile(r"Average = (\d+)ms")
_RECEIVED = re.compile(r"Received = (\d+)")


def windows_ping(address):
    completed = subprocess.run(
        ["ping", "-n", "1", "-w", str(TIMEOUT_MS), address],
        capture_output=True,
        text=True,
        errors="replace",
    )
    return completed.returncode, completed.stdout


def check_parsing():
    print("1. App's parsed time vs. Windows' own 'Average = Xms' (same ping)")
    for address in RESPONDING:
        errors = []
        for _ in range(ROUNDS):
            code, output = windows_ping(address)
            reference = _AVERAGE.search(output)
            app = parse_ping_output(code, output, TIMEOUT_MS)
            if reference and app.reachable:
                errors.append(app.response_time_ms - float(reference.group(1)))
        print(
            f"   {address:<10} pings compared: {len(errors):>2}  "
            f"max |error|: {max(map(abs, errors)):.0f} ms  "
            f"errors seen: {sorted(set(errors))}"
        )


def check_concurrent_scan():
    print("2. App's concurrent scan vs. a separate Windows ping straight afterwards")
    differences = {address: [] for address in RESPONDING}
    app_times = {address: [] for address in RESPONDING}
    ref_times = {address: [] for address in RESPONDING}
    for _ in range(ROUNDS):
        results = {r.address: r for r in scan(RESPONDING, timeout_ms=TIMEOUT_MS)}
        for address in RESPONDING:
            code, output = windows_ping(address)
            reference = _AVERAGE.search(output)
            result = results[address]
            if reference and result.status == UP:
                app_ms = result.response_time_ms
                ref_ms = float(reference.group(1))
                # Windows prints "time<1ms" as Average = 0ms; the app records 1 ms.
                app_times[address].append(app_ms)
                ref_times[address].append(ref_ms)
                differences[address].append(app_ms - ref_ms)
    for address in RESPONDING:
        diffs = differences[address]
        print(
            f"   {address:<10} pairs: {len(diffs):>2}  "
            f"median app: {statistics.median(app_times[address]):.0f} ms  "
            f"median Windows: {statistics.median(ref_times[address]):.0f} ms  "
            f"median difference: {statistics.median(diffs):+.0f} ms  "
            f"max |difference|: {max(map(abs, diffs)):.0f} ms"
        )


def check_status():
    print("3. App's UP/DOWN vs. Windows ping 'Received = N'")
    targets = RESPONDING + SILENT
    agree = total = 0
    for _ in range(5):
        results = {r.address: r for r in scan(targets, timeout_ms=TIMEOUT_MS)}
        for address in targets:
            _, output = windows_ping(address)
            received = _RECEIVED.search(output)
            reference_up = bool(received) and received.group(1) == "1" and "TTL=" in output
            total += 1
            agree += (results[address].status == UP) == reference_up
    print(f"   {agree} of {total} checks agree")


def check_validator():
    print("4. App's IPv4 validation vs. socket.inet_pton (Windows' own parser)")
    hand_picked = [
        "192.168.1.1", "0.0.0.0", "255.255.255.255", "192.168.1.999", "10.0.0.256",
        "192.168.01.5", "1.2.3", "1.2.3.4.5", "hello", "-1.2.3.4", "1.2.3.4 ", "::1",
        "1..2.3", "01.2.3.4", "1.2.3.04", "0x7f.0.0.1", "1.2.3.4/24", "１.2.3.4",
    ]
    rng = random.Random(1)
    random_strings = [
        "".join(rng.choice("0123456789..") for _ in range(rng.randint(1, 15)))
        for _ in range(20000)
    ]
    disagreements = []
    for text in hand_picked + random_strings:
        try:
            socket.inet_pton(socket.AF_INET, text)
            reference = True
        except OSError:
            reference = False
        if validate_entry(text).is_valid != reference:
            disagreements.append(text)
    valid = sum(1 for t in random_strings if validate_entry(t).is_valid)
    print(
        f"   {len(hand_picked)} hand-picked + {len(random_strings)} random strings "
        f"({valid} of the random ones valid): {len(disagreements)} disagreements"
    )


if __name__ == "__main__":
    if platform.system() != "Windows":
        sys.exit("This validation compares against Windows ping; run it on Windows.")
    check_parsing()
    check_concurrent_scan()
    check_status()
    check_validator()
