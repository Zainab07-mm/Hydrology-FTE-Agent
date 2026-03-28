"""
Hydrology FTE Agent - Main Entry Point

Autonomous hydrology data processing agent powered by Qwen AI:
1. Detects CSV files in /Inbox (via Watcher)
2. Computes discharge from width, depth, velocity
3. Analyzes flow condition and risk
4. Generates reports in /Done

AI Brain: Qwen (open-source, no API credits required)

Usage:
    python main.py              # Run orchestrator (autonomous mode)
    python main.py --watcher    # Run only the CSV watcher
    python main.py --run        # Run single workflow (manual mode)
"""

import sys
import argparse
from pathlib import Path


def run_autonomous_mode():
    """Run the orchestrator in autonomous mode (24/7)."""
    print("=" * 60)
    print("🌊 Hydrology FTE Agent - Autonomous Mode")
    print("=" * 60)
    print("Starting orchestrator and watcher...")
    print("Drop CSV files in Hydrology-Vault/Inbox to process")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    from orchestrator import HydrologyOrchestrator
    vault_path = Path(__file__).parent / 'Hydrology-Vault'
    orchestrator = HydrologyOrchestrator(str(vault_path))
    orchestrator.run()


def run_watcher_mode():
    """Run only the CSV watcher (triggers action files)."""
    print("=" * 60)
    print("🌊 Hydrology FTE Agent - Watcher Mode")
    print("=" * 60)
    print("Monitoring Hydrology-Vault/Inbox for CSV files...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    from watchers.csv_watcher import CSVWatcher
    vault_path = Path(__file__).parent / 'Hydrology-Vault'
    watcher = CSVWatcher(str(vault_path))
    
    # Check for existing files
    existing = watcher.check_existing_files()
    if existing:
        print(f"Found {len(existing)} existing CSV file(s)")
        for csv_file in existing:
            watcher.handler.create_action_file(csv_file)
    
    watcher.start()


def run_manual_mode():
    """Run a single workflow manually (for testing)."""
    from skill_runner import run_skill
    from qwen_brain import decide_next_skill

    state = {
        "file_path": "hydrology_data/sample.csv",
        "data": None,
        "results": None,
        "log": []
    }

    print("🚀 Hydrology Autonomous FTE Started (Powered by Qwen AI)\n")
    
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        skill = decide_next_skill(state)
        print(f"🧠 Qwen selected: {skill}")

        if skill == "DONE":
            print("\n✅ Workflow completed")
            break
        
        if skill == "ingest_hydrology_data":
            state["data"] = run_skill(skill, file_path=state["file_path"])
            state["log"].append(skill)
            
        elif skill == "compute_discharge":
            state["data"] = run_skill(skill, df=state["data"])
            state["log"].append(skill)
            
        elif skill == "analyze_flow_condition":
            state["results"] = run_skill(skill, df=state["data"])
            state["log"].append(skill)
            
        elif skill == "generate_hydrology_report":
            run_skill(skill, results=state["results"], output_file="report.md")
            state["log"].append(skill)
            print("📄 Report generated → report.md")
            
        else:
            print("⚠ Unknown skill:", skill)
            break


def main():
    parser = argparse.ArgumentParser(
        description='Hydrology FTE Agent - Autonomous Data Processing'
    )
    parser.add_argument(
        '--watcher',
        action='store_true',
        help='Run only the CSV watcher'
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run single workflow in manual mode'
    )
    
    args = parser.parse_args()
    
    if args.watcher:
        run_watcher_mode()
    elif args.run:
        run_manual_mode()
    else:
        run_autonomous_mode()


if __name__ == "__main__":
    main()
