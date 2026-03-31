"""
Hydrology FTE Agent - Main Entry Point

Autonomous hydrology data processing agent powered by Qwen AI:
1. Detects CSV files in /Inbox (via Watcher)
2. Detects weather bulletins in /Weather_Inbox (via Weather Watcher)
3. Computes discharge from width, depth, velocity
4. Analyzes flow condition and risk
5. Generates reports in /Done
6. Sends flood alerts via email with human approval
7. Auto-posts to LinkedIn for marketing

AI Brain: Qwen (open-source, no API credits required)

SILVER TIER FEATURES:
- Multi-source data ingestion (CSV + Weather bulletins)
- Email alert system with human-in-the-loop approval
- LinkedIn auto-posting for professional updates
- Automated scheduling via Windows Task Scheduler
- AI reasoning plans for transparent decision-making

Usage:
    python main.py              # Run orchestrator (autonomous mode)
    python main.py --watcher    # Run all watchers (CSV, Weather, Gmail, Approval)
    python main.py --run        # Run single workflow (manual mode)
    python main.py --linkedin   # Generate and post to LinkedIn immediately
"""

import sys
import argparse
import threading
import io
import subprocess
from pathlib import Path

# Handle Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        # Reconfigure stdout to handle emojis
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def check_qwen_available():
    """
    Verify Qwen CLI is installed and working.
    Returns True if available, False otherwise.
    """
    try:
        # Try to find Qwen CLI path
        qwen_cli_path = None
        possible_paths = [
            r'C:\Users\zaina\AppData\Roaming\npm\node_modules\@qwen-code\qwen-code\cli.js',
        ]

        for path in possible_paths:
            if Path(path).exists():
                qwen_cli_path = path
                break

        if qwen_cli_path:
            result = subprocess.run(
                ['node', qwen_cli_path, '--version'],
                capture_output=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ['qwen', '--version'],
                capture_output=True,
                timeout=5
            )

        if result.returncode != 0:
            return False

        return True

    except Exception as e:
        print(f"\nHealth check error: {e}")
        return False


def print_qwen_not_available():
    """Print error message when Qwen is not available."""
    print("\n" + "="*60)
    print("❌ QWEN CLI NOT AVAILABLE")
    print("="*60)
    print("\nQwen CLI is required for this system to work.")
    print("There is NO fallback - Qwen MUST be installed.")
    print("\n📦 Install Qwen CLI:")
    print("   npm install -g @qwen-code/qwen-code")
    print("\n🔗 Or visit: https://github.com/QwenLM/Qwen")
    print("\n💡 After installation, verify:")
    print("   qwen --version")
    print("="*60)
    print("\n⚠️  System cannot start without Qwen CLI.")
    print("="*60)


def run_autonomous_mode():
    """Run the orchestrator in autonomous mode (24/7)."""
    # Check Qwen availability first
    print("\n🔍 Checking Qwen CLI availability...")
    if not check_qwen_available():
        print_qwen_not_available()
        sys.exit(1)
    print("✅ Qwen CLI is available\n")

    print("=" * 60)
    print("🌊 Hydrology FTE Agent - Autonomous Mode")
    print("=" * 60)
    print("Starting orchestrator and watchers...")
    print("Drop CSV files in Hydrology-Vault/Inbox to process")
    print("Drop weather bulletins in Hydrology-Vault/Weather_Inbox")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    from orchestrator import HydrologyOrchestrator
    vault_path = Path(__file__).parent / 'Hydrology-Vault'
    orchestrator = HydrologyOrchestrator(str(vault_path))
    orchestrator.run()


