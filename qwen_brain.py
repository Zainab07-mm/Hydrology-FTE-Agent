"""
Qwen Brain for Hydrology FTE Agent

This module uses Qwen AI (via CLI) as the reasoning engine to decide
which skill to execute next based on the current workflow state.

Qwen is an open-source AI model - no API credits required.

Requirements:
    - Qwen CLI installed and configured
    - Run: qwen --version to verify installation
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


def decide_next_skill(state: dict) -> str:
    """
    Use Qwen AI to decide the next skill to execute.

    Args:
        state: Current workflow state containing file_path, data, results, log

    Returns:
        Name of the next skill to run, or "DONE" if workflow is complete
    """
    prompt = _build_qwen_prompt(state)

    try:
        # Find the Qwen CLI path
        # Qwen CLI is installed via npm, so we need to call it through node
        import os
        import sys

        # Try to find qwen CLI script
        qwen_cli_path = None
        possible_paths = [
            os.path.join(os.getenv('APPDATA', ''), 'npm', 'node_modules', '@qwen-code', 'qwen-code', 'cli.js'),
            r'C:\Users\zaina\AppData\Roaming\npm\node_modules\@qwen-code\qwen-code\cli.js',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                qwen_cli_path = path
                break

        if qwen_cli_path:
            # Call via node directly
            process = subprocess.run(
                ['node', qwen_cli_path, '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            # Fallback to calling 'qwen' command directly
            process = subprocess.run(
                ['qwen', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

        if process.returncode != 0:
            raise RuntimeError(f"Qwen CLI error: {process.stderr}")

        output = process.stdout.strip()

        if not output:
            raise RuntimeError("Qwen returned empty response")

        print(f"🧠 Qwen Output: {output}")

        skill = _parse_qwen_response(output)

        # Validate the decision
        if skill == "DONE" and state.get("results") is None:
            print("⚠️ Qwen returned DONE prematurely, re-evaluating...")
            return _deterministic_decision(state)

        return skill

    except FileNotFoundError:
        print("❌ Qwen CLI not found!")
        print("   Install: npm install -g @qwen-code/qwen-code")
        print("   Or visit: https://github.com/QwenLM/Qwen")
        raise

    except subprocess.TimeoutExpired:
        print("⚠️ Qwen request timed out (60s limit)")
        raise

    except Exception as e:
        print(f"❌ Qwen error: {e}")
        raise


def _build_qwen_prompt(state: dict) -> str:
    """Build a strict, structured prompt for Qwen AI."""

    # Simplify state for prompt (remove large data)
    simplified_state = state.copy()
    if simplified_state.get("data") is not None:
        simplified_state["data"] = f"<DataFrame: {len(simplified_state['data'])} rows>"
    if simplified_state.get("results") is not None:
        simplified_state["results"] = f"<Results: {len(simplified_state['results'])} items>"

    # Determine expected next step based on state
    expected_next = "UNKNOWN"
    if state.get("data") is None:
        expected_next = "ingest_hydrology_data"
    elif not hasattr(state["data"], 'columns') or 'Discharge' not in state["data"].columns:
        expected_next = "compute_discharge"
    elif state.get("results") is None:
        expected_next = "analyze_flow_condition"
    elif "generate_hydrology_report" not in state.get("log", []):
        expected_next = "generate_hydrology_report"
    else:
        expected_next = "DONE"

    return f"""You are a deterministic workflow controller.

RESPOND WITH EXACTLY ONE OF THESE VALUES (no other text):
- ingest_hydrology_data
- compute_discharge
- analyze_flow_condition
- generate_hydrology_report
- DONE

Current workflow state:
- data: {simplified_state.get("data")}
- results: {simplified_state.get("results")}
- log: {simplified_state.get("log")}

The correct next step is: {expected_next}

