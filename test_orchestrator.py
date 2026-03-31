"""
Quick test script for the CSV Watcher and Orchestrator
"""

from pathlib import Path
from watchers.csv_watcher import CSVWatcher, CSVFileHandler
from orchestrator import HydrologyOrchestrator

vault_path = Path(__file__).parent / 'Hydrology-Vault'

print("=" * 60)
print("🧪 Testing CSV Watcher and Orchestrator")
print("=" * 60)

# Test 1: Check if watcher detects existing files
print("\n1. Testing CSV Watcher (existing file detection)...")
watcher = CSVWatcher(str(vault_path))
existing = watcher.check_existing_files()
print(f"   Found {len(existing)} CSV file(s) in Inbox:")
for f in existing:
    print(f"   - {f.name}")

# Test 2: Create action files for existing CSVs
print("\n2. Creating action files for existing CSVs...")
# Create handler directly for testing
handler = CSVFileHandler(str(vault_path))
for csv_file in existing:
    action_path = handler.create_action_file(csv_file)
    print(f"   Created: {action_path.name}")

# Test 3: Check Needs_Action folder
print("\n3. Checking Needs_Action folder...")
needs_action = vault_path / 'Needs_Action'
action_files = list(needs_action.glob('*.md'))
print(f"   Found {len(action_files)} action file(s):")
for f in action_files:
    print(f"   - {f.name}")

# Test 4: Run orchestrator (single iteration)
print("\n4. Testing Orchestrator (single task processing)...")
orchestrator = HydrologyOrchestrator(str(vault_path))
tasks = orchestrator.get_pending_tasks()
print(f"   Pending tasks: {len(tasks)}")

if tasks:
    for task in tasks:
        task_info = orchestrator.parse_action_file(task)
        print(f"   Processing: {task_info['action_path'].name}")
        success = orchestrator.process_task(task_info)
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        break  # Only process one task for testing
else:
    print("   No pending tasks")

# Test 5: Check Done folder
print("\n5. Checking Done folder...")
done_folder = vault_path / 'Done'
done_files = list(done_folder.glob('*.md'))
print(f"   Found {len(done_files)} file(s) in Done:")
for f in done_files:
    print(f"   - {f.name}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
