"""Network Health Checker - Milestone 2 prototype.

This prototype loads a text file of 1-20 candidate IPv4 addresses (R1),
marks invalid entries (R2), pings the valid ones (R3, R4) and counts the
results (R7). Results can be exported to CSV (R6). The five-second
performance target (R5) was measured on Linux (see README.md).
"""

from .exporter import CSV_COLUMNS, ExportError, export_csv
from .loader import MAX_ENTRIES, InputFileError, load_targets
from .pinger import PingResult, PingUnavailableError, ping
from .scanner import DOWN, UP, ScanResult, scan, summarize
from .validator import INVALID, VALID, Entry, validate_entries, validate_entry

__all__ = [
    "CSV_COLUMNS",
    "ExportError",
    "export_csv",
    "MAX_ENTRIES",
    "InputFileError",
    "load_targets",
    "PingResult",
    "PingUnavailableError",
    "ping",
    "DOWN",
    "UP",
    "ScanResult",
    "scan",
    "summarize",
    "INVALID",
    "VALID",
    "Entry",
    "validate_entries",
    "validate_entry",
]
