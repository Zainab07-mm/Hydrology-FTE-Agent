"""
Live demo of the Hydrology FTE Agent
Shows the agent working in real-time
"""

import time
import shutil
from pathlib import Path
from watchers.csv_watcher import CSVWatcher, CSVFileHandler
from orchestrator import HydrologyOrchestrator

vault_path = Path(__file__).parent / 'Hydrology-Vault'
inbox = vault_path / 'Inbox'
needs_action = vault_path / 'Needs_Action'
done = vault_path / 'Done'

# Clean up previous test files
print("🧹 Cleaning up previous test files...")
for f in inbox.glob('*'):
    if f.is_file():
        f.unlink()
for f in needs_action.glob('*'):
    f.unlink()
print("   Inbox and Needs_Action cleared\n")

# Create a fresh test CSV
test_csv = inbox / 'live_test.csv'
test_csv.write_text('River,Width_m,Depth_m,Velocity_mps\nChenab,30,2,1.5\nIndus,50,3,2\n')
print(f"📄 Created test file: {test_csv.name}\n")

# Start watcher to detect the file
print("👁️  Starting CSV Watcher...")
handler = CSVFileHandler(str(vault_path))
handler.create_action_file(test_csv)
print(f"   Action file created in Needs_Action/\n")

# Check action files
action_files = list(needs_action.glob('*.md'))
print(f"📋 Action files in Needs_Action/:")
for f in action_files:
    print(f"   - {f.name}")
print()

# Run orchestrator
print("🤖 Starting Orchestrator...")
orchestrator = HydrologyOrchestrator(str(vault_path))
tasks = orchestrator.get_pending_tasks()

if tasks:
    for task in tasks:
        task_info = orchestrator.parse_action_file(task)
        print(f"\n⚙️  Processing: {task_info['action_path'].name}")
        print("-" * 50)
        success = orchestrator.process_task(task_info)
        print("-" * 50)
        print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\n")
else:
    print("   No tasks found!")

# Show results
print("\n" + "=" * 60)
print("📊 FINAL RESULTS")
print("=" * 60)

print(f"\n✅ Reports in Done/:")
reports = list(done.glob('report_*.md'))
for r in reports:
    print(f"   - {r.name}")

print(f"\n✅ Completed action files:")
completed = list(done.glob('completed_*.md'))
for c in completed:
    print(f"   - {c.name}")

# Show latest report content
if reports:
    latest_report = max(reports, key=lambda x: x.stat().st_mtime)
    print(f"\n📄 Latest Report Content ({latest_report.name}):")
    print("-" * 50)
    print(latest_report.read_text())
    print("-" * 50)

print("\n✅ Demo Complete! The Hydrology FTE Agent is working!")
