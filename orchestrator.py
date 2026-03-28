"""
Orchestrator for Hydrology FTE Agent

This script connects the CSV Watcher with Qwen AI to create
a fully autonomous agent that processes hydrology data 24/7.

When a new CSV file is detected in /Inbox:
1. Watcher creates action file in /Needs_Action
2. Orchestrator picks up the action file
3. Qwen AI processes the data through all skills
4. Report is generated in /Done
5. Action file is moved to /Done
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
        """Get list of pending action files in Needs_Action folder."""
        return list(self.needs_action.glob('*.md'))
    
    def parse_action_file(self, action_path: Path) -> dict:
        """Parse an action file to extract task information."""
        content = action_path.read_text(encoding='utf-8')
        
        # Extract source file path from frontmatter
        source_file = None
        for line in content.split('\n'):
            if line.startswith('source_path:'):
                source_file = Path(line.split(':', 1)[1].strip())
                break
        
        return {
            'action_path': action_path,
            'source_file': source_file,
            'status': 'pending'
        }
    
    def process_task(self, task: dict) -> bool:
        """
        Process a single hydrology data task.
        
        Returns True if successful, False otherwise.
        """
        action_path = task['action_path']
        source_file = task['source_file']
        
        logger.info(f"Processing task: {action_path.name}")
        update_dashboard(str(self.vault_path), "Processing", str(action_path.name), "starting")
        
        if not source_file or not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            return False
        
        # Initialize workflow state
        state = {
            "file_path": str(source_file),
            "data": None,
            "results": None,
            "log": [],
            "action_file": str(action_path)
        }
        
        logger.info(f"🚀 Starting hydrology processing for: {source_file.name}")
        
        # Execute workflow loop
        max_iterations = 10  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1

            # Decide next skill using Qwen AI
            skill = decide_next_skill(state)

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
            
            # Execute the skill
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
                # Generate report with timestamped filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_name = f"report_{source_file.stem}_{timestamp}.md"
                report_path = self.done / report_name

                # Pass original DataFrame for formula calculations
                run_skill(skill, results=state["results"], df=state["data"], output_file=str(report_path))
                state["log"].append(skill)
                logger.info(f"📄 Report generated → {report_path}")
                
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
        return True
    
    def run(self):
        """Run the orchestrator loop."""
        logger.info("=" * 60)
        logger.info("🌊 Hydrology FTE Orchestrator")
        logger.info("=" * 60)
        logger.info(f"Vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        update_dashboard(str(self.vault_path), "Running", "System started", "waiting")
        
        try:
            while True:
                # Check for pending tasks
                tasks = self.get_pending_tasks()
                
                if tasks:
                    logger.info(f"Found {len(tasks)} pending task(s)")
                    for task in tasks:
                        task_info = self.parse_action_file(task)
                        self.process_task(task_info)
                else:
                    logger.debug("No pending tasks, waiting...")
                
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
