# 🌊 Hydrology FTE Agent

> **Autonomous AI-Powered Hydrology Data Processing System**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AI: Qwen](https://img.shields.io/badge/AI-Qwen-purple.svg)](https://github.com/QwenLM/Qwen)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](https://github.com/Zainab07-mm/Hydrology-FTE-Agent)

An autonomous agent that monitors for hydrology measurement data, computes river discharge, analyzes flow conditions and risk levels, and generates professional reports — all without human intervention.

Powered by **Qwen AI** (open-source, no API credits required).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🔍 Autonomous Monitoring** | Continuously watches for new CSV data files |
| **🧮 Automatic Computation** | Calculates discharge using Q = Width × Depth × Velocity |
| **📊 Risk Analysis** | Classifies flow conditions and assesses risk levels |
| **📄 Report Generation** | Creates professional markdown reports automatically |
| **🖥️ Real-Time Dashboard** | Live status tracking of all processing activities |
| **🛡️ Error Handling** | Comprehensive validation and graceful error recovery |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Zainab07-mm/Hydrology-FTE-Agent.git
cd Hydrology-FTE-Agent

# Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# Start the autonomous agent
python main.py
```

Drop CSV files into `Hydrology-Vault/Inbox/` and watch the agent process them automatically.

---

## 💻 How to Run (Quick Reference)

**Already have everything installed? Just run:**

```bash
# 1. Start the agent (runs 24/7)
python main.py

# 2. Drop CSV files in Hydrology-Vault/Inbox/
# 3. Check reports in Hydrology-Vault/Done/
```

**That's it!** The agent automatically:
- Detects new CSV files
- Processes them with Qwen AI
- Generates reports
- Updates the dashboard

Press `Ctrl+C` to stop the agent.

---

## 📋 Usage Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **Autonomous** | `python main.py` | Production (24/7 monitoring) |
| **Watcher Only** | `python main.py --watcher` | Create tasks without processing |
| **Manual Test** | `python main.py --run` | Test single workflow |

---

## 📖 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Hydrology FTE Agent                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Watcher    │ →  │  Orchestrator │ →  │   Skills     │  │
│  │  (Monitors)  │    │  (Decides)    │    │  (Executes)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↓                   ↓                   ↓           │
│  Inbox folder         Task queue        Processing pipeline │
└─────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

1. **File Detection** → CSV watcher detects new measurement data
2. **Task Creation** → Action file created in processing queue
3. **AI Decision (Qwen)** → Qwen AI determines next processing step
4. **Data Ingestion** → CSV data loaded and validated
5. **Discharge Calculation** → Q = Width × Depth × Velocity
6. **Risk Classification** → Flow condition and risk level assigned
7. **Report Generation** → Professional markdown report created
8. **Completion** → Files archived, dashboard updated

### Discharge Classification

| Discharge (Q) | Condition | Risk Level |
|---------------|-----------|------------|
| Q < 50 m³/s | Low | Low |
| 50 ≤ Q ≤ 150 m³/s | Moderate | Medium |
| Q > 150 m³/s | High | High |

---

## 📁 Project Structure

```
Hydrology-FTE-Agent/
├── main.py                     # Main entry point
├── orchestrator.py             # Workflow orchestration
├── qwen_brain.py               # AI reasoning engine (Qwen)
├── skill_runner.py             # Skill execution
├── requirements.txt            # Python dependencies
├── LICENSE                     # Proprietary license
├── SECURITY.md                 # Security policies
│
├── watchers/
│   └── csv_watcher.py          # File system monitoring
│
├── skills/
│   ├── ingest_hydrology_data.py    # Data ingestion
│   ├── compute_discharge.py        # Discharge calculation
│   ├── analyze_flow_condition.py   # Risk analysis
│   └── generate_hydrology_report.py # Report generation
│
├── Hydrology-Vault/
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Operating procedures
│   ├── Inbox/                  # Input folder (CSV files)
│   ├── Needs_Action/           # Processing queue
│   └── Done/                   # Completed reports
│
└── hydrology_data/
    └── sample.csv              # Sample measurement data
```

---

## 💻 Usage

### Mode 1: Autonomous Operation (Recommended)

```bash
python main.py
```

Runs 24/7, automatically processing any CSV files dropped in the Inbox folder.

### Mode 2: Watcher Only

```bash
python main.py --watcher
```

Runs only the file watcher, creating task files for external processing.

### Mode 3: Single Workflow (Testing)

```bash
python main.py --run
```

Processes a single file manually — useful for testing and debugging.

---

## 📊 Dashboard

The system includes a real-time dashboard (`Hydrology-Vault/Dashboard.md`) showing:

- 📥 Pending files in inbox
- ⚡ Currently processing tasks
- ✅ Completed reports
- 🤖 Agent status and activity log

---

## 📋 Sample Data

### Required CSV Format

Your CSV files **must** have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `River` | River name | Chenab |
| `Width_m` | Width in meters | 30 |
| `Depth_m` | Depth in meters | 2 |
| `Velocity_mps` | Velocity in meters/second | 1.5 |

### Example Input CSV

```csv
River,Width_m,Depth_m,Velocity_mps
Chenab,30,2,1.5
Indus,50,3,2
```

### Generated Report

```markdown
# 🌊 Hydrology Report

*Generated by Hydrology FTE Agent*

**Report Generated:** 2026-03-28 19:10:47

---

## River: Chenab

### Discharge Calculation

**Formula:** Q = Width × Depth × Velocity

**Calculation:** Q = 30m × 2m × 1.5m/s = **90.0 m³/s**

### Analysis

- **Condition:** Moderate
- **Risk Level:** Medium

### What This Means

The river is flowing at a moderate rate with a discharge of 90.0 m³/s. This represents normal flow conditions, suitable for typical river operations and ecosystem health.

---

## River: Indus

### Discharge Calculation

**Formula:** Q = Width × Depth × Velocity

**Calculation:** Q = 50m × 3m × 2.0m/s = **300.0 m³/s**

### Analysis

- **Condition:** High
- **Risk Level:** High

### What This Means

The river is experiencing high flow conditions with a discharge of 300.0 m³/s. This elevated flow may indicate recent rainfall, snowmelt, or upstream releases, requiring increased monitoring.

---

*Report complete.*
```

---

## 🧪 Testing

```bash
# Run test suite
python test_bronze.py

# Test with sample data
copy hydrology_data\sample.csv Hydrology-Vault\Inbox\
```

---

## 🔧 Configuration

### AI Reasoning Engine (Qwen)

The system uses **Qwen AI** as the reasoning engine for autonomous decision-making. Qwen is open-source and requires no API credits.

**Install Qwen CLI:**

```bash
pip install qwen-cli
```

Or visit: https://github.com/QwenLM/Qwen

**Verify installation:**
```bash
qwen --version
```

### Customization

- **Check interval**: Edit `watchers/csv_watcher.py` (default: 5 seconds)
- **Monitored folder**: Configure in `orchestrator.py`
- **Classification thresholds**: Modify in `skills/analyze_flow_condition.py`

---

## 🛡️ Security

- **Local processing only** — No external API calls required
- **Open-source AI** — Qwen AI runs locally, no cloud dependencies
- **User data protected** — CSV files excluded from version control
- **Input validation** — All data validated before processing
- **Error handling** — Comprehensive exception handling throughout

See [SECURITY.md](SECURITY.md) for details.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Zainab07-mm/Hydrology-FTE-Agent/issues)
- **Email**: zainabmukhtar2277@gmail.com
- **Qwen AI**: https://github.com/QwenLM/Qwen

---

*Hydrology FTE Agent — Autonomous Intelligence for Hydrology Data Processing*
*Powered by Qwen AI (Open Source)*
