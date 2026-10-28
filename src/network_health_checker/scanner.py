"""Validate a list of entries and ping the valid ones concurrently (R2, R3, R4, R7)."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

from .pinger import DEFAULT_TIMEOUT_MS, ping
from .validator import INVALID, validate_entries

UP = "UP"
DOWN = "DOWN"


@dataclass(frozen=True)
class ScanResult:
    address: str
    status: str  # UP, DOWN or INVALID
    response_time_ms: Optional[float] = None
    details: str = ""


def scan(texts, timeout_ms=DEFAULT_TIMEOUT_MS, ping_func=ping):
    """Return one ScanResult per entry in ``texts``, in the same order.

    INVALID entries are never passed to ``ping_func`` (AC2). Valid addresses
    are pinged at the same time, so a scan takes about one timeout rather
    than one timeout per address.
    """
    entries = validate_entries(texts)
    valid = [entry.text for entry in entries if entry.is_valid]

    replies = []
    if valid:
        with ThreadPoolExecutor(max_workers=len(valid)) as pool:
            replies = list(pool.map(lambda address: ping_func(address, timeout_ms), valid))

    reply_iter = iter(replies)
    results = []
    for entry in entries:
        if not entry.is_valid:
            results.append(ScanResult(entry.text, INVALID, details=entry.reason))
            continue
        reply = next(reply_iter)
        status = UP if reply.reachable else DOWN
        results.append(ScanResult(entry.text, status, reply.response_time_ms))
    return results


def summarize(results):
    """Return the R7 summary counts for a finished scan."""
    up = sum(1 for result in results if result.status == UP)
    down = sum(1 for result in results if result.status == DOWN)
    return {
        "input_entries": len(results),
        "checked": up + down,
        "up": up,
        "down": down,
        "invalid": len(results) - up - down,
    }


def describe_response(result):
    """Return the text shown in the Response Time column."""
    if result.status == UP:
        if result.response_time_ms is None:
            return "Reply received (time not reported)"
        return f"{result.response_time_ms:g} ms"
    if result.status == DOWN:
        return "No reply"
    return f"Not checked: {result.details}"
