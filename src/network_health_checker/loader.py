"""Load candidate IPv4 addresses from a text file (requirement R1)."""

from pathlib import Path

# SPEC.md, R1 and Section 4: a scan contains no more than 20 input entries.
MAX_ENTRIES = 20


class InputFileError(Exception):
    """Raised when the input file cannot be used for a scan."""


def load_targets(path):
    """Return the non-blank lines of the file at ``path``.

    Each line is one candidate IPv4 address. Leading and trailing spaces are
    removed and blank lines are skipped. The file must contain between 1 and
    MAX_ENTRIES entries, otherwise InputFileError is raised.
    """
    file_path = Path(path)

    if not file_path.is_file():
        raise InputFileError(f"File not found: {file_path}")

    try:
        # "utf-8-sig" also accepts files saved by Windows Notepad with a BOM.
        text = file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise InputFileError(f"File is not a UTF-8 text file: {file_path}")

    entries = [line.strip() for line in text.splitlines() if line.strip()]

    if not entries:
        raise InputFileError(f"File contains no addresses: {file_path}")

    if len(entries) > MAX_ENTRIES:
        raise InputFileError(
            f"File contains {len(entries)} entries; "
            f"the maximum is {MAX_ENTRIES}: {file_path}"
        )

    return entries
