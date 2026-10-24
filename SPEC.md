# Network Health Checker — Project Specification

## 1. Goal and Users

### Goal

The goal of this project is to develop a network health checker that checks a user-provided list of IP addresses and reports whether they respond to ping requests. The application will display response times, identify addresses that do not respond within a defined timeout, summarize the results, and export them to a CSV file.

The main objective is to make basic network checks faster and easier than checking each address manually.

### Intended users

The intended users are students, home network users, and beginners who want to perform basic network connectivity checks.

### Problem boundaries

The application will check a maximum of 20 IPv4 addresses per scan. It will use the computer's existing network connection and operating-system ping utility. The required version will be command-line based. A simple graphical user interface may be considered as an optional enhancement after all required features pass their acceptance tests.

A DOWN result means that no ping reply was received within the configured timeout. It does not necessarily mean that the device is physically offline.

## 2. Context: Hardware, Software, and Versions

### Hardware

- A Windows computer or laptop.
- A network connection, such as home Wi-Fi or Ethernet.
- Access to at least one device that responds to ping for testing.

Twenty physical devices are not required. The test list may include valid addresses that do not respond, provided testing is performed on a network the user is authorized to check.

### Software

- Operating system: Windows 10 or Windows 11.
- Programming language: Python.
- Standard Python modules: `ipaddress`, `subprocess`, `csv`, and a suitable concurrency module.
- Network checking: the Windows `ping` utility.
- Development and version control: a code editor, Git, and GitHub.

The exact Python and operating-system versions used for implementation and testing will be recorded in the final project documentation.

The required implementation should use Python's standard library unless an additional dependency is justified.

## 3. Requirements

**R1 — Input:** The application shall accept a text file containing between 1 and 20 candidate IPv4 addresses, with one address per line.

**R2 — Input validation:** The application shall identify invalid IPv4 addresses and exclude them from ping checks.

**R3 — Reachability status:** The application shall classify each valid address as UP when a ping reply is received and DOWN when no reply is received before the configured timeout.

**R4 — Response time:** For each address that responds, the application shall display its measured ping response time in milliseconds. For addresses that do not respond, it shall display a clear indication that no response time is available.

**R5 — Performance:** Under the defined test conditions, the application shall complete a scan of 20 valid IPv4 addresses within 5 seconds. The implementation shall use concurrent checks and a bounded timeout to support this target.

**R6 — CSV export:** The application shall allow the user to export scan results to a CSV file containing the address, status, and response time. Invalid input entries shall be identifiable in the exported results.

**R7 — Summary:** At the end of a scan, the application shall display counts for the total number of input entries, valid addresses checked, UP addresses, DOWN addresses, and invalid entries.

## 4. Constraints

- The required application shall run on Windows using Python.
- Each scan shall contain no more than 20 input entries.
- The input format shall be a text file with one candidate IPv4 address per line.
- The required interface shall be command-line based; a graphical interface is optional and is not required for acceptance.
- Ping results depend on network conditions, device configuration, and firewall rules. The application can report only whether a response was received within the timeout.
- The five-second performance target applies to a documented test environment and a defined list of 20 valid addresses. It is not a guarantee for every network.
- Testing shall be limited to networks and devices the user owns or is authorized to check.
- The project shall be developed and demonstrated within the course project schedule.

## 5. Interfaces: Input and Output Examples

### Input

The user provides a text file named `targets.txt`, containing one address per line.

Example:

```text
192.168.1.1
192.168.1.10
192.168.1.20
192.168.1.999
```

These are illustrative addresses. Actual test addresses will be selected from an authorized test network.

### Terminal output

An illustrative output could look like this:

```text
IP Address       Status    Response Time
192.168.1.1      UP        2.4 ms
192.168.1.10     UP        5.8 ms
192.168.1.20     DOWN      No reply
192.168.1.999    INVALID   Not checked

Input entries: 4
Valid addresses checked: 3
UP: 2
DOWN: 1
Invalid: 1
```

The response times and statuses above are examples, not real measurements.

### CSV output

The application shall create a CSV file containing at least these columns:

```text
ip_address,status,response_time_ms
192.168.1.1,UP,2.4
192.168.1.10,UP,5.8
192.168.1.20,DOWN,
192.168.1.999,INVALID,
```

The actual response times and statuses will depend on the test environment. The application shall clearly represent unavailable response times.

## 6. Acceptance Criteria

### AC1 — Input file (R1)

**Given** a text file containing between 1 and 20 candidate IPv4 addresses,  
**When** the user starts a scan using that file,  
**Then** the application shall load and process the entries without exceeding the 20-entry limit.

### AC2 — Invalid addresses (R2)

**Given** an input file containing an invalid IPv4 address such as `192.168.1.999`,  
**When** the application validates the entries,  
**Then** it shall identify that entry as INVALID and shall not send a ping request to it.

### AC3 — Reachability status (R3)

**Given** a test address that responds to ping and a valid test address that does not respond within the timeout,  
**When** the application checks both addresses,  
**Then** it shall report the first as UP and the second as DOWN.

### AC4 — Response time (R4)

**Given** a test address that responds to ping,  
**When** the application completes the check,  
**Then** it shall display a numerical response time in milliseconds. For a nonresponding address, it shall show that the response time is unavailable.

### AC5 — Performance (R5)

**Given** a prepared list of 20 valid IPv4 addresses and documented test conditions,  
**When** the application scans the list three times,  
**Then** each scan shall finish within 5 seconds, with each run's duration recorded. If the target is not met, the result shall be documented and investigated rather than reported as a pass.

### AC6 — CSV export (R6)

**Given** a completed scan containing responding, nonresponding, and invalid entries,  
**When** the user requests an export,  
**Then** the application shall create a readable CSV file containing the required columns and representing all entries with their appropriate statuses.

### AC7 — Summary counts (R7)

**Given** a scan containing known valid and invalid entries,  
**When** the scan finishes,  
**Then** the displayed counts shall match the actual input, with the valid addresses divided correctly between UP and DOWN.

## 7. Out of Scope and Open Questions

### Out of scope

The following features are not part of the required project:

- Automatically discovering all devices connected to a network.
- Measuring Wi-Fi signal strength or creating a Wi-Fi coverage map.
- Continuous monitoring, historical dashboards, or alert notifications.
- Packet capture or detailed traffic analysis.
- Port scanning, vulnerability testing, or router configuration.
- A database, user accounts, or a cloud service.
- Monitoring devices or networks without authorization.

### Open questions

- Will a graphical user interface be practical after all required features and tests are complete? It will be treated as an optional enhancement, not a requirement.
- Which exact 20-address test list will be used to demonstrate the performance target? It will be selected and documented during implementation.
- Does the instructor require a specific Python version or any additional documentation format?

## AI Critique and Main Changes

An AI-assisted review of this specification identified several points that needed clarification:

1. **Bounded scope:** The project is limited to 20 candidate IPv4 addresses per scan, with a command-line interface as the required baseline.
2. **Measurable performance:** The five-second target now specifies 20 valid addresses, three test runs, and recording each duration under documented conditions.
3. **Meaning of DOWN:** The specification clarifies that DOWN means no ping reply was received before the timeout, rather than proving that a device is offline.
4. **Consistent testing:** Each numbered requirement has a corresponding Given / When / Then acceptance criterion.
5. **Optional GUI:** A graphical interface is an optional enhancement rather than a promised feature or a core acceptance requirement.
6. **Output details:** Input format, terminal output or GUI output, CSV columns, invalid-entry handling, and summary counts are defined explicitly.
