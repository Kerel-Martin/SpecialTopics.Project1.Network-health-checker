"""Tests for R3 / R4: running ping and reading its output."""

import shutil
import subprocess
import unittest

from network_health_checker.pinger import (
    PingUnavailableError,
    build_ping_command,
    parse_ping_output,
    ping,
)

WINDOWS_REPLY = """
Pinging 192.168.1.1 with 32 bytes of data:
Reply from 192.168.1.1: bytes=32 time=2ms TTL=64

Ping statistics for 192.168.1.1:
    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 2ms, Maximum = 2ms, Average = 2ms
"""

WINDOWS_FAST_REPLY = "Reply from 127.0.0.1: bytes=32 time<1ms TTL=128\n"

WINDOWS_GERMAN_REPLY = "Antwort von 192.168.1.1: Bytes=32 Zeit=3ms TTL=64\n"

# Windows exits with 0 here even though the target itself did not answer.
WINDOWS_UNREACHABLE = """
Pinging 192.168.1.50 with 32 bytes of data:
Reply from 192.168.1.10: Destination host unreachable.

Ping statistics for 192.168.1.50:
    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),
"""

WINDOWS_TIMEOUT = """
Pinging 192.168.1.50 with 32 bytes of data:
Request timed out.
"""

LINUX_REPLY = """PING 192.168.18.1 (192.168.18.1) 56(84) bytes of data.
64 bytes from 192.168.18.1: icmp_seq=1 ttl=64 time=1.19 ms

--- 192.168.18.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.186/1.186/1.186/0.000 ms
"""

LINUX_NO_REPLY = """PING 192.168.18.69 (192.168.18.69) 56(84) bytes of data.

--- 192.168.18.69 ping statistics ---
1 packets transmitted, 0 received, 100% packet loss, time 0ms
"""


class BuildCommandTests(unittest.TestCase):
    def test_windows_command_uses_milliseconds(self):
        self.assertEqual(
            build_ping_command("10.0.0.1", 1000, system="Windows"),
            ["ping", "-n", "1", "-w", "1000", "10.0.0.1"],
        )

    def test_linux_command_uses_whole_seconds(self):
        self.assertEqual(
            build_ping_command("10.0.0.1", 1000, system="Linux"),
            ["ping", "-c", "1", "-W", "1", "10.0.0.1"],
        )
        self.assertEqual(build_ping_command("10.0.0.1", 1500, system="Linux")[4], "2")
        self.assertEqual(build_ping_command("10.0.0.1", 200, system="Linux")[4], "1")

    def test_macos_command_uses_milliseconds(self):
        self.assertEqual(
            build_ping_command("10.0.0.1", 1000, system="Darwin"),
            ["ping", "-c", "1", "-W", "1000", "10.0.0.1"],
        )


class ParseOutputTests(unittest.TestCase):
    def test_windows_reply(self):
        result = parse_ping_output(0, WINDOWS_REPLY)
        self.assertTrue(result.reachable)
        self.assertEqual(result.response_time_ms, 2.0)

    def test_windows_reply_under_one_millisecond(self):
        result = parse_ping_output(0, WINDOWS_FAST_REPLY)
        self.assertTrue(result.reachable)
        self.assertEqual(result.response_time_ms, 1.0)

    def test_windows_reply_in_another_language(self):
        result = parse_ping_output(0, WINDOWS_GERMAN_REPLY)
        self.assertTrue(result.reachable)
        self.assertEqual(result.response_time_ms, 3.0)

    def test_windows_destination_unreachable_is_not_a_reply(self):
        result = parse_ping_output(0, WINDOWS_UNREACHABLE)
        self.assertFalse(result.reachable)
        self.assertIsNone(result.response_time_ms)

    def test_windows_timeout(self):
        self.assertFalse(parse_ping_output(1, WINDOWS_TIMEOUT).reachable)

    def test_linux_reply(self):
        result = parse_ping_output(0, LINUX_REPLY)
        self.assertTrue(result.reachable)
        self.assertEqual(result.response_time_ms, 1.19)

    def test_linux_no_reply(self):
        result = parse_ping_output(1, LINUX_NO_REPLY)
        self.assertFalse(result.reachable)
        self.assertIsNone(result.response_time_ms)


class PingFunctionTests(unittest.TestCase):
    def test_missing_ping_command_raises_clear_error(self):
        def run(*args, **kwargs):
            raise FileNotFoundError("ping")

        with self.assertRaisesRegex(PingUnavailableError, "not found"):
            ping("10.0.0.1", run=run)

    def test_hung_ping_counts_as_no_reply(self):
        def run(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        self.assertFalse(ping("10.0.0.1", run=run).reachable)


@unittest.skipIf(shutil.which("ping") is None, "ping command not available")
class RealPingTests(unittest.TestCase):
    """AC3 / AC4 with the real ping command (no external network needed)."""

    def test_loopback_address_is_up_with_a_response_time(self):
        result = ping("127.0.0.1", timeout_ms=1000)
        self.assertTrue(result.reachable)
        self.assertIsNotNone(result.response_time_ms)
        self.assertGreaterEqual(result.response_time_ms, 0)

    def test_documentation_address_is_down(self):
        # 192.0.2.1 is reserved for documentation (RFC 5737) and is never used
        # by a real device, so it must not reply.
        result = ping("192.0.2.1", timeout_ms=1000)
        self.assertFalse(result.reachable)
        self.assertIsNone(result.response_time_ms)


if __name__ == "__main__":
    unittest.main()
