# HydroWatch Pro: System Architecture

> A prototype pipeline that turns river measurement files into discharge values, flow classifications and reports. Tested on sample data only.

---

## Table of Contents

1. [Project Requirements](#project-requirements)
2. [Design Choices](#design-choices)
3. [Component Overview](#component-overview)
4. [Data Flow](#data-flow)
5. [Human Approval Workflow](#human-approval-workflow)
6. [Email Module](#email-module)
7. [Notes and Limitations](#notes-and-limitations)
8. [Possible Improvements](#possible-improvements)

---

## Project Requirements

This project was built for the Personal AI Employee Hackathon (2026). The hackathon describes tiers of increasing scope. This project targeted the Bronze and Silver tiers.

### Bronze tier: foundation

- Obsidian-style vault with `Dashboard.md` and a handbook file
- One watcher script (file system monitoring)
- Qwen CLI reading from and writing to the vault
- Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- AI functionality implemented as skills (small Python modules)

### Silver tier: functional assistant

All Bronze requirements plus:

- Two or more watcher scripts (CSV, weather text files, approval files, Gmail)
- A reasoning step that writes `Plan.md` files
- One email module for an external action (Gmail SMTP)
- A human approval step before sensitive actions
- Scheduling through Windows Task Scheduler

**What has been tested:** the CSV workflow (data in, discharge and classification out, report written) has been run on sample files. The Gmail alert and LinkedIn code is written but has not been connected to live accounts or tested end to end.

**AI component:** Qwen Code CLI. There is no fallback model.

---

## Design Choices

| Goal | Reason | How it is handled |
|------|--------|-------------------|
| Transparent | Hydrology reports should show their calculations | Formula-based skills; reports print the formula and the numbers |
| Safe | Alerts should not go out without a person checking them | Human approval step before any email is sent |
| Extensible | New data sources should be easy to add | Separate watchers and skills |
| Low cost | Single-developer project | Python, pandas and a command-line AI tool; no paid cloud services |

### Alternatives that were not used

- **Microservices:** too much overhead for a single-developer prototype.
- **Serverless functions:** adds vendor-specific setup and per-use costs.
- **One large script:** harder to test and extend.

### Chosen approach

A modular orchestrator pattern: Watchers, then Orchestrator, then Skills, then Outputs. Each part can be tested on its own, and new watchers or skills can be added without changing the others.

---

## Component Overview

### 1. Watchers (input)

**Purpose:** detect new files and create action requests.

| Watcher | Monitors | Creates |
|---------|----------|---------|
| `csv_watcher.py` | `Hydrology-Vault/Inbox/*.csv` | `HYDROLOGY_*.md` action files |
| `pdf_watcher.py` | `Hydrology-Vault/Weather_Inbox/*.txt` | `WEATHER_*.md` action files |
| `gmail_watcher.py` | Gmail inbox (attachments) | Downloads CSV files into `Inbox/` |
| `approval_watcher.py` | `Hydrology-Vault/Needs_Action/APPROVAL_*.md` | Reads human YES/NO decisions |

Different file types need different parsers, and approval files need their own logic, so each has its own watcher.

Simplified sketch of the idea (not the exact code):

```python
class CSVWatcher:
    def __init__(self, vault_path):
        self.inbox = Path(vault_path) / 'Inbox'
        self.needs_action = Path(vault_path) / 'Needs_Action'

    def start(self):
        """Keep checking the inbox for new CSV files."""
        while True:
            for csv_file in self.inbox.glob('*.csv'):
                self.create_action_file(csv_file)
            time.sleep(10)
```

---

### 2. Orchestrator (workflow manager)

**Purpose:** manage the steps for each task.

1. Read action files from `Needs_Action/`
2. Set up the workflow state
3. Ask the Qwen model which skill should run next
4. Run the skills in order
5. Move finished tasks to `Done/`

Watchers only detect files. The orchestrator handles the processing, so either can be changed without touching the other.

Workflow states:

```
Pending, Planning, Ingesting, Computing, Analyzing,
Alerting, Reporting, Done
```

---

### 3. Qwen model (decision and writing)

**Purpose:** choose the next skill from the current state, and write the plain-language parts of reports and plans.

Simplified sketch of the prompt pattern:

```python
def decide_next_skill(state):
    prompt = f"""
    Current state: {state}

    Available skills:
    - ingest_hydrology_data
    - compute_discharge
    - analyze_flow_condition
    - send_alert_email
    - generate_hydrology_report
    - create_plan

    Which skill should run next? Return only the skill name.
    """
    return call_qwen(prompt)
```

**Reasoning plans:** before processing, the `create_plan` skill asks Qwen to write a `Plan_*.md` file. It records the planned analysis steps so a person can review them.

The discharge and risk calculations are ordinary Python code. Qwen decides the order of steps and writes text. It does not do the calculations.

---

### 4. Skills (action executors)

| Skill | Input | Output |
|-------|-------|--------|
| `ingest_hydrology_data` | File path | DataFrame |
| `compute_discharge` | DataFrame | DataFrame with a discharge column |
| `analyze_flow_condition` | DataFrame with discharge | Low / moderate / high classification |
| `create_plan` | Data preview | Markdown plan |
| `generate_hydrology_report` | Results | Markdown report |
| `send_alert_email` | Results and risk | Approval request (email only after approval) |
| `post_linkedin` | Recent reports | LinkedIn post draft (saved and copied to clipboard) |

Each skill has a clear input and output, so it can be tested on its own and reused.

---

### 5. Email module

| Module | External service | Function |
|--------|------------------|----------|
| `mcp_email_server.py` | Gmail SMTP | `send_email()` |

Skills call `send_email()` instead of handling SMTP details themselves. If the email provider changes, only this module needs to change. See [Email Module](#email-module).

---

### 6. Dashboard

A markdown file at `Hydrology-Vault/Dashboard.md`, updated by the agent and by `update_dashboard.ps1`. It shows status, files in the inbox, files being processed, completed reports and the classification rules.

---

## Data Flow

### From CSV to report

All file names and values below are examples.

```
STEP 1: A CSV file is dropped into Hydrology-Vault/Inbox/

STEP 2: The CSV watcher detects the file
        Creates HYDROLOGY_<name>_<timestamp>.md in Needs_Action/

STEP 3: The orchestrator picks up the task
        Reads the action file and sets up the workflow state

STEP 4: A reasoning plan is created
        create_plan asks Qwen for a Plan_<name>_<timestamp>.md file

STEP 5: Skills run in order
        1. ingest_hydrology_data   file path -> DataFrame
        2. compute_discharge       Q = Width x Depth x Velocity
        3. analyze_flow_condition  low / moderate / high
        4. send_alert_email        for high flow, creates an
                                   APPROVAL_<river>_<timestamp>.md
                                   file and waits for a YES or NO
        5. generate_hydrology_report
                                   report_<name>_<timestamp>.md in Done/

STEP 6: The task is complete
        The action file moves to Done/ and the dashboard is updated
```

---

## Human Approval Workflow

### Why

An alert email sent in error could cause confusion. The email step therefore waits for a person to approve it.

### How it works

```
High flow detected (Q above 150 m3/s)
    |
    v
Create APPROVAL_*.md in Needs_Action/
    The file shows: river, discharge, risk level,
    email preview, and a DECISION line
    |
    v
Approval watcher reads the DECISION line
    |
    +-- YES: send the email via Gmail SMTP,
    |        log it, move the file to Done/
    |
    +-- NO:  cancel the email, log it,
             move the file to Done/
```

### Example approval file (sample values)

```markdown
# Flood Alert Approval Request

**River:** Chenab
**Discharge:** 185.5 m3/s
**Risk Level:** HIGH
**Date:** 2026-03-31 08:15:30

---

## Email Preview

**To:** client@example.com
**Subject:** FLOOD ALERT - Chenab - 2026-03-31

**Body:**
A high flow condition has been flagged on the Chenab River.

Discharge: 185.5 m3/s
Threshold: 150.0 m3/s

---

## Decision

**Type YES or NO below:**

DECISION: [type YES or NO here]
```

The 150 m3/s threshold is a demonstration value used for every river. It is not an official flood-stage limit.

---

## Email Module

`mcp_email_server.py` wraps Gmail SMTP behind a `send_email()` function. MCP (Model Context Protocol) is a standard way for AI tools to call external services. Here the idea is used to keep external calls separate from the skills.

Without the wrapper, every skill would handle SMTP itself:

```python
def send_email(to, subject, body):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(email, password)
    # ... more SMTP handling ...
```

With the wrapper, a skill only makes the call:

```python
from mcp_email_server import send_email

result = send_email(to=to, subject=subject, body=body)
```

Simplified sketch of the module:

```python
import os
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, body):
    """Send email via Gmail SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv('GMAIL_ADDRESS')
    msg['To'] = to

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.getenv('GMAIL_ADDRESS'),
                     os.getenv('GMAIL_APP_PASSWORD'))
        server.send_message(msg)
```

Gmail needs an App Password, and 2-step verification must be enabled on the account first. This module has not been tested against a live Gmail account.

---

## Notes and Limitations

- Discharge is width x depth x velocity, which treats the channel as a rectangle.
- Risk thresholds are fixed and the same for every river (low below 50 m3/s, moderate 50 to 150, high above 150). They are demonstration values.
- Inputs are one width, depth and velocity value per river, with no time series or gauge calibration.
- All results come from sample data. Nothing has been validated against observed records.
- Qwen can return unexpected formats, so its output should be reviewed.
- The email and LinkedIn parts are written but not tested against live accounts.
- The project runs on Windows only because it uses Windows Task Scheduler.
- The project was developed with an AI coding assistant (Qwen Code CLI).

---

## Possible Improvements

1. **Tests first.** Add unit tests for each skill and mock external services.
2. **A database.** Use SQLite for task state instead of parsing markdown files.
3. **Configuration checks.** Validate `.env` values at startup and give clear errors for missing ones.
4. **Better hydrology.** Use cross-section geometry, per-river thresholds from published flood stages, and validation against gauge data.
5. **Web dashboard.** Charts of discharge over time and downloadable reports.

---

*Documented by Zainab Mukhtar (March 2026, revised October 2026)*
