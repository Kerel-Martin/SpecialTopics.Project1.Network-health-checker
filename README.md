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
