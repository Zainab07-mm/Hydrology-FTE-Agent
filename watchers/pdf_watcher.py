"""
PDF/TXT File Watcher for Hydrology FTE Agent

This watcher monitors the /Weather_Inbox folder for new .txt or .pdf files
(rainfall bulletins). When a new file is detected, it:
1. Reads the file contents
2. Extracts rainfall amounts (mm values)
3. Creates a task file in /Needs_Action/ with extracted data
"""

import time
import logging
import re
import hashlib
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PDFWatcher')


class WeatherFileHandler(FileSystemEventHandler):
    """Handles .txt and .pdf file creation events in the Weather_Inbox folder."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.weather_inbox = self.vault_path / 'Weather_Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.processed_files = set()

        # Ensure directories exist
        self.weather_inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)

    def read_file_contents(self, file_path: Path) -> str:
        """
        Read contents of a .txt or .pdf file.
        
        For .txt files: Direct text reading
        For .pdf files: Try to extract text (basic implementation)
        
        Returns:
            File contents as string, or None if reading fails
        """
        try:
            if file_path.suffix.lower() == '.txt':
                # Read text file directly
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.suffix.lower() == '.pdf':
                # For PDF files, try to read as text (works for simple PDFs)
                # Note: For production, use a proper PDF library like PyPDF2 or pdfplumber
                try:
                    # Attempt basic text extraction
                    with open(file_path, 'rb') as f:
                        # Simple PDF text extraction (limited)
                        # This is a basic implementation - works for text-based PDFs
                        content = f.read().decode('utf-8', errors='ignore')
                        # Remove PDF binary markers and extract readable text
                        text_content = re.sub(r'[^\x20-\x7E\n\r\t]', '', content)
                        return text_content if text_content.strip() else None
                except Exception:
                    # If PDF reading fails, log and return None
                    logger.warning(f"Could not extract text from PDF: {file_path.name}")
                    return None
            
            return None
            
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {file_path.name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path.name}: {str(e)}")
            return None

    def extract_rainfall_data(self, content: str) -> list:
        """
        Extract rainfall amounts (mm values) from bulletin content.
        
        Uses regex patterns to find:
        - Numbers followed by 'mm' or 'millimeters'
        - Numbers in context of 'rainfall' or 'precipitation'
        - River catchment rainfall mentions
        
        Returns:
            List of dictionaries with location and rainfall amount
        """
        rainfall_data = []
        
        # Pattern: Line-based extraction for "Location: Xmm rainfall recorded" format
        # Matches lines like: "Chenab River catchment: 45mm rainfall recorded"
        line_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:River|Basin|Catchment|Area|Region))\s*(?:catchment)?[:\s]+?\s*(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?\s*(?:rainfall)?'
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to match river/location + rainfall pattern
            match = re.search(line_pattern, line, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                amount = float(match.group(2))
                
                # Check if we already have this location
                if not any(r['location'].lower() == location.lower() for r in rainfall_data):
                    rainfall_data.append({
                        'location': location,
                        'rainfall_mm': amount,
                        'confidence': 'high'
                    })
        
        # Fallback: Pattern for explicit mm mentions if line-based failed
        if not rainfall_data:
            mm_pattern = r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)'
            mm_matches = re.finditer(mm_pattern, content, re.IGNORECASE)
            
            for match in mm_matches:
                amount = float(match.group(1))
                # Try to find location context (look backwards in text)
                start_pos = max(0, match.start() - 100)
                context = content[start_pos:match.start()]
                
                # Look for river/location names in context
                location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:River|catchment|basin|area|region))'
                location_match = re.search(location_pattern, context, re.IGNORECASE)
                location = location_match.group(1) if location_match else "Unknown Location"
                
                rainfall_data.append({
                    'location': location.strip(),
                    'rainfall_mm': amount,
                    'confidence': 'medium'
                })
        
        return rainfall_data

    def extract_warnings(self, content: str) -> list:
        """
        Extract warning/alert messages from bulletin content.
        
        Returns:
            List of warning messages found
        """
        warnings = []
        
        # Look for warning keywords
        warning_keywords = ['warning', 'alert', 'caution', 'heavy rainfall', 
                          'flood', 'danger', 'expected', 'advisory']
        
        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in warning_keywords):
                warnings.append(line.strip())
        
        return warnings

    def on_created(self, event):
        """Triggered when a new file is created."""
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # Only process .txt and .pdf files in Weather_Inbox
        if source_path.suffix.lower() not in ['.txt', '.pdf']:
            return

        if str(source_path.parent) != str(self.weather_inbox):
            return

        # Avoid processing the same file twice
        file_hash = hashlib.md5(str(source_path).encode()).hexdigest()
        if file_hash in self.processed_files:
            return

        logger.info(f"New weather bulletin detected: {source_path.name}")

        # Read file contents
        content = self.read_file_contents(source_path)
        
        if content is None:
            logger.error(f"Failed to read file: {source_path.name}")
            self.create_error_task(source_path, "Could not read file contents")
            return

        # Extract rainfall data
        rainfall_data = self.extract_rainfall_data(content)
        
        # Extract warnings
        warnings = self.extract_warnings(content)
        
        # Create action file with extracted data
        self.create_action_file(source_path, content, rainfall_data, warnings)
        self.processed_files.add(file_hash)

    def create_error_task(self, file_path: Path, error_message: str) -> Path:
        """Create an error task file in Needs_Action folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_filename = f"WEATHER_ERROR_{file_path.stem}_{timestamp}.md"
        action_path = self.needs_action / action_filename

        content = f"""---
type: weather_bulletin_error
source_file: {file_path.name}
created: {datetime.now().isoformat()}
priority: high
status: pending
---

# ⚠️ Weather Bulletin Processing Error

## Source File
- **Name:** {file_path.name}
- **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Error
{error_message}

## Next Steps
1. Check if file is corrupted or in unsupported format
2. Try converting to plain text format
3. Drop the corrected file back into Weather_Inbox

---

*Error generated by Hydrology FTE Agent - Weather Watcher*
"""

        action_path.write_text(content, encoding='utf-8')
        logger.warning(f"Error task created: {action_path.name}")
        return action_path

    def create_action_file(self, file_path: Path, content: str, 
                          rainfall_data: list, warnings: list) -> Path:
        """Create a markdown action file in Needs_Action folder with extracted data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_filename = f"WEATHER_{file_path.stem}_{timestamp}.md"
        action_path = self.needs_action / action_filename

        # Build rainfall data section
        rainfall_section = ""
        if rainfall_data:
            rainfall_section = """
