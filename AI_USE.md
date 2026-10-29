# AI Tool Usage Log

## Project

Network Health Checker — Project 1, Milestones 1 and 2

## AI Tools Used

### 1. ChatGPT (OpenAI)

- **Purpose:** Brainstorming and narrowing the project idea; understanding how ping-based network checking works; drafting the project specification, numbered requirements, acceptance criteria, proposal, and AI critique.
- **Work assisted:** Problem definition, scope boundaries, test planning, input/output examples, and documentation structure.
- **How the output was checked:** Requirements were compared with the instructor's milestone instructions and grading rubric. The specification was reviewed for measurable requirements, corresponding acceptance criteria, and a bounded scope.
- **Human contribution:** Selected the Network Health Checker project, considered the required functionality and optional GUI, and reviewed the proposed specification.

## Milestone 2

### 2. Claude Code (Anthropic, model Claude Opus 5.5) — 28 October 2026

- **What was asked:** Inspect the existing README.md, SPEC.md, AI_USE.md and .gitignore. Then build a first prototype that loads a text file of up to 20 candidate IPv4 addresses and validates them (R1, R2). Organize the repository into `src/`, `tests/` and `data/`, add automated tests and run them, and document the install/run/test commands for Windows PowerShell. Do not change the approved specification without explaining any conflict first, and do not claim that unimplemented features work.
- **What the AI produced:**
  - `src/network_health_checker/loader.py`: file loading and the 1–20 entry limit (R1).
  - `src/network_health_checker/validator.py`: IPv4 validation with Python's `ipaddress` module (R2).
  - `src/network_health_checker/cli.py`: the command-line interface.
  - `src/network_health_checker/gui.py`: an optional Tkinter window.
  - `src/main.py`: the entry point.
  - `data/sample_targets.txt`: sample data.
  - `requirements.txt`: lists no packages, because only the standard library is used.
  - `tests/`: 21 unittest tests (later 45, see the follow-up below).
  - New Milestone 2 sections in README.md.
- **What was not changed:** SPEC.md and the original project proposal in README.md. `.gitignore` was checked and already excluded `.venv`, `__pycache__/` and `.env`.
- **Spec consistency issue the AI raised:** SPEC.md (Sections 1 and 4) makes the command-line interface the required interface. A GUI is only an optional enhancement, to be considered after all required features pass. The Tkinter window was therefore added as an optional extra on top of the command-line version, and the specification was not edited. Whether to amend SPEC.md to make the GUI the main interface is left to the team and the instructor.
- **How it was verified:**
  - Ran `python3 -m unittest -v` on Ubuntu 24.04 with Python 3.12.3. The first run gave 21 tests, 20 passed and 1 skipped: the GUI test, because Tkinter was not installed. After the team installed `python3-tk`, all 21 tests passed. The Tkinter window was also launched with the sample file and checked visually.
  - Ran `python3 src/main.py data/sample_targets.txt` and compared the output with the expected VALID/INVALID results.
  - Checked `.gitignore` with `git check-ignore`.
  - Searched the files for passwords, API keys and tokens; none were found.
- **Still to be verified by the team:** Run the tests and the GUI on Windows. Review all generated code before committing it.
- **Not implemented at this stage:** ping/UP-DOWN (R3), response times (R4), the five-second performance target (R5) and CSV export (R6). Ping was added in the follow-up session below.

#### Follow-up, same day: adding ping (R3, R4, R7)

- **What was asked:** The team added `192.168.18.17` and `192.168.18.69` to the sample file, expecting one to show as valid and the other as invalid. Both showed "VALID — Not checked (ping not implemented yet)". The team asked for ping to work.
- **Explanation the AI gave:** "Valid" (R2) only means the text is a correctly formatted IPv4 address. Both addresses are correctly formatted. Whether a device answers is a separate question, answered by ping (R3).
- **What the AI produced:**
  - `src/network_health_checker/pinger.py`: runs the system `ping` command on Windows, Linux or macOS. A reply counts only if the output contains a TTL value, so a Windows "Destination host unreachable" message, which still exits with code 0, counts as DOWN. It reads the response time in ms.
  - `src/network_health_checker/scanner.py`: pings all valid addresses at the same time using a thread pool, never pings INVALID entries, and calculates the R7 counts.
  - Updated `cli.py` (UP/DOWN/INVALID table, summary counts, scan time and a `--timeout` option) and `gui.py` (scans in a background thread so the window does not freeze, with a "Scan again" button).
  - New tests: `tests/test_pinger.py`, `tests/test_scanner.py` and `tests/fakes.py`, a fake ping with fixed answers. `test_cli.py` and `test_gui.py` were rewritten to use temporary files and the fake ping, so they no longer depend on the contents of `data/sample_targets.txt` or on the network.
  - The README Milestone 2 section was rewritten. The original proposal and SPEC.md were not changed.
- **How it was verified:**
  - `python -m unittest -v` on Ubuntu 24.04 with Python 3.12.3: 45 tests, all passed. This includes real pings: `127.0.0.1` gave UP with a response time, and `192.0.2.1`, a documentation-only address, gave DOWN.
  - A real scan of `data/sample_targets.txt` on the team's home network gave `8.8.8.8` UP (41.8 ms), five DOWN, four INVALID, in 1.01 s.
  - The GUI was opened and showed the same results.
  - Before writing the code, the two addresses were checked by hand with `ping` and the ARP table. `192.168.18.17` is a device on the network that does not answer ping, probably because of its firewall; no device answered at `192.168.18.69`.
- **Still not claimed:**
  - R5: the AC5 measurement (20 valid addresses, 3 runs, documented conditions) has not been done.
  - R6: CSV export is not implemented.
  - Windows: when this entry was written, the tests had not been run on Windows. On 29 October 2026 the team ran them on a Windows laptop and all passed; see README.md.

## Future Updates

Add an entry whenever another AI tool is used. Record the tool name, date, purpose, affected files or code, and how its output was checked.
