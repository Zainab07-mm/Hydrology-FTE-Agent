"""
CSV File Watcher for Hydrology FTE Agent

This watcher monitors the /Inbox folder for new CSV files.
When a new CSV file is detected, it creates an action file in /Needs_Action
to trigger the Qwen AI agent for processing.
"""

import time
import logging
import hashlib
import shutil
import csv
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CSVWatcher')


class CSVFileHandler(FileSystemEventHandler):
    """Handles CSV file creation events in the Inbox folder."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.errors = self.vault_path / 'Errors'
        self.processed_files = set()

        # Ensure directories exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)
        self.errors.mkdir(exist_ok=True)

    def validate_csv_file(self, csv_path: Path) -> tuple:
        """
        Validate a CSV file for proper format and content.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists and is readable
            if not csv_path.exists():
                return False, "File does not exist"

            # Check file size (empty file)
            if csv_path.stat().st_size == 0:
                return False, "File is empty"

            # Try to read and parse CSV
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Check if file has any content
                first_line = f.readline()
                if not first_line.strip():
                    return False, "File has no content"

                # Reset and try CSV parsing
                f.seek(0)
                reader = csv.DictReader(f)

                # Check if CSV has headers
                if not reader.fieldnames:
                    return False, "CSV has no headers"

                # Check for required columns
                required_cols = {'River', 'Width_m', 'Depth_m', 'Velocity_mps'}
                actual_cols = set(reader.fieldnames)
                missing_cols = required_cols - actual_cols

                if missing_cols:
                    return False, f"Missing required columns: {', '.join(missing_cols)}"

                # Check if CSV has data rows
                rows = list(reader)
                if not rows:
                    return False, "CSV has headers but no data rows"

                # Validate data in first row
                first_row = rows[0]
                for col in ['Width_m', 'Depth_m', 'Velocity_mps']:
                    try:
                        float(first_row[col])
                    except (ValueError, TypeError):
                        return False, f"Invalid numeric value in column '{col}'"

            return True, None

        except csv.Error as e:
            return False, f"CSV parsing error: {str(e)}"
        except UnicodeDecodeError as e:
            return False, f"File encoding error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def handle_invalid_file(self, csv_path: Path, error_message: str) -> Path:
        """
        Handle an invalid CSV file by moving it to Errors folder and creating error report.

        Returns:
            Path to error report in Done folder
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Move file to Errors folder
        error_filename = f"{csv_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{csv_path.suffix}"
        error_path = self.errors / error_filename
        shutil.move(str(csv_path), str(error_path))

        # Create error report in Done folder
        error_report_name = f"ERROR_{csv_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        error_report_path = self.done / error_report_name

        content = f"""# ❌ Error Processing File

**Original File:** {csv_path.name}

**Error Detected:** {timestamp}

**Error Message:** {error_message}

---

## What Happened

The CSV file dropped in the Inbox folder could not be processed because:

> **{error_message}**

## Required CSV Format

Your CSV files must have these columns:
- `River` - River name (text)
- `Width_m` - Width in meters (number)
- `Depth_m` - Depth in meters (number)
- `Velocity_mps` - Velocity in meters/second (number)

## Next Steps

1. Check the original file for the error above
2. Fix the issue (add missing columns, correct data format, etc.)
3. Drop the corrected file back into the Inbox folder

---

*Error report generated by Hydrology FTE Agent*
"""

        error_report_path.write_text(content, encoding='utf-8')
        logger.warning(f"❌ Invalid file moved to Errors: {error_path.name}")
        logger.warning(f"Error report created: {error_report_path.name}")

        return error_report_path

    def on_created(self, event):
        """Triggered when a new file is created."""
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # Only process CSV files in Inbox
        if source_path.suffix.lower() != '.csv':
            return

        if str(source_path.parent) != str(self.inbox):
            return

        # Avoid processing the same file twice
        file_hash = hashlib.md5(str(source_path).encode()).hexdigest()
        if file_hash in self.processed_files:
            return

        logger.info(f"New CSV file detected: {source_path.name}")

        # Validate the CSV file before processing
        is_valid, error_message = self.validate_csv_file(source_path)

        if not is_valid:
            logger.error(f"Invalid CSV file: {source_path.name} - {error_message}")
            self.handle_invalid_file(source_path, error_message)
            return

        # File is valid, create action file
        self.create_action_file(source_path)
        self.processed_files.add(file_hash)
    
    def create_action_file(self, csv_path: Path) -> Path:
        """Create a markdown action file in Needs_Action folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_filename = f"HYDROLOGY_{csv_path.stem}_{timestamp}.md"
        action_path = self.needs_action / action_filename
        
        content = f"""---
type: hydrology_data
source_file: {csv_path.name}
source_path: {csv_path.absolute()}
created: {datetime.now().isoformat()}
priority: normal
status: pending
processing_stage: ingest
---

# 🌊 Hydrology Data Processing Request

## Source File
- **Name:** {csv_path.name}
- **Path:** {csv_path.absolute()}
- **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Required Processing Steps
1. [ ] Ingest CSV data
2. [ ] Compute discharge (Width × Depth × Velocity)
3. [ ] Analyze flow condition and risk
4. [ ] Generate hydrology report

## Instructions for Qwen AI Agent
Process this hydrology data file through the complete workflow:
1. Run `ingest_hydrology_data` skill to read the CSV
2. Run `compute_discharge` skill to calculate discharge values
3. Run `analyze_flow_condition` skill to classify conditions
4. Run `generate_hydrology_report` skill to create the report

Move this file to /Done when processing is complete.
"""
        
        action_path.write_text(content, encoding='utf-8')
        logger.info(f"Action file created: {action_path.name}")
        return action_path


class CSVWatcher:
    """
    Main watcher class that monitors the Inbox folder for CSV files.
    Runs continuously until stopped.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 5):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.observer = None
        self.handler = None
        
    def start(self):
        """Start the file watcher."""
        # Ensure directories exist
        self.vault_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'Inbox').mkdir(exist_ok=True)
        (self.vault_path / 'Needs_Action').mkdir(exist_ok=True)
        (self.vault_path / 'Done').mkdir(exist_ok=True)
        
        self.handler = CSVFileHandler(str(self.vault_path))
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.vault_path / 'Inbox'),
            recursive=False
        )
        
        self.observer.start()
        logger.info(f"CSV Watcher started. Monitoring: {self.vault_path / 'Inbox'}")
        
        try:
            while True:
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the file watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("CSV Watcher stopped")
    
    def check_existing_files(self) -> list:
        """Check for existing CSV files in Inbox (for initial scan)."""
        inbox_path = self.vault_path / 'Inbox'
        csv_files = list(inbox_path.glob('*.csv'))
        return csv_files


def main():
    """Main entry point for the CSV Watcher."""
    import sys
    
    # Default vault path (relative to script location)
    default_vault = Path(__file__).parent.parent / 'Hydrology-Vault'
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else str(default_vault)
    
    logger.info("=" * 50)
    logger.info("🌊 Hydrology FTE - CSV Watcher")
    logger.info("=" * 50)
    logger.info(f"Vault Path: {vault_path}")
    logger.info(f"Monitoring: {Path(vault_path) / 'Inbox'}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    watcher = CSVWatcher(vault_path)
    
    # Check for existing files first
    existing = watcher.check_existing_files()
    if existing:
        logger.info(f"Found {len(existing)} existing CSV file(s) in Inbox")
        for csv_file in existing:
            watcher.handler.create_action_file(csv_file)
    
    # Start watching
    watcher.start()


if __name__ == "__main__":
    main()
