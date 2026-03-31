# 🏗️ HydroWatch Pro — System Architecture

> **Silver Tier: Functional Assistant for Hydrology Monitoring**

---

## Table of Contents

1. [Project Requirements](#project-requirements)
2. [Why This Architecture](#why-this-architecture)
3. [Component Overview](#component-overview)
4. [Data Flow](#data-flow)
5. [MCP Server Pattern](#mcp-server-pattern)
6. [Lessons Learned](#lessons-learned)

---

## Project Requirements

### 🥉 Bronze Tier: Foundation (Minimum Viable Deliverable)

**Estimated time: 8-12 hours**

- ✅ Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- ✅ One working Watcher script (file system monitoring)
- ✅ Qwen CLI successfully reading from and writing to the vault
- ✅ Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- ✅ All AI functionality implemented as Agent Skills

### 🥈 Silver Tier: Functional Assistant

**Estimated time: 20-30 hours**

**All Bronze requirements plus:**

- ✅ Two or more Watcher scripts (CSV + Weather + Approval + Gmail)
- ✅ Qwen reasoning loop that creates `Plan.md` files
- ✅ One working MCP server for external action (Email via Gmail SMTP)
- ✅ Human-in-the-loop approval workflow for sensitive actions
- ✅ Basic scheduling via Windows Task Scheduler
- ✅ All AI functionality implemented as Agent Skills

**AI Brain: Qwen CLI** (no fallback, no Claude)

---

## Why This Architecture

### Design Goals

| Goal | Why It Mattered | How We Achieved It |
|------|-----------------|-------------------|
| **Autonomous** | Must run 24/7 without human intervention | Watchers + Orchestrator + Qwen AI |
| **Transparent** | Hydrology reports must show calculations | Formula-based skills with plain English |
| **Safe** | Flood alerts need human verification | Human-in-the-loop approval workflow |
| **Extensible** | New data sources should be easy to add | Modular skill-based architecture |
| **Affordable** | Target users are small consulting firms | Free/open-source stack, no cloud costs |

### Why Not Other Approaches?

**❌ Microservices:**
- Too complex for a single-developer project
- Network overhead would slow down time-critical flood alerts
- Debugging distributed systems is harder

**❌ Serverless (AWS Lambda):**
- Cold starts would delay flood detection
- Vendor lock-in concerns
- Costs scale with usage (unpredictable)

**❌ Monolithic Script:**
- Hard to test individual components
- No separation of concerns
- Difficult to extend with new features

**✅ Chosen: Modular Orchestrator Pattern**
- Clear separation: Watchers → Orchestrator → Skills → Outputs
- Each component is independently testable
- Easy to add new watchers or skills
- Runs locally with zero cloud costs

---

## Component Overview

### 1. Watchers (Event-Driven Input)

**Purpose:** Detect new data files and create action requests.

| Watcher | Monitors | Triggers |
|---------|----------|----------|
| `csv_watcher.py` | `Hydrology-Vault/Inbox/*.csv` | `HYDROLOGY_*.md` action files |
| `pdf_watcher.py` | `Hydrology-Vault/Weather_Inbox/*.txt` | `WEATHER_*.md` action files |
| `gmail_watcher.py` | Gmail inbox (with attachments) | Downloads CSV → saves to `Inbox/` |
| `approval_watcher.py` | `Hydrology-Vault/Needs_Action/APPROVAL_*.md` | Processes human YES/NO decisions |

**Why Separate Watchers?**
- Different file formats need different parsers
- Weather data has different structure than hydrology data
- Approval files require human-in-the-loop logic
- Email receiving is separate from file processing

**Design Pattern: Observer Pattern**
```python
class CSVWatcher:
    def __init__(self, vault_path):
        self.inbox = Path(vault_path) / 'Inbox'
        self.needs_action = Path(vault_path) / 'Needs_Action'

    def start(self):
        """Run forever, watching for new CSV files."""
        while True:
            csv_files = list(self.inbox.glob('*.csv'))
            for csv_file in csv_files:
                self.create_action_file(csv_file)
            time.sleep(10)  # Check every 10 seconds
```

---

### 2. Orchestrator (Workflow Manager)

**Purpose:** Manage the end-to-end workflow for each task.

**Responsibilities:**
1. Parse action files from `Needs_Action/`
2. Initialize workflow state
3. Call Qwen AI to decide next skill
4. Execute skills in order
5. Handle task completion (move to `Done/`)

**Why a Separate Orchestrator?**
- Watchers should only detect files, not process them
- Processing logic is complex and needs state management
- Orchestrator can be swapped without changing watchers

**State Machine:**
```
Pending → Planning → Ingesting → Computing → Analyzing →
Alerting → Reporting → Done
```

---

### 3. Qwen AI Brain (Decision Maker)

**Purpose:** Decide which skill to run next based on current state.

**Why Qwen (not Claude)?**
- Free and open-source
- No API costs for unlimited calls
- Runs locally (no network latency)
- No fallback needed—Qwen is the only AI

**Prompt Pattern:**
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

**Reasoning Plans:**
- Before processing, Qwen creates a `Plan_*.md` file
- This file contains the AI's reasoning and analysis steps
- Provides transparency for human review
- Stored in `Needs_Action/` for audit trail

---

### 4. Skills (Action Executors)

**Purpose:** Execute specific tasks with clear inputs and outputs.

| Skill | Input | Output |
|-------|-------|--------|
| `ingest_hydrology_data` | File path | DataFrame |
| `compute_discharge` | DataFrame | DataFrame + Q column |
| `analyze_flow_condition` | DataFrame + Q | Risk classification |
| `create_plan` | Data preview | Markdown reasoning plan |
| `generate_hydrology_report` | Results | Markdown report |
| `send_alert_email` | Results + Risk | Approval request |
| `post_linkedin` | Report | LinkedIn post (clipboard) |

**Why Skills Pattern?**
- Each skill is independently testable
- Skills can be reused across workflows
- Easy to add new skills without changing orchestrator
- Clear contract: input → output

---

### 5. MCP Servers (API Integrations)

**Purpose:** Provide unified interface to external services.

| MCP Server | External Service | Functions |
|------------|------------------|-----------|
| `mcp_email_server.py` | Gmail SMTP | `send_email()` |

**Why MCP Pattern?**
- Skills call `mcp_email_server.send_email()` not raw SMTP
- API changes only affect MCP server, not skills
- Consistent interface across all external services
- Easy to mock for testing

---

### 6. Dashboard (System Monitoring)

**Purpose:** Display current system status in Obsidian vault.

**Updates Every 10 Seconds:**
- Current status (Idle / Processing / Alerting)
- Last processed file
- Today's statistics (reports generated, alerts sent)
- System health indicators

**Location:** `Hydrology-Vault/Dashboard.md`

---

## Data Flow

### Complete Journey: CSV to Report

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: CSV File Dropped in Inbox                               │
│ User copies hydrology_data.csv to Hydrology-Vault/Inbox/        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: CSV Watcher Detects File                                │
│ csv_watcher.py scans Inbox/ every 10 seconds                    │
│ Creates: HYDROLOGY_hydrology_data_20260331_081500.md            │
│ Location: Hydrology-Vault/Needs_Action/                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Orchestrator Picks Up Task                              │
│ Reads action file, extracts source_path                         │
│ Initializes state: {"file_path": "...", "data": None, ...}      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Qwen AI Creates Reasoning Plan                          │
│ create_plan skill calls Qwen with data preview                  │
│ Qwen returns: Plan_Chenab_20260331_081500.md                    │
│ Plan includes: risk assessment, analysis steps, decision rules  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Qwen AI Executes Skills (via Orchestrator)              │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Skill 1: ingest_hydrology_data                          │    │
│ │   Input: file_path                                      │    │
│ │   Output: DataFrame with 4 rivers                       │    │
│ └─────────────────────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Skill 2: compute_discharge                              │    │
│ │   Input: DataFrame                                      │    │
│ │   Output: DataFrame + Discharge column                  │    │
│ │   Formula: Q = Width × Depth × Velocity                 │    │
│ └─────────────────────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Skill 3: analyze_flow_condition                         │    │
│ │   Input: DataFrame + Discharge                          │    │
│ │   Output: Risk classification (LOW/MEDIUM/HIGH)         │    │
│ └─────────────────────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Skill 4: send_alert_email                               │    │
│ │   Input: Results with risk levels                       │    │
│ │   Output: Approval requests for HIGH risk rivers        │    │
│ │   Creates: APPROVAL_Chenab_20260331_081530.md           │    │
│ │   Waits for human YES/NO decision                       │    │
│ └─────────────────────────────────────────────────────────┘    │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Skill 5: generate_hydrology_report                      │    │
│ │   Input: Results + DataFrame                            │    │
│ │   Output: report_Chenab_20260331_081600.md              │    │
│ │   Location: Hydrology-Vault/Done/                       │    │
│ └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Task Complete                                           │
│ Action file moved to: Done/completed_HYDROLOGY_*.md             │
│ Dashboard updated with new report count                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Human-in-the-Loop Approval

### How It Works

**Problem:** Flood alerts can cause panic if sent incorrectly.

**Solution:** Require human approval before sending any alert email.

### Approval Workflow

```
HIGH RISK Detected (Q > 150 m³/s)
    │
    ▼
Create APPROVAL_*.md in Needs_Action/
    │
    ▼
File Contains:
- River name and discharge value
- Risk level classification
- Email preview (subject + body)
- DECISION: [type YES or NO here]
    │
    ▼
Approval Watcher Detects Change (every 10 seconds)
    │
    ├─► DECISION: YES ──► Send email via Gmail SMTP
    │                      Log to email_log.txt
    │                      Move approval file to Done/
    │
    └─► DECISION: NO ────► Cancel email
                           Log cancellation
                           Move approval file to Done/
```

### Example Approval File

```markdown
# Flood Alert Approval Request

**River:** Chenab
**Discharge:** 185.5 m³/s
**Risk Level:** HIGH
**Date:** 2026-03-31 08:15:30

---

## Email Preview

**To:** client@example.com
**Subject:** FLOOD ALERT - Chenab - 2026-03-31

**Body:**
A HIGH RISK flood condition has been detected on the Chenab River.

Discharge: 185.5 m³/s
Threshold: 150.0 m³/s

Immediate action recommended.

---

## Decision

**Type YES or NO below:**

DECISION: [type YES or NO here]
```

---

## MCP Server Pattern

### What Is MCP?

**MCP = Model Context Protocol**

A standardized way for AI agents to interact with external services.

### Why MCP?

**Without MCP:**
```python
# Every skill needs to know SMTP details
def send_email(to, subject, body):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(email, password)
    # ... 30 lines of SMTP handling ...
```

**With MCP:**
```python
# Skill only cares about the action
from mcp_email_server import send_email

result = send_email(to=to, subject=subject, body=body)
# Done!
```

### MCP Email Server

```python
# mcp_email_server.py

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

    return {'success': True, 'message_id': '...'}
```

---

## Lessons Learned

### What Worked Well

1. **Modular Skills Pattern**
   - Each skill is independently testable
   - Easy to add new skills without breaking existing ones
   - Clear input/output contracts

2. **Human-in-the-Loop Approval**
   - Critical for flood alerts (can't have false positives)
   - Simple YES/NO decision in markdown file
   - Approval watcher processes decisions automatically

3. **Qwen AI Reasoning Plans**
   - Transparency: can see exactly what AI was thinking
   - Debugging: easier to understand AI decisions
   - Audit trail: plans stored for future review

4. **Watcher Architecture**
   - File system monitoring with Watchdog library
   - Event-driven triggers for real-time processing
   - Multiple watchers can run simultaneously

### What Was Harder Than Expected

1. **Qwen AI Reliability**
   - Qwen sometimes returns unexpected formats
   - Had to add extensive fallback handling
   - Prompt engineering is a skill unto itself

2. **Windows Task Scheduler**
   - Different behavior than cron on Linux
   - Had to use batch files as intermediaries
   - Permission issues required "Run as Administrator"

3. **Gmail SMTP Setup**
   - Requires App Password (not regular password)
   - 2FA must be enabled first
   - Rate limits for free accounts

### What I Would Do Differently

1. **Start with Testing**
   - Write tests before implementing features
   - Mock external services for unit tests
   - Integration tests for full workflows

2. **Use a Database**
   - SQLite for task state tracking
   - Better than parsing markdown files
   - Easier to query for reports

3. **Add Configuration Validation**
   - Check .env variables at startup
   - Provide clear error messages for missing config
   - Auto-generate .env from .env.example

4. **Build a Web Dashboard**
   - Real-time monitoring from anywhere
   - Visual charts for discharge trends
   - Client portal for viewing reports

---

## Summary

HydroWatch Pro's architecture is the result of iterative design decisions driven by real-world requirements:

- **Autonomous operation** → Watchers + Orchestrator + Qwen AI
- **Transparent decisions** → Reasoning plans stored as markdown
- **Safe alerts** → Human-in-the-loop approval workflow
- **Email integration** → Gmail SMTP via MCP server
- **Real-time monitoring** → Dashboard updates every 10 seconds

Each component serves a specific purpose, and the modular design allows for easy extension as requirements evolve.

---

*Architecture documented by Zainab Mukhtar — March 2026*
