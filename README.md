# SpecialTopics.Project1.Network-health-checker
# Network Health Checker

## Project Proposal

### Problem

Checking whether multiple devices on a network are responding can take time when each address must be checked manually. This project will develop a Python application that checks a list of up to 20 IPv4 addresses and reports their reachability status and response times.

### Why It Matters

The application will provide a simple way to perform basic network connectivity checks. It can help users identify addresses that respond to ping and those that do not respond within a defined timeout. The project will also demonstrate practical concepts such as IP address validation, subprocess execution, concurrent tasks, performance testing, and CSV file handling.

### Team Members and Roles

- **Kerel Martin Fahim & Cynthia Ziadeh — project:** Requirements and specification, implementation with AI assistance, testing, debugging, documentation, and demonstration.

### Tools Plan

- **Python:** Main programming language.
- **Windows ping utility:** Check whether IP addresses respond.
- **Python standard library:** Validate IPv4 addresses, run checks, and export results to CSV.
- **Git and GitHub:** Version control and project submission.
- **AI assistance:** Help review the specification, explain implementation choices, and troubleshoot code. All generated code and test results will be checked before acceptance.

The required version will use a command-line interface. A simple graphical interface may be considered later if the required functionality and acceptance tests are completed first.

### Success Criteria

The project will be considered successful when all seven requirements in `SPEC.md` pass their acceptance tests, including the target of scanning 20 valid addresses within five seconds under documented test conditions, and the results can be exported to CSV.

## Milestone 2 Prototype

This prototype loads a text file of candidate IPv4 addresses, marks invalid entries, and pings each valid address using the operating system's own `ping` command. It then shows UP/DOWN, response times and summary counts. It works with the Windows `ping` command and with the Linux one.

### Status of the requirements in `SPEC.md`

| Requirement | Status in this prototype |
|---|---|
| R1 — Input file (1–20 addresses, one per line) | **Implemented and tested** |
| R2 — Input validation (INVALID entries are not pinged) | **Implemented and tested** |
| R3 — UP / DOWN reachability | **Implemented and tested** |
| R4 — Response time in ms, or "No reply" | **Implemented and tested** |
| R5 — 20 addresses within 5 seconds | Pings run concurrently with a bounded timeout and the scan time is printed, but the AC5 measurement (20 valid addresses, 3 runs, documented conditions) **has not been done yet**, so R5 is **not claimed** |
| R6 — CSV export | **Not implemented** |
| R7 — Summary counts | **Implemented and tested** |

A **valid** address is one written in correct IPv4 format. Whether it is **UP** or **DOWN** depends only on whether it answers ping. As SPEC.md says, DOWN means no reply arrived within the timeout. The device may still be switched on but blocking ping with a firewall; Windows blocks ping by default.

### Repository structure

```text
README.md             Proposal and how to run the prototype
SPEC.md               Approved specification (unchanged)
AI_USE.md             AI tool usage log
requirements.txt      Dependencies (standard library only, nothing to install)
.gitignore            Ignores .venv/, __pycache__/, .env and other local files
src/
  main.py             Entry point
  network_health_checker/
    loader.py         R1: read the file, enforce the 1–20 entry limit
    validator.py      R2: check each entry with Python's ipaddress module
    pinger.py         R3/R4: run the system ping command, read UP/DOWN and time
    scanner.py        Ping valid addresses concurrently; R7 summary counts
    cli.py            Command-line interface (the required interface in SPEC.md)
    gui.py            Optional Tkinter window (an optional enhancement in SPEC.md)
data/
  sample_targets.txt  Small sample with valid and invalid entries
tests/                Automated tests (unittest)
```

### Requirements to run it

- Python 3.10 or newer. Development and testing used Python 3.12.3.
- No extra packages: only the Python standard library is used.
- The `ping` command. It is built into Windows and Ubuntu.
- Tkinter, but only for the optional GUI. It is included in the standard Python installer from python.org on Windows. On Ubuntu/Debian, install it with `sudo apt install python3-tk`.

### Install and run on Windows (PowerShell)

Run these from the repository folder:

```powershell
cd SpecialTopics.Project1.Network-health-checker
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src\main.py data\sample_targets.txt
```

If PowerShell says that running scripts is disabled, run this once and then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Open the optional Tkinter window. The file is scanned as soon as it is loaded; use **Scan again** to repeat the scan.

```powershell
python src\main.py --gui
python src\main.py --gui data\sample_targets.txt
```

Change the ping timeout (default 1000 ms):