def run_watcher_mode():
    """Run CSV, Weather, Gmail, and Approval watchers simultaneously."""
    # Check Qwen availability first
    print("\n🔍 Checking Qwen CLI availability...")
    if not check_qwen_available():
        print_qwen_not_available()
        sys.exit(1)
    print("✅ Qwen CLI is available\n")

    print("=" * 60)
    print("🌊 Hydrology FTE Agent - Complete Watcher Mode")
    print("=" * 60)
    print("Monitoring Gmail inbox for emails with attachments...")
    print("Monitoring Hydrology-Vault/Inbox for CSV files...")
    print("Monitoring Hydrology-Vault/Weather_Inbox for weather bulletins...")
    print("Monitoring Hydrology-Vault/Needs_Action for approval decisions...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()  # Add blank line for readability

    from watchers.csv_watcher import CSVWatcher, CSVFileHandler
    from watchers.pdf_watcher import PDFWatcher, WeatherFileHandler
    from watchers.approval_watcher import ApprovalWatcher
    from watchers.gmail_watcher import GmailWatcher

    vault_path = Path(__file__).parent / 'Hydrology-Vault'

    # Initialize all watchers
    csv_watcher = CSVWatcher(str(vault_path))
    weather_watcher = PDFWatcher(str(vault_path))
    approval_watcher = ApprovalWatcher(str(vault_path))
    
    # Gmail watcher (with error handling if not configured)
    try:
        gmail_watcher = GmailWatcher(str(vault_path), check_interval=60)
        gmail_available = True
    except ValueError as e:
        print(f"⚠️  Gmail Watcher not available: {e}")
        print("   Email receiving disabled. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        gmail_available = False

    # Create handlers manually for initial file scan
    csv_handler = CSVFileHandler(str(vault_path))
    weather_handler = WeatherFileHandler(str(vault_path))

    # Check for existing files
    existing_csv = csv_watcher.check_existing_files()
    if existing_csv:
        print(f"📂 Found {len(existing_csv)} existing CSV file(s)")
        for csv_file in existing_csv:
            csv_handler.create_action_file(csv_file)

    existing_weather = weather_watcher.check_existing_files()
    if existing_weather:
        print(f"📂 Found {len(existing_weather)} existing weather bulletin file(s)")
        for file in existing_weather:
            content = weather_handler.read_file_contents(file)
            if content:
                rainfall_data = weather_handler.extract_rainfall_data(content)
                warnings = weather_handler.extract_warnings(content)
                weather_handler.create_action_file(file, content, rainfall_data, warnings)

    # Print startup summary
    print()
    print("=" * 60)
    print("✅ Watchers started successfully!")
    print("=" * 60)
    if gmail_available:
        print("📧 Gmail Watcher: Active (receiving emails)")
    else:
        print("📧 Gmail Watcher: Not configured")
    print("📂 CSV Watcher: Active (monitoring Inbox)")
    print("🌤️  Weather Watcher: Active (monitoring Weather_Inbox)")
    print("⚖️  Approval Watcher: Active (monitoring Needs_Action)")
    print("=" * 60)
    print()

    # Run watchers in separate threads
    threads = []
    
    if gmail_available:
        gmail_thread = threading.Thread(target=gmail_watcher.start, daemon=True)
        gmail_thread.start()
        threads.append(gmail_thread)
    
    csv_thread = threading.Thread(target=csv_watcher.start, daemon=True)
    weather_thread = threading.Thread(target=weather_watcher.start, daemon=True)
    approval_thread = threading.Thread(target=approval_watcher.start, daemon=True)

    csv_thread.start()
    weather_thread.start()
    approval_thread.start()

    threads.extend([csv_thread, weather_thread, approval_thread])

    # Keep main thread alive
    try:
        while all(t.is_alive() for t in threads):
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n\nStopping all watchers...")
        csv_watcher.stop()
        weather_watcher.stop()
        approval_watcher.stop()
        if gmail_available:
            # Gmail watcher doesn't have stop method, will stop when main thread exits
            pass
        print("✅ All watchers stopped.")


def run_manual_mode():
    """Run a single workflow manually (for testing)."""
    # Check Qwen availability first
    print("\n🔍 Checking Qwen CLI availability...")
    if not check_qwen_available():
        print_qwen_not_available()
        sys.exit(1)
    print("✅ Qwen CLI is available\n")

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
            result = run_skill(skill, file_path=state["file_path"])
            if result and result.get('success'):
                state["data"] = result.get('data')
            state["log"].append(skill)

        elif skill == "compute_discharge":
            result = run_skill(skill, df=state["data"])
            if result and result.get('success'):
                state["data"] = result.get('data')
            state["log"].append(skill)

        elif skill == "analyze_flow_condition":
            result = run_skill(skill, df=state["data"])
            if result and result.get('success'):
                state["results"] = result.get('results')
            state["log"].append(skill)

        elif skill == "generate_hydrology_report":
            run_skill(skill, results=state["results"], output_file="report.md")
            state["log"].append(skill)
            print("📄 Report generated → report.md")

        else:
            print("⚠ Unknown skill:", skill)
            break


def run_linkedin_mode():
    """Generate and post to LinkedIn immediately."""
    print("=" * 60)
    print("📝 LinkedIn Auto-Poster - Manual Trigger")
    print("=" * 60)

    from skills.post_linkedin import run

    result = run()

    if result['success']:
        print("\n🎉 LinkedIn posting complete!")
        print(f"   Reports used: {result['reports_used']}")
        print(f"   Check Hydrology-Vault/linkedin_log.txt for details")
    else:
        print("\n⚠️  LinkedIn posting failed or skipped")
        print(f"   Reason: {result['message']}")


def main():
    parser = argparse.ArgumentParser(
        description='Hydrology FTE Agent - Autonomous Data Processing'
    )
    parser.add_argument(
        '--watcher',
        action='store_true',
        help='Run CSV, Weather, Gmail, and Approval watchers'
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run single workflow in manual mode'
    )
    parser.add_argument(
        '--linkedin',
        action='store_true',
        help='Generate and post to LinkedIn immediately'
    )

    args = parser.parse_args()

    if args.watcher:
        run_watcher_mode()
    elif args.run:
        run_manual_mode()
    elif args.linkedin:
        run_linkedin_mode()
    else:
        run_autonomous_mode()


if __name__ == "__main__":
    main()
