"""
Schedule Setup for Hydrology FTE Agent

This script automatically creates Windows Task Scheduler tasks:
1. Daily Hydrology FTE Agent (8:00 AM) - Main monitoring

Usage:
    python schedule_setup.py

Requirements:
    - Administrator privileges (for task creation)
    - Python 3.8+
    - Windows OS
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


def get_python_path():
    """Get the current Python executable path."""
    return sys.executable


def get_script_directory():
    """Get the directory where this script is located."""
    return Path(__file__).parent.absolute()


def create_scheduled_task(task_name="HydrologyFTE_DailyAgent", time="08:00"):
    """
    Create a Windows Task Scheduler task for daily hydrology monitoring.

    Args:
        task_name: Name of the scheduled task
        time: Time to run task (HH:MM format, 24-hour)

    Returns:
        bool: True if successful, False otherwise
    """
    script_dir = get_script_directory()
    python_path = get_python_path()
    main_script = script_dir / "main.py"

    print("\n" + "=" * 60)
    print("📊 Hydrology FTE Agent - Schedule Setup")
    print("=" * 60)
    print(f"\n📁 Script Directory: {script_dir}")
    print(f"🐍 Python Path: {python_path}")
    print(f"📄 Main Script: {main_script}")
    print(f"\n⏰ Scheduled Time: Daily at {time}")
    print("-" * 60)

    # Build the schtasks command for daily monitoring
    command = [
        "schtasks",
        "/Create",
        "/TN", task_name,
        "/TR", f'"{python_path}" "{main_script}" --watcher',
        "/SC", "DAILY",
        "/ST", time,
        "/RL", "HIGHEST",
        "/F"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("\n✅ SUCCESS! Daily Agent task created!")
            print("=" * 60)
            print(f"\n📌 Task Name: {task_name}")
            print(f"⏰ Schedule: Daily at {time}")
            print(f"🚀 Action: Run hydrology monitoring with all watchers")
            print(f"👤 Run Level: Highest privileges")

            print("\n📖 To verify:")
            print("   1. Press Win + R")
            print("   2. Type: taskschd.msc")
            print("   3. Look for task in Active Tasks list")

            print("\n📖 To test manually:")
            print(f"   schtasks /Run /TN \"{task_name}\"")

            print("\n📖 To delete:")
            print(f"   schtasks /Delete /TN \"{task_name}\" /F")

            print("\n" + "=" * 60)
            return True
        else:
            print(f"\n❌ FAILED: {result.stderr}")
            print("\n💡 Troubleshooting:")
            print("   1. Run terminal as Administrator")
            print("   2. Check if task already exists (delete and retry)")
            print("   3. Verify Python path is correct")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    """Main function to set up all scheduled tasks."""
    print("\n" + "=" * 60)
    print("📅 HYDROLOGY FTE AGENT - SCHEDULING SETUP")
    print("=" * 60)
    print("\nThis script will create Windows Task Scheduler tasks:")
    print("  1. Daily Agent Monitoring (8:00 AM)")
    print("     - Runs main.py --watcher")
    print("     - Monitors Inbox, Weather_Inbox, Needs_Action")
    print("     - Processes hydrology data automatically")

    # Confirm with user
    print("\n" + "=" * 60)
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\n❌ Setup cancelled by user")
        return

    # Create the scheduled task
    print("\n" + "=" * 60)
    print("📅 TASK: Daily Agent Monitoring")
    print("=" * 60)
    success = create_scheduled_task()

    # Summary
    print("\n" + "=" * 60)
    print("📋 SETUP SUMMARY")
    print("=" * 60)

    if success:
        print("✅ Daily Agent: CREATED (8:00 AM)")
        print("\n🎉 Task created successfully!")
        print("\n📝 Next steps:")
        print("   1. Verify task in Windows Task Scheduler")
        print("   2. Drop a CSV file in Hydrology-Vault/Inbox to test")
        print("   3. Agent will run automatically every day at 8:00 AM")
    else:
        print("\n❌ Setup failed. Check error messages above.")
        print("\n💡 Troubleshooting:")
        print("   1. Run terminal as Administrator")
        print("   2. Ensure Python is installed and in PATH")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
