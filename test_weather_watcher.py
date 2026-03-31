"""
Test script for Weather Watcher (PDF/TXT Watcher)

This script tests the weather watcher functionality:
1. Creates the Weather_Inbox folder
2. Processes the sample rainfall bulletin
3. Verifies the task file is created
"""

import time
import threading
from pathlib import Path

# Import watchers
from watchers.csv_watcher import CSVWatcher
from watchers.pdf_watcher import PDFWatcher

def test_dual_watchers():
    """Test both watchers running simultaneously."""
    print("=" * 60)
    print("🧪 Testing Dual Watcher System")
    print("=" * 60)
    
    vault_path = Path(__file__).parent / 'Hydrology-Vault'
    
    # Initialize both watchers
    csv_watcher = CSVWatcher(str(vault_path))
    weather_watcher = PDFWatcher(str(vault_path))
    
    # Initialize handlers manually (without starting the observer)
    from watchers.csv_watcher import CSVFileHandler
    from watchers.pdf_watcher import WeatherFileHandler
    
    csv_handler = CSVFileHandler(str(vault_path))
    weather_handler = WeatherFileHandler(str(vault_path))
    
    # Ensure directories exist
    (vault_path / 'Inbox').mkdir(exist_ok=True)
    (vault_path / 'Weather_Inbox').mkdir(exist_ok=True)
    (vault_path / 'Needs_Action').mkdir(exist_ok=True)
    
    print(f"\n✓ Vault path: {vault_path}")
    print(f"✓ CSV Inbox: {vault_path / 'Inbox'}")
    print(f"✓ Weather Inbox: {vault_path / 'Weather_Inbox'}")
    print(f"✓ Needs_Action: {vault_path / 'Needs_Action'}")
    
    # Check for existing files
    existing_csv = csv_watcher.check_existing_files()
    if existing_csv:
        print(f"\n📊 Found {len(existing_csv)} existing CSV file(s)")
        for csv_file in existing_csv:
            csv_handler.create_action_file(csv_file)
            print(f"  ✓ Created action file for: {csv_file.name}")
    
    existing_weather = weather_watcher.check_existing_files()
    if existing_weather:
        print(f"\n🌦️  Found {len(existing_weather)} weather bulletin file(s)")
        for file in existing_weather:
            content = weather_handler.read_file_contents(file)
            if content:
                rainfall_data = weather_handler.extract_rainfall_data(content)
                warnings = weather_handler.extract_warnings(content)
                weather_handler.create_action_file(file, content, rainfall_data, warnings)
                print(f"  ✓ Created task file for: {file.name}")
                print(f"     - Rainfall locations: {len(rainfall_data)}")
                print(f"     - Warnings: {len(warnings)}")
    
    print("\n" + "=" * 60)
    print("Starting watchers (will run for 10 seconds)...")
    print("Drop files in Inbox or Weather_Inbox to test")
    print("=" * 60)
    
    # Run watchers in separate threads for 10 seconds
    csv_thread = threading.Thread(target=csv_watcher.start, daemon=True)
    weather_thread = threading.Thread(target=weather_watcher.start, daemon=True)
    
    csv_thread.start()
    weather_thread.start()
    
    try:
        # Wait for 10 seconds
        for i in range(10):
            time.sleep(1)
            print(f"⏱  Watchers running... ({i+1}s)")
            
            # Check for new task files
            needs_action = vault_path / 'Needs_Action'
            task_files = list(needs_action.glob('*.md'))
            if task_files:
                print(f"  📄 Task files in Needs_Action: {len(task_files)}")
                
    except KeyboardInterrupt:
        print("\n\n⏹  Stopping watchers...")
    
    csv_watcher.stop()
    weather_watcher.stop()
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    needs_action = vault_path / 'Needs_Action'
    task_files = list(needs_action.glob('*.md'))
    
    if task_files:
        print(f"\n✅ SUCCESS: {len(task_files)} task file(s) created:")
        for tf in task_files:
            print(f"   • {tf.name}")
    else:
        print("\n⚠️  No task files created")
        print("   Tip: Drop a .txt or .pdf file in Hydrology-Vault/Weather_Inbox/")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_dual_watchers()
