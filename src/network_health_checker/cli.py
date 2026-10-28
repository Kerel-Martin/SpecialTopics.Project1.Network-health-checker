"""Command-line interface for the prototype."""

import argparse
import sys
import time

from .loader import InputFileError, load_targets
from .pinger import DEFAULT_TIMEOUT_MS, PingUnavailableError, ping
from .scanner import describe_response, scan, summarize


def format_report(results, seconds=None):
    """Return the results table and summary counts as text."""
    lines = [f"{'IP Address':<18}{'Status':<10}Response Time"]
    for result in results:
        lines.append(f"{result.address:<18}{result.status:<10}{describe_response(result)}")

    counts = summarize(results)
    lines.append("")
    lines.append(f"Input entries: {counts['input_entries']}")
    lines.append(f"Valid addresses checked: {counts['checked']}")
    lines.append(f"UP: {counts['up']}")
    lines.append(f"DOWN: {counts['down']}")
    lines.append(f"Invalid: {counts['invalid']}")
    if seconds is not None:
        lines.append(f"Scan time: {seconds:.2f} s")
    return "\n".join(lines)


def main(argv=None, ping_func=ping):
    parser = argparse.ArgumentParser(
        prog="network_health_checker",
        description="Validate and ping up to 20 IPv4 addresses from a text file.",
    )
    parser.add_argument("file", nargs="?", help="text file with one IPv4 address per line")
    parser.add_argument("--gui", action="store_true", help="open the Tkinter window instead")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        metavar="MS",
        help=f"ping timeout in milliseconds (default {DEFAULT_TIMEOUT_MS})",
    )
    args = parser.parse_args(argv)

    if args.timeout <= 0:
        parser.error("--timeout must be a positive number of milliseconds")

    if args.gui:
        from .gui import run_gui

        run_gui(args.file, timeout_ms=args.timeout)
        return 0

    if args.file is None:
        parser.error("a file is required unless --gui is used")

    try:
        texts = load_targets(args.file)
    except InputFileError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    try:
        results = scan(texts, timeout_ms=args.timeout, ping_func=ping_func)
    except PingUnavailableError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    seconds = time.perf_counter() - start

    print(format_report(results, seconds))
    return 0
