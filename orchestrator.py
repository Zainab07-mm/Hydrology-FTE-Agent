"""
Orchestrator for Hydrology FTE Agent

This script connects the CSV Watcher with Qwen AI to create
a fully autonomous agent that processes hydrology data 24/7.

When a new CSV file is detected in /Inbox:
1. Watcher creates action file in /Needs_Action
2. Orchestrator picks up the action file
3. Qwen AI creates a reasoning Plan.md file
4. Qwen AI processes the data through all skills
5. Report is generated in /Done
6. Action file is moved to /Done

SILVER TIER: Includes email alerts with human approval and LinkedIn auto-posting.
"""

import time
import logging
import shutil
from pathlib import Path
from datetime import datetime

from skill_runner import run_skill
from qwen_brain import decide_next_skill, update_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Orchestrator')


class HydrologyOrchestrator:
    """
    Orchestrates the autonomous hydrology data processing workflow.
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.check_interval = 10  # Check for new tasks every 10 seconds
        
        # Ensure directories exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)
        
    def get_pending_tasks(self) -> list:
        """Get list of pending action files in Needs_Action folder (HYDROLOGY and WEATHER only)."""
        # Only process HYDROLOGY and WEATHER action files, not APPROVAL files
        all_files = list(self.needs_action.glob('*.md'))
        return [f for f in all_files if f.name.startswith('HYDROLOGY_') or f.name.startswith('WEATHER_')]
    
    def parse_action_file(self, action_path: Path) -> dict:
        """Parse an action file to extract task information."""
        content = action_path.read_text(encoding='utf-8')

        # Extract source file path from frontmatter
        source_file = None
        retry_count = 0
        for line in content.split('\n'):
            if line.startswith('source_path:'):
                source_file = Path(line.split(':', 1)[1].strip())
            elif line.startswith('retry_count:'):
                try:
                    retry_count = int(line.split(':', 1)[1].strip())
                except ValueError:
                    retry_count = 0

        return {
            'action_path': action_path,
            'source_file': source_file,
            'retry_count': retry_count,
            'status': 'pending'
        }
    
    def process_task(self, task: dict) -> bool:
        """
        Process a single hydrology data task.

        Returns True if successful, False otherwise.
        """
        action_path = task['action_path']
        source_file = task['source_file']
        retry_count = task.get('retry_count', 0)

        # Check if max retries exceeded
        MAX_RETRIES = 3
        if retry_count >= MAX_RETRIES:
            logger.error(f"❌ Task {action_path.name} failed {retry_count} times, moving to Errors")
            print(f"\n⚠️  Task {action_path.name} failed {retry_count} times")
            print(f"   Moving to Errors folder for manual review")
            self.move_to_errors(action_path)
            return False

        # Safety check: skip if no source file
        if not source_file:
            logger.warning(f"⚠️  Skipping {action_path.name}: No source file found (might be an APPROVAL file)")
            print(f"\n⚠️  Skipping {action_path.name}: Not a hydrology/weather task")
            return False

        # Print to console for visibility
        print(f"\n{'='*60}")
        print(f"🌊 Processing: {action_path.name}")
        print(f"   Source: {source_file.name}")
        print(f"{'='*60}")

        logger.info(f"Processing task: {action_path.name}")
        update_dashboard(str(self.vault_path), "Processing", str(action_path.name), "starting")

        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            print(f"❌ Error: Source file not found: {source_file}")
            return False

        # Initialize workflow state
        state = {
            "file_path": str(source_file),
            "data": None,
            "results": None,
            "log": [],
            "action_file": str(action_path),
            "plan": None  # Will store the reasoning plan
        }

        logger.info(f"🚀 Starting hydrology processing for: {source_file.name}")

        # STEP 0: Create reasoning plan BEFORE any analysis
        logger.info("🧠 Creating reasoning plan...")
        update_dashboard(
            str(self.vault_path),
            "Planning",
            str(action_path.name),
            "create_plan"
        )

        # First, ingest data to get DataFrame for planning
        logger.info("📥 Ingesting data for initial analysis...")
        ingest_result = run_skill("ingest_hydrology_data", file_path=state["file_path"])

        if ingest_result.get('success'):
            state["data"] = ingest_result.get('data')
        else:
            logger.error("❌ Failed to ingest data")
            print(f"   ❌ Failed to ingest data")
            return False

        # Create the reasoning plan
        plan_result = run_skill("create_plan",
                               df=state["data"],
                               source_file=source_file,
                               vault_path=str(self.vault_path))

        if plan_result:
            state["plan"] = plan_result
            logger.info(f"✅ Plan created: {plan_result['plan_path']}")
        else:
            logger.warning("⚠️ Plan creation failed, continuing with standard workflow")

        # Execute remaining workflow loop
        max_iterations = 10  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Decide next skill using Qwen AI
            skill = decide_next_skill(state)

            # Print skill execution to console
            print(f"  🧠 Qwen → {skill}")

            logger.info(f"🧠 Qwen selected: {skill}")
            update_dashboard(
                str(self.vault_path),
                "Processing",
                str(action_path.name),
                skill
            )

            if skill == "DONE":
                logger.info("✅ Workflow completed successfully")
                break

            # Determine if skill requires approval (HITL)
            if skill in ['send_alert_email', 'post_linkedin']:
                max_attempts = 3  # External services
            else:
                max_attempts = 3  # Internal processing

            # Execute the skill
            if skill == "ingest_hydrology_data":
                # Already ingested for planning, skip
                logger.info("⏭️  Data already ingested, skipping")
                state["log"].append("ingest_hydrology_data (skipped - already done)")

            elif skill == "compute_discharge":
                result = run_skill(skill, df=state["data"])
                if result.get('success'):
                    state["data"] = result.get('data')
                    state["log"].append(skill)
                    print(f"  ✅ Completed: compute_discharge")
                else:
                    logger.error(f"❌ compute_discharge failed: {result.get('error')}")
                    break

            elif skill == "analyze_flow_condition":
                result = run_skill(skill, df=state["data"])
                if result.get('success'):
                    state["results"] = result.get('results')
                    state["log"].append(skill)
                    print(f"  ✅ Completed: analyze_flow_condition")
                else:
                    logger.error(f"❌ analyze_flow_condition failed: {result.get('error')}")
                    break

                # After analyzing flow, check for HIGH RISK and create approval requests
                logger.info("📧 Checking for HIGH RISK conditions...")
                update_dashboard(
                    str(self.vault_path),
                    "Alerting",
                    str(action_path.name),
                    "send_alert_email"
                )

                # Create approval requests for high-risk rivers (requires human approval)
                alert_result = run_skill("send_alert_email",
                                        results=state["results"],
                                        df=state["data"],
                                        vault_path=str(self.vault_path))

                if alert_result and alert_result.get('approval_requests_created', 0) > 0:
                    logger.info(f"⚠️ Created {alert_result['approval_requests_created']} approval request(s)")
                    logger.info(f"   Waiting for human decision in Needs_Action folder")
                    state["log"].append(f"send_alert_email ({alert_result['approval_requests_created']} pending approval)")
                else:
                    logger.info("ℹ️ No flood alerts required")
                    state["log"].append("send_alert_email (no alerts needed)")

            elif skill == "generate_hydrology_report":
                # Generate report with timestamped filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_name = f"report_{source_file.stem}_{timestamp}.md"
                report_path = self.done / report_name

                # Generate report
                result = run_skill(skill,
                                  results=state["results"],
                                  df=state["data"],
                                  output_file=str(report_path),
                                  plan=state["plan"])

                if result.get('success'):
                    state["log"].append(skill)
                    logger.info(f"📄 Report generated → {report_path}")
                    print(f"  📄 Report generated → {report_path}")
                else:
                    logger.error(f"❌ generate_hydrology_report failed: {result.get('error')}")
                    break

            else:
                logger.warning(f"⚠ Unknown skill: {skill}")
                break

        # Move action file to Done folder
        done_action_path = self.done / f"completed_{action_path.name}"
        shutil.move(str(action_path), str(done_action_path))

        update_dashboard(
            str(self.vault_path),
            "Idle",
            f"Completed: {source_file.name}",
            "DONE"
        )

        logger.info(f"✅ Task completed: {action_path.name} → {done_action_path}")
        print(f"\n{'='*60}")
        print(f"✅ TASK COMPLETE: {source_file.name}")
        print(f"   Report: {report_path.name}")
        print(f"   Action file moved to: {done_action_path.name}")
        print(f"{'='*60}\n")
        return True

    def increment_retry_count(self, action_path: Path) -> int:
        """
        Increment the retry count in an action file.
        Returns the new retry count.
        """
        try:
            content = action_path.read_text(encoding='utf-8')
            
            # Check if retry_count exists in frontmatter
            retry_count = 0
            for line in content.split('\n'):
                if line.startswith('retry_count:'):
                    try:
                        retry_count = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        retry_count = 0
                    break
            
            # Increment retry count
            new_retry_count = retry_count + 1
            
            # Update or add retry_count in frontmatter
            if 'retry_count:' in content:
                # Replace existing retry_count
                import re
                content = re.sub(
                    r'retry_count:\s*\d+',
                    f'retry_count: {new_retry_count}',
                    content
                )
            else:
                # Add retry_count after status line
                content = content.replace(
                    'status: pending',
                    f'status: pending\nretry_count: {new_retry_count}'
                )
            
            action_path.write_text(content, encoding='utf-8')
            return new_retry_count
            
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")
            return -1

    def move_to_errors(self, action_path: Path):
        """Move a failed action file to the Errors folder."""
        try:
            errors_dir = self.vault_path / 'Errors'
            errors_dir.mkdir(exist_ok=True)
            
            # Generate new filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            error_filename = f"FAILED_{action_path.stem}_{timestamp}{action_path.suffix}"
            error_path = errors_dir / error_filename
            
            # Add error note to file
            content = action_path.read_text(encoding='utf-8')
            error_note = f"\n\n---\n\n## ❌ Processing Failed\n\n**Failed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**Reason:** Maximum retries exceeded (3 attempts)\n\n**Manual review required.**\n"
            content += error_note
            
            error_path.write_text(content, encoding='utf-8')
            
            # Remove original file
            action_path.unlink()
            
            logger.info(f"📁 Moved to Errors: {error_filename}")
            print(f"   📁 File moved to: Errors/{error_filename}")
            
        except Exception as e:
            logger.error(f"Error moving to errors: {e}")
            print(f"   ❌ Error moving file to Errors: {e}")
    
    def run(self):
        """Run the orchestrator loop."""
        logger.info("=" * 60)
        logger.info("🌊 Hydrology FTE Orchestrator")
        logger.info("=" * 60)
        logger.info(f"Vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Print startup message to console
        print(f"\n{'='*60}")
        print(f"🌊 Hydrology FTE Orchestrator Started")
        print(f"{'='*60}")
        print(f"Vault: {self.vault_path}")
        print(f"Monitoring: {self.needs_action}")
        print(f"Check interval: {self.check_interval}s")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*60}\n")

        update_dashboard(str(self.vault_path), "Running", "System started", "waiting")
        
        try:
            while True:
                # Check for pending tasks
                tasks = self.get_pending_tasks()

                if tasks:
                    logger.info(f"Found {len(tasks)} pending task(s)")
                    print(f"⏳ Found {len(tasks)} pending task(s) in queue...")
                    for task in tasks:
                        task_info = self.parse_action_file(task)
                        self.process_task(task_info)
                else:
                    logger.debug("No pending tasks, waiting...")
                    print(f"⏳ No pending tasks... waiting ({self.check_interval}s)", end='\r', flush=True)

                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user")
            update_dashboard(str(self.vault_path), "Stopped", "User stopped", "N/A")


def main():
    """Main entry point for the Orchestrator."""
    import sys
    
    # Default vault path (relative to script location)
    default_vault = Path(__file__).parent / 'Hydrology-Vault'
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else str(default_vault)
    
    orchestrator = HydrologyOrchestrator(vault_path)
    orchestrator.run()


if __name__ == "__main__":
    main()