## Extracted Rainfall Data

| Location | Rainfall (mm) | Confidence |
|----------|---------------|------------|
"""
            for data in rainfall_data:
                rainfall_section += f"| {data['location']} | {data['rainfall_mm']:.1f} mm | {data['confidence']} |\n"
        else:
            rainfall_section = "\n**No rainfall data extracted**\n"

        # Build warnings section
        warnings_section = ""
        if warnings:
            warnings_section = """
## Warnings/Alerts Detected

"""
            for warning in warnings:
                warnings_section += f"- {warning}\n"
        else:
            warnings_section = "\n*No warnings detected*\n"

        content_md = f"""---
type: weather_bulletin
source_file: {file_path.name}
source_path: {file_path.absolute()}
created: {datetime.now().isoformat()}
priority: normal
status: pending
processing_stage: review
rainfall_locations: {len(rainfall_data)}
warnings_count: {len(warnings)}
---

# 🌦️ Weather Bulletin Processing Request

## Source File
- **Name:** {file_path.name}
- **Path:** {file_path.absolute()}
- **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Type:** {file_path.suffix[1:].upper()}

## Original Content Preview
```
{content[:500]}{'...' if len(content) > 500 else ''}
```
{rainfall_section}
{warnings_section}

## Required Processing Steps
1. [ ] Review extracted rainfall data
2. [ ] Correlate with river discharge data (if available)
3. [ ] Assess flood risk based on rainfall + discharge
4. [ ] Generate combined hydrology + weather report
5. [ ] Issue alerts if critical thresholds exceeded

## Instructions for Qwen AI Agent
Process this weather bulletin:
1. Verify extracted rainfall amounts are accurate
2. Cross-reference with existing hydrology data
3. Update risk assessments if heavy rainfall detected
4. Generate alert if rainfall + discharge indicate flood risk

Move this file to /Done when processing is complete.
"""

        action_path.write_text(content_md, encoding='utf-8')
        logger.info(f"Weather task created: {action_path.name}")
        
        # Print confirmation to terminal
        print(f"\n{'='*60}")
        print(f"🌦️  WEATHER BULLETIN DETECTED")
        print(f"{'='*60}")
        print(f"File: {file_path.name}")
        print(f"Rainfall locations found: {len(rainfall_data)}")
        for data in rainfall_data:
            print(f"  • {data['location']}: {data['rainfall_mm']:.1f} mm")
        if warnings:
            print(f"Warnings: {len(warnings)}")
            for warning in warnings[:3]:  # Show first 3 warnings
                print(f"  ⚠️  {warning}")
        print(f"Task file: {action_path.name}")
        print(f"{'='*60}\n")
        
        return action_path


class PDFWatcher:
    """
    Main watcher class that monitors the Weather_Inbox folder for .txt/.pdf files.
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
        (self.vault_path / 'Weather_Inbox').mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'Needs_Action').mkdir(exist_ok=True)
        (self.vault_path / 'Done').mkdir(exist_ok=True)

        self.handler = WeatherFileHandler(str(self.vault_path))
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.vault_path / 'Weather_Inbox'),
            recursive=False
        )

        self.observer.start()
        logger.info(f"Weather Watcher started. Monitoring: {self.vault_path / 'Weather_Inbox'}")

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
            logger.info("Weather Watcher stopped")

    def check_existing_files(self) -> list:
        """Check for existing .txt/.pdf files in Weather_Inbox (for initial scan)."""
        inbox_path = self.vault_path / 'Weather_Inbox'
        files = list(inbox_path.glob('*.txt')) + list(inbox_path.glob('*.pdf'))
        return files


def main():
    """Main entry point for the Weather Watcher."""
    import sys

    # Default vault path (relative to script location)
    default_vault = Path(__file__).parent.parent / 'Hydrology-Vault'

    vault_path = sys.argv[1] if len(sys.argv) > 1 else str(default_vault)

    logger.info("=" * 50)
    logger.info("🌦️  Hydrology FTE - Weather Watcher")
    logger.info("=" * 50)
    logger.info(f"Vault Path: {vault_path}")
    logger.info(f"Monitoring: {Path(vault_path) / 'Weather_Inbox'}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)

    watcher = PDFWatcher(vault_path)

    # Check for existing files first
    existing = watcher.check_existing_files()
    if existing:
        logger.info(f"Found {len(existing)} existing weather bulletin file(s)")
        for file in existing:
            # Simulate file detection
            content = watcher.handler.read_file_contents(file)
            if content:
                rainfall_data = watcher.handler.extract_rainfall_data(content)
                warnings = watcher.handler.extract_warnings(content)
                watcher.handler.create_action_file(file, content, rainfall_data, warnings)

    # Start watching
    watcher.start()


if __name__ == "__main__":
    main()