```powershell
python src\main.py data\sample_targets.txt --timeout 500
```

Run the automated tests:

```powershell
python -m unittest -v
```

### Install and run on Linux (bash)

Use `python3`, not `py`: `py` is the Windows Python launcher, and on Linux it may be an unrelated program or missing entirely.

```bash
cd SpecialTopics.Project1.Network-health-checker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py data/sample_targets.txt
python src/main.py --gui data/sample_targets.txt
python -m unittest -v
```

### Using your own file

Create a text file with one IPv4 address per line, up to 20 lines. Blank lines are ignored. Then pass the file to the program:

```powershell
python src\main.py C:\path\to\targets.txt
```

A file with more than 20 entries, no entries, or that does not exist is rejected with an error message (exit code 1). Only ping networks and devices you own or are allowed to check.

### Example output

This is a real run of `python src/main.py data/sample_targets.txt` on a home Wi-Fi network (192.168.18.0/24), on 28 October 2026. Results depend on the network.

```text
IP Address        Status    Response Time
192.168.1.1       DOWN      No reply
192.168.1.10      DOWN      No reply
192.168.1.20      DOWN      No reply
192.168.1.999     INVALID   Not checked: Octet 999 (> 255) not permitted in '192.168.1.999'
192.168.18.17     DOWN      No reply
192.168.18.69     DOWN      No reply
10.0.0.256        INVALID   Not checked: Octet 256 (> 255) not permitted in '10.0.0.256'
hello             INVALID   Not checked: Expected 4 octets in 'hello'
192.168.01.5      INVALID   Not checked: Leading zeros are not permitted in '01' in '192.168.01.5'
8.8.8.8           UP        41.8 ms

Input entries: 10
Valid addresses checked: 6
UP: 1
DOWN: 5
Invalid: 4
Scan time: 1.01 s
```

Notes on these results:

- The `192.168.1.x` addresses are not on this network, so they are DOWN.
- `192.168.18.17` is a real device on the network: it answered at the network (ARP) level but did not reply to ping, probably because its firewall blocks ping.
- No device answered at `192.168.18.69`.

### How the requirements were checked

Most tests use a fake ping function with fixed answers, so they give the same result on any network. Two tests (`RealPingTests` in `tests/test_pinger.py`) run the real `ping` command.

- **AC1 (R1) — passed.** The `tests/test_loader.py` tests check that the program:
  - loads files with 1 and with exactly 20 entries
  - rejects a file with 21 entries
  - rejects empty and missing files
  - skips blank lines and extra spaces
  - reads Windows line endings and Notepad's UTF-8 BOM
- **AC2 (R2) — passed.** The `tests/test_validator.py` tests mark these entries INVALID:
  - octets above 255, such as `192.168.1.999`
  - the wrong number of octets
  - text, leading zeros, negative octets, IPv6 addresses and empty entries

  `tests/test_scanner.py` records every address sent to ping and confirms that INVALID entries are never pinged.
- **AC3 (R3) — passed.** These tests run real pings:
  - `127.0.0.1` (this computer) is reported as UP.
  - `192.0.2.1` is reported as DOWN. It is an address reserved for documentation, so no real device uses it.

  `tests/test_pinger.py` also checks saved Windows and Linux ping output. This includes the Windows case where a router answers "Destination host unreachable" with exit code 0, which must count as DOWN.
- **AC4 (R4) — passed.** A real ping to `127.0.0.1` returns a numeric time in ms, and a DOWN address returns no time ("No reply"). Response times are read from Linux output (`time=1.19 ms`), Windows output (`time=2ms`, `time<1ms`, recorded as 1 ms) and non-English Windows output (`Zeit=3ms`).
- **AC7 (R7) — passed.** `tests/test_scanner.py` and `tests/test_cli.py` check that the counts for the SPEC.md example (4 entries: 2 UP, 1 DOWN, 1 INVALID) are correct.
- **Concurrency (supports R5, but is not the AC5 test):** 20 simulated pings that each take 0.3 s finish in under 2 s, instead of the 6 s they would take one after another.

Test result on Ubuntu 24.04 (Linux), Python 3.12.3, with Tkinter installed, 28 October 2026:

```text
Ran 45 tests in 1.630s

OK
```

The GUI was also opened by hand with `data/sample_targets.txt` and showed the same UP/DOWN/INVALID results and counts as the command-line version.

**Not yet done:** the tests have not been run on Windows. Run them there with the command above and record the result here. Real Windows ping output is only covered by the saved examples in `tests/test_pinger.py`.
