"""Ping one IPv4 address with the operating system's ping command (R3, R4)."""

import math
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

DEFAULT_TIMEOUT_MS = 1000

# Every ping reply line contains "TTL=" (Windows) or "ttl=" (Linux, macOS),
# whatever the system language. The exit code alone is not enough: Windows
# ping exits with 0 when a router answers "Destination host unreachable".
_REPLY_PATTERN = re.compile(r"\bttl=\s*\d+", re.IGNORECASE)

# Matches "time=1.19 ms" (Linux), "time=2ms" or "time<1ms" (Windows) and
# translated forms such as "Zeit=3ms", without depending on the word "time".
_TIME_PATTERN = re.compile(r"[=<]\s*(\d+(?:[.,]\d+)?)\s*ms\b", re.IGNORECASE)


class PingUnavailableError(Exception):
    """Raised when the computer has no ping command."""


@dataclass(frozen=True)
class PingResult:
    reachable: bool
    response_time_ms: Optional[float] = None


def build_ping_command(address, timeout_ms=DEFAULT_TIMEOUT_MS, system=None):
    """Return the ping command that sends one request to ``address``."""
    system = system or platform.system()
    if system == "Windows":
        # -n count, -w timeout in milliseconds
        return ["ping", "-n", "1", "-w", str(timeout_ms), address]
    if system == "Darwin":
        # macOS: -W timeout in milliseconds
        return ["ping", "-c", "1", "-W", str(timeout_ms), address]
    # Linux: -W timeout in whole seconds
    seconds = max(1, math.ceil(timeout_ms / 1000))
    return ["ping", "-c", "1", "-W", str(seconds), address]


def parse_ping_output(returncode, output):
    """Turn the exit code and text printed by ping into a PingResult.

    Windows reports replies faster than 1 ms as "time<1ms"; that is
    recorded as 1 ms.
    """
    if returncode != 0 or not _REPLY_PATTERN.search(output):
        return PingResult(False)
    match = _TIME_PATTERN.search(output)
    if match is None:
        return PingResult(True)
    return PingResult(True, float(match.group(1).replace(",", ".")))


def ping(address, timeout_ms=DEFAULT_TIMEOUT_MS, run=subprocess.run):
    """Ping ``address`` once and return a PingResult."""
    command = build_ping_command(address, timeout_ms)
    options = {}
    if platform.system() == "Windows":
        # Stop a console window flashing up for each ping when using the GUI.
        options["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        completed = run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout_ms / 1000 + 5,
            **options,
        )
    except FileNotFoundError:
        raise PingUnavailableError("The 'ping' command was not found on this computer.")
    except subprocess.TimeoutExpired:
        return PingResult(False)

    return parse_ping_output(completed.returncode, completed.stdout)
