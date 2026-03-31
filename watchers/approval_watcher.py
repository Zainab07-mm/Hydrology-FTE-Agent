"""
Approval Watcher for Hydrology FTE Agent

This watcher monitors Hydrology-Vault/Needs_Action/ for APPROVAL_ files.
When a user adds DECISION: YES or DECISION: NO to an approval file,
this watcher processes the decision and sends emails (if approved).

Workflow:
1. Watch for APPROVAL_*.md files in Needs_Action/
2. Check file content every 10 seconds for DECISION: field
3. If DECISION: YES → send email via mcp_email_server
4. If DECISION: NO → log cancellation and move to Done/
5. Update Dashboard with approval history
"""

import time
import logging
import shutil
import re
import os
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApprovalWatcher')


class ApprovalFileHandler(FileSystemEventHandler):
    """Handles approval file changes and processes decisions."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.processed_files = set()

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(exist_ok=True)

        # Track pending approvals
        self.pending_approvals = {}

    def extract_decision(self, file_path: Path) -> str:
        """
        Extract DECISION value from approval file.
        
        Returns:
            'YES', 'NO', or None if no decision found
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Look for DECISION: field
            decision_match = re.search(r'DECISION:\s*(YES|NO)', content, re.IGNORECASE)
            
            if decision_match:
                return decision_match.group(1).upper()
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading decision from {file_path}: {e}")
            return None

    def extract_approval_details(self, file_path: Path) -> dict:
        """Extract river name, discharge, and recipient from approval file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            details = {
                'river_name': 'Unknown',
                'discharge': 0,
                'recipient': 'recipient@gmail.com'
            }
            
            # Extract river name
            river_match = re.search(r'\*\*River Name\*\*\s*\|\s*([^\|]+)', content)
            if river_match:
                details['river_name'] = river_match.group(1).strip()
            
            # Extract discharge
            discharge_match = re.search(r'\*\*Discharge\*\*\s*\|\s*([\d.]+)', content)
            if discharge_match:
                details['discharge'] = float(discharge_match.group(1))
            
            # Extract recipient
            recipient_match = re.search(r'\*\*Proposed Recipient:\*\*\s*`?([^`]+)`?', content)
            if recipient_match:
                details['recipient'] = recipient_match.group(1).strip()
            
            return details
            
        except Exception as e:
            logger.error(f"Error extracting details from {file_path}: {e}")
            return {'river_name': 'Unknown', 'discharge': 0, 'recipient': 'recipient@gmail.com'}

    def process_approval(self, file_path: Path, decision: str):
        """
        Process an approval decision (YES or NO).
        
        Args:
            file_path: Path to approval file
            decision: 'YES' or 'NO'
        """
        if file_path.name in self.processed_files:
            return
        
        logger.info(f"Processing approval decision: {decision} for {file_path.name}")
        
        # Extract details
        details = self.extract_approval_details(file_path)
        river_name = details['river_name']
        discharge = details['discharge']
        recipient = details['recipient']
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if decision == 'YES':
            # Send the email
            logger.info(f"✅ Approval GRANTED - Sending flood alert for {river_name}")
            
            try:
                from mcp_email_server import send_flood_alert
                
                success = send_flood_alert(
                    river_name=river_name,
                    discharge=discharge,
                    risk_level='High',
                    recipient_email=recipient
                )
                
                if success:
                    logger.info(f"✅ Email sent successfully to {recipient}")
                    status = "APPROVED - Email Sent"
                else:
                    logger.error(f"❌ Email sending failed")
                    status = "APPROVED - Send Failed"
                    
            except Exception as e:
                logger.error(f"❌ Error sending email: {e}")
                status = f"APPROVED - Error: {e}"
            
            # Move to Done folder
            done_path = self.done / f"APPROVED_{file_path.name}"
            shutil.move(str(file_path), str(done_path))
            
            # Log to approval history
            self.log_approval_decision(file_path.name, river_name, discharge, decision, status, recipient)
            
            # Update Dashboard
            self.update_dashboard_approval(river_name, discharge, 'APPROVED')
            
            print(f"\n{'='*60}")
            print(f"✅ APPROVAL PROCESSED - Email Sent")
            print(f"{'='*60}")
            print(f"River: {river_name}")
            print(f"Discharge: {discharge:.2f} m³/s")
            print(f"Decision: {decision}")
            print(f"Status: Email sent to {recipient}")
            print(f"{'='*60}\n")
            
        elif decision == 'NO':
            # Cancel the email
            logger.info(f"❌ Approval DENIED - Cancelling flood alert for {river_name}")
            
            status = "DENIED - Email Cancelled"
            
            # Move to Done folder
            done_path = self.done / f"DENIED_{file_path.name}"
            shutil.move(str(file_path), str(done_path))
            
            # Log to approval history
            self.log_approval_decision(file_path.name, river_name, discharge, decision, status, recipient)
            
            # Update Dashboard
            self.update_dashboard_approval(river_name, discharge, 'DENIED')
            
            print(f"\n{'='*60}")
            print(f"❌ APPROVAL PROCESSED - Email Cancelled")
            print(f"{'='*60}")
            print(f"River: {river_name}")
            print(f"Discharge: {discharge:.2f} m³/s")
            print(f"Decision: {decision}")
            print(f"Status: Email cancelled by user")
            print(f"{'='*60}\n")
        
        # Mark as processed
        self.processed_files.add(file_path.name)

    def log_approval_decision(self, filename, river_name, discharge, decision, status, recipient):
        """Log approval decision to approval_history.txt."""
        log_path = self.vault_path / 'approval_history.txt'
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_entry = f"""
{'='*60}
Approval Decision
{'='*60}
Timestamp: {timestamp}
File: {filename}
River: {river_name}
Discharge: {discharge:.2f} m³/s
Recipient: {recipient}
Decision: {decision}
Status: {status}
{'='*60}
"""
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def update_dashboard_approval(self, river_name, discharge, status):
        """Update Dashboard.md with approval status."""
        dashboard_path = self.vault_path / 'Dashboard.md'
        
        if not dashboard_path.exists():
            return
        
        try:
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Check if approval history section exists
            if "## ⚖️ Approval History" not in content:
                # Add approval history section before the footer
                approval_section = """
