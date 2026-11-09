"""Export scan results to a CSV file (requirement R6)."""

import csv

# SPEC.md, Section 5: the CSV file contains at least these columns.
CSV_COLUMNS = ["ip_address", "status", "response_time_ms"]


class ExportError(Exception):
    """Raised when the CSV file cannot be written."""


def format_response_time(result):
    """Return the response time for the CSV, or "" when there is none."""
    if result.response_time_ms is None:
        return ""
    return f"{result.response_time_ms:g}"


def export_csv(results, path):
    """Write one row per scan result to ``path``, in input order.

    DOWN and INVALID rows have an empty response_time_ms, as in the SPEC.md
    example. INVALID entries keep their original text in ip_address.
    """
    try:
        # newline="" stops the csv module writing blank lines between rows on
        # Windows; "utf-8-sig" lets Excel open the file with the right encoding.
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_COLUMNS)
            for result in results:
                writer.writerow([result.address, result.status, format_response_time(result)])
    except OSError as error:
        # For example: the folder does not exist, or the file is open in Excel.
        raise ExportError(f"Could not write {path}: {error.strerror or error}")
