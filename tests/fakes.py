"""A fake ping function so tests do not depend on the real network."""

import threading

from network_health_checker.pinger import PingResult


class FakePing:
    """Answers from a fixed table and records every address it was asked about.

    ``replies`` maps an address to its response time in ms; any address not in
    the table gets no reply (DOWN).
    """

    def __init__(self, replies=None):
        self.replies = replies or {}
        self.pinged = []
        self._lock = threading.Lock()

    def __call__(self, address, timeout_ms):
        with self._lock:
            self.pinged.append(address)
        if address in self.replies:
            return PingResult(True, self.replies[address])
        return PingResult(False)