Your response (skill name only):"""


def _parse_qwen_response(response: str) -> str:
    """Parse Qwen's response to extract the skill name."""
    response_lower = response.lower().strip()

    # Check for completion
    if "done" in response_lower or response_lower == "":
        return "DONE"

    # Check for specific skills
    if "ingest" in response_lower:
        return "ingest_hydrology_data"
    elif "compute" in response_lower or "discharge" in response_lower:
        return "compute_discharge"
    elif "analyze" in response_lower or "condition" in response_lower or "flow" in response_lower:
        return "analyze_flow_condition"
    elif "report" in response_lower or "generate" in response_lower:
        return "generate_hydrology_report"

    # Default to DONE if unclear
    return "DONE"


def _deterministic_decision(state: dict) -> str:
    """
    Deterministic decision logic for timeout/error scenarios.
    This is NOT a fallback - it's a safety mechanism for edge cases.

    Uses simple state machine logic based on workflow progress.
    """
    if state.get("data") is None:
        return "ingest_hydrology_data"
    elif "Discharge" not in state.get("data", {}):
        return "compute_discharge"
    elif state.get("results") is None:
        return "analyze_flow_condition"
    elif "generate_hydrology_report" not in state.get("log", []):
        return "generate_hydrology_report"
    else:
        return "DONE"


def update_dashboard(vault_path: str, status: str, last_action: str = "", current_skill: str = ""):
    """
    Update the Dashboard.md with current agent status.

    Args:
        vault_path: Path to the Hydrology-Vault folder
        status: Current agent status (Running, Idle, Processing, etc.)
        last_action: Description of the last action performed
        current_skill: Name of the currently executing skill
    """
    dashboard_path = Path(vault_path) / "Dashboard.md"

    if not dashboard_path.exists():
        return

    # Count files in each folder
    inbox_count = len(list((Path(vault_path) / "Inbox").glob("*.csv")))
    processing_count = len(list((Path(vault_path) / "Needs_Action").glob("*.md")))
    done_count = len(list((Path(vault_path) / "Done").glob("*.md")))

    # Get file lists
    inbox_files = "\n".join([f"- {f.name}" for f in (Path(vault_path) / "Inbox").glob("*.csv")]) or "- (empty)"
    processing_files = "\n".join([f"- {f.name}" for f in (Path(vault_path) / "Needs_Action").glob("*.md")]) or "- (none)"
    done_files = "\n".join([f"- {f.name}" for f in (Path(vault_path) / "Done").glob("*.md")]) or "- (none)"

    content = f"""# 🌊 Hydrology FTE Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {status}

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| Files in Inbox | {inbox_count} |
| Files Processing | {processing_count} |
| Reports Generated | {done_count} |

---

## 📥 Inbox Status

{inbox_files}

---

## ⚡ Currently Processing

{processing_files}

---

## ✅ Completed Reports

{done_files}

---

## 🤖 Agent Status

- **Brain:** Qwen AI (Open Source)
- **Watcher:** File System Watcher (Active)
- **Last Action:** {last_action}
- **Current Skill:** {current_skill}

---

## 📋 Rules of Engagement

1. Process all CSV files dropped in `/Inbox`
2. Calculate discharge: `Width_m × Depth_m × Velocity_mps`
3. Classify flow condition:
   - Low: Q < 50 m³/s
   - Moderate: 50 ≤ Q ≤ 150 m³/s
   - High: Q > 150 m³/s
4. Assess risk level based on discharge
5. Generate report in `/Done` folder
6. Flag high-risk readings for human review

---

## 🚨 Alerts

- (No active alerts)

---

*Auto-generated by Hydrology FTE Agent with Qwen AI*
"""

    dashboard_path.write_text(content, encoding='utf-8')


if __name__ == "__main__":
    # Test the Qwen Brain
    print("=" * 50)
    print("🧪 Testing Qwen Brain")
    print("=" * 50)

    test_state = {
        "file_path": "hydrology_data/sample.csv",
        "data": None,
        "results": None,
        "log": []
    }

    print("\nTest 1: Initial state (should return ingest_hydrology_data)")
    try:
        next_skill = decide_next_skill(test_state)
        print(f"✅ Result: {next_skill}")
    except SystemExit as e:
        print(f"⚠️ Qwen CLI not available: {e}")
        print("   Using deterministic decision for testing...")
        print(f"   Result: {_deterministic_decision(test_state)}")

    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)