---

## ⚖️ Approval History

| Timestamp | River | Discharge | Decision | Status |
|-----------|-------|-----------|----------|--------|
"""
                # Insert before the last section (footer)
                lines = content.split('\n')
                for i in range(len(lines) - 1, 0, -1):
                    if lines[i].startswith('---') and i > 10:
                        lines.insert(i, approval_section)
                        break
                content = '\n'.join(lines)
            
            # Add entry to approval history table
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            status_emoji = "✅" if status == 'APPROVED' else "❌"
            new_row = f"| {timestamp} | {river_name} | {discharge:.2f} m³/s | {status} | {status_emoji} |\n"
            
            # Find the approval history table and add row
            if "## ⚖️ Approval History" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('| Timestamp |') or (line.startswith('|---') and i > 0 and 'Approval History' in content[:content.find(line)]):
                        # Insert after the header/separator
                        insert_pos = i + 1
                        if lines[insert_pos].startswith('|---'):
                            insert_pos += 1
                        lines.insert(insert_pos, new_row)
                        break
                content = '\n'.join(lines)
            
            dashboard_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def on_modified(self, event):
        """Triggered when a file is modified."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process APPROVAL_*.md files in Needs_Action
        if not file_path.name.startswith('APPROVAL_'):
            return
        
        if file_path.suffix.lower() != '.md':
            return
        
        if str(file_path.parent) != str(self.needs_action):
            return

        logger.info(f"Approval file modified: {file_path.name}")

        # Check for decision
        decision = self.extract_decision(file_path)
        
        if decision:
            logger.info(f"Decision found: {decision}")
            self.process_approval(file_path, decision)
        else:
            logger.debug(f"No decision found yet in {file_path.name}")

    def check_pending_approvals(self):
        """Check all pending approval files for decisions."""
        if not self.needs_action.exists():
            return
        
        approval_files = [f for f in self.needs_action.glob('APPROVAL_*.md') 
                         if f.name not in self.processed_files]
        
        for file_path in approval_files:
            decision = self.extract_decision(file_path)
            
            if decision:
                logger.info(f"Decision detected in {file_path.name}: {decision}")
                self.process_approval(file_path, decision)
            else:
                # Track pending
                self.pending_approvals[file_path.name] = file_path.stat().st_mtime


class ApprovalWatcher:
    """
    Main watcher class that monitors for approval files and processes decisions.
    """

    def __init__(self, vault_path: str, check_interval: int = 10):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.observer = None
        self.handler = None

    def start(self):
        """Start the approval watcher."""
        # Ensure directories exist
        self.vault_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'Needs_Action').mkdir(exist_ok=True)
        (self.vault_path / 'Done').mkdir(exist_ok=True)

        self.handler = ApprovalFileHandler(str(self.vault_path))
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.vault_path / 'Needs_Action'),
            recursive=False
        )

        self.observer.start()
        logger.info(f"Approval Watcher started. Monitoring: {self.vault_path / 'Needs_Action'}")
        
        print(f"\n{'='*60}")
        print(f"⚖️  Approval Watcher Active")
        print(f"{'='*60}")
        print(f"Monitoring: {self.vault_path / 'Needs_Action'}")
        print(f"Check interval: {self.check_interval}s")
        print(f"\nℹ️  How to use:")
        print(f"  1. When HIGH RISK is detected, approval file is created")
        print(f"  2. Open the file and type: DECISION: YES  (or NO)")
        print(f"  3. Save the file")
        print(f"  4. Watcher will process your decision within {self.check_interval}s")
        print(f"{'='*60}\n")

        try:
            while True:
                time.sleep(self.check_interval)
                
                # Also check for pending approvals periodically
                self.handler.check_pending_approvals()
                
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the approval watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Approval Watcher stopped")

    def get_pending_count(self) -> int:
        """Get count of pending approval files."""
        if not self.needs_action.exists():
            return 0
        
        return len([f for f in self.needs_action.glob('APPROVAL_*.md') 
                   if f.name not in self.handler.processed_files])


def main():
    """Main entry point for the Approval Watcher."""
    import sys

    # Default vault path (relative to script location)
    default_vault = Path(__file__).parent.parent / 'Hydrology-Vault'

    vault_path = sys.argv[1] if len(sys.argv) > 1 else str(default_vault)

    logger.info("=" * 60)
    logger.info("⚖️  Hydrology FTE - Approval Watcher")
    logger.info("=" * 60)
    logger.info(f"Vault Path: {vault_path}")
    logger.info(f"Monitoring: {Path(vault_path) / 'Needs_Action'}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    watcher = ApprovalWatcher(vault_path)
    watcher.start()


if __name__ == "__main__":
    main()
