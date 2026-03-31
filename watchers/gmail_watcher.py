"""
Gmail Watcher for Hydrology FTE Agent

This watcher monitors Gmail inbox for new emails with attachments.
When an email with CSV attachment is detected, it:
1. Downloads the attachment
2. Saves it to Hydrology-Vault/Inbox/
3. Creates an action file for processing

Requirements:
    - Gmail account with IMAP enabled
    - Gmail App Password (same as sending)
    - python-dotenv installed

Setup Instructions:
    1. Enable IMAP in Gmail:
       - Gmail Settings → Forwarding and POP/IMAP → Enable IMAP
    2. Use same App Password as sending (in .env file)
    3. Run: python watchers/gmail_watcher.py

Silver Tier Feature:
    - Automatically processes hydrology data from email attachments
    - Filters emails by subject keywords (e.g., "Hydrology", "River Data")
    - Saves attachments and triggers processing workflow
"""

import imaplib
import email
from email.header import decode_header
from email.message import Message as EmailMessage
from pathlib import Path
import time
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GmailWatcher')

# Gmail configuration
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

# IMAP configuration
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993

# Keywords to filter relevant emails
EMAIL_KEYWORDS = ['hydrology', 'river', 'flood', 'discharge', 'data', 'measurement', 'water level']

# Attachments to download
ATTACHMENT_EXTENSIONS = ['.csv', '.xls', '.xlsx', '.pdf']


class GmailWatcher:
    """
    Monitors Gmail inbox for new emails with attachments.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.inbox_dir = self.vault_path / 'Inbox'
        self.check_interval = check_interval  # seconds
        self.processed_emails = set()
        self.last_check = datetime.now()

        # Ensure inbox directory exists
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

        # Validate credentials
        if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
            logger.error("❌ Gmail credentials not configured in .env")
            logger.error("   Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
            raise ValueError("Gmail credentials not configured")

    def connect(self):
        """Connect to Gmail IMAP server."""
        try:
            logger.info(f"📧 Connecting to Gmail IMAP: {GMAIL_ADDRESS}")
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            logger.info("✅ Connected to Gmail successfully")
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    def decode_subject(self, subject):
        """Decode MIME encoded subject line."""
        if not subject:
            return ""

        decoded_parts = decode_header(subject)
        decoded = ""
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                try:
                    decoded += content.decode(encoding or 'utf-8')
                except (UnicodeDecodeError, LookupError):
                    decoded += content.decode('latin-1')
            else:
                decoded += content
        return decoded

    def decode_filename(self, filename):
        """Decode MIME encoded filename."""
        if not filename:
            return ""

        decoded_parts = decode_header(filename)
        decoded = ""
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                try:
                    decoded += content.decode(encoding or 'utf-8')
                except (UnicodeDecodeError, LookupError):
                    decoded += content.decode('latin-1')
            else:
                decoded += content
        return decoded

    def is_relevant_email(self, subject: str, from_address: str) -> bool:
        """
        Check if email is relevant for processing.

        Filters by:
        - Subject keywords
        - Known senders
        """
        subject_lower = subject.lower()
        from_lower = from_address.lower()

        # Check subject keywords
        for keyword in EMAIL_KEYWORDS:
            if keyword in subject_lower:
                return True

        # Check if from known sender (optional - can be enhanced)
        # For now, accept all emails with relevant keywords

        return False

    def save_attachment(self, payload: EmailMessage, filename: str) -> Path:
        """
        Save attachment to Inbox folder.

        Args:
            payload: Email message payload
            filename: Attachment filename

        Returns:
            Path to saved file
        """
        # Generate unique filename if exists
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"email_{timestamp}_{filename}"
        file_path = self.inbox_dir / safe_filename

        # Save file
        with open(file_path, 'wb') as f:
            f.write(payload.get_payload(decode=True))

        logger.info(f"📎 Attachment saved: {file_path.name}")
        return file_path

    def process_email(self, mail, msg_id: str, msg: email.message.Message):
        """
        Process a single email and extract attachments.

        Args:
            mail: IMAP connection
            msg_id: Email message ID
            msg: Parsed email message
        """
        subject = self.decode_subject(msg.get('Subject', ''))
        from_address = msg.get('From', '')
        date_str = msg.get('Date', '')

        logger.info(f"\n📧 Processing email:")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   From: {from_address}")
        logger.info(f"   Date: {date_str}")

        # Check if email is relevant
        if not self.is_relevant_email(subject, from_address):
            logger.info("   ⏭️  Skipping - not relevant")
            return

        logger.info("   ✅ Email is relevant - checking attachments...")

        attachments_saved = []

        # Walk through email parts
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))

            # Look for attachments
            if 'attachment' in content_disposition.lower():
                filename = self.decode_filename(part.get_filename())

                if filename:
                    # Check if attachment type is supported
                    ext = Path(filename).suffix.lower()
                    if ext in ATTACHMENT_EXTENSIONS:
                        try:
                            file_path = self.save_attachment(part, filename)
                            attachments_saved.append(file_path)
                            logger.info(f"   ✅ Saved: {filename}")
                        except Exception as e:
                            logger.error(f"   ❌ Failed to save {filename}: {e}")
                    else:
                        logger.info(f"   ⏭️  Skipping unsupported attachment: {filename}")

        # Summary
        if attachments_saved:
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Email processed successfully")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Attachments saved: {len(attachments_saved)}")
            for path in attachments_saved:
                logger.info(f"   - {path.name}")
            logger.info(f"{'='*60}\n")

            # Log to email_log.txt
            self.log_email_received(subject, from_address, attachments_saved)
        else:
            logger.info(f"   ⚠️  No relevant attachments found")

    def log_email_received(self, subject: str, from_address: str, attachments: list):
        """Log received email to email_log.txt."""
        log_path = self.vault_path / 'email_log.txt'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_entry = f"""
{'='*60}
✅ EMAIL RECEIVED
{'='*60}
Timestamp: {timestamp}
From: {from_address}
Subject: {subject}
Attachments: {len(attachments)}
Files: {', '.join([p.name for p in attachments])}
{'='*60}
"""

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def check_inbox(self):
        """Check Gmail inbox for new emails."""
        try:
            # Connect to Gmail
            mail = self.connect()

            # Select inbox
            mail.select('inbox')

            # Search for unread emails from last check
            since_date = self.last_check.strftime('%d-%b-%Y')
            status, messages = mail.search(None, f'(SINCE "{since_date}")')

            if status != 'OK':
                logger.warning("⚠️  Search failed")
                mail.close()
                mail.logout()
                return

            # Get list of message IDs
            msg_ids = messages[0].split()

            if not msg_ids:
                logger.info("📬 No new emails since last check")
            else:
                logger.info(f"📬 Found {len(msg_ids)} email(s) since last check")

                # Process each email
                for msg_id in msg_ids:
                    try:
                        # Skip if already processed
                        if msg_id in self.processed_emails:
                            continue

                        # Fetch email
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')

                        if status == 'OK':
                            # Parse email
                            msg = email.message_from_bytes(msg_data[0][1])
                            self.process_email(mail, msg_id, msg)

                            # Mark as processed
                            self.processed_emails.add(msg_id)

                            # Mark as read in Gmail
                            mail.store(msg_id, '+FLAGS', '\\Seen')

                    except Exception as e:
                        logger.error(f"❌ Error processing email {msg_id}: {e}")

            # Close connection
            mail.close()
            mail.logout()

            # Update last check time
            self.last_check = datetime.now()

        except Exception as e:
            logger.error(f"❌ Error checking inbox: {e}")
            # Wait a bit before retrying
            time.sleep(30)

    def start(self):
        """Start the Gmail watcher loop."""
        logger.info("=" * 60)
        logger.info("📧 Gmail Watcher Starting")
        logger.info("=" * 60)
        logger.info(f"Monitoring: {GMAIL_ADDRESS}")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info(f"Keywords: {', '.join(EMAIL_KEYWORDS)}")
        logger.info(f"Attachment types: {', '.join(ATTACHMENT_EXTENSIONS)}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        print(f"\n{'='*60}")
        print(f"📧 Gmail Watcher Active")
        print(f"{'='*60}")
        print(f"Monitoring: {GMAIL_ADDRESS}")
        print(f"Check interval: {self.check_interval}s")
        print(f"Keywords: {', '.join(EMAIL_KEYWORDS)}")
        print(f"Attachment types: {', '.join(ATTACHMENT_EXTENSIONS)}")
        print(f"\nℹ️  How it works:")
        print(f"  1. Emails with CSV attachments are detected")
        print(f"  2. Attachments saved to Hydrology-Vault/Inbox/")
        print(f"  3. CSV Watcher will automatically process files")
        print(f"{'='*60}\n")

        try:
            while True:
                logger.info(f"\n🔍 Checking inbox... ({datetime.now().strftime('%H:%M:%S')})")
                self.check_inbox()

                # Wait until next check
                for _ in range(self.check_interval):
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Gmail Watcher stopped by user")


def main():
    """Main entry point."""
    import sys

    # Default vault path
    default_vault = Path(__file__).parent.parent / 'Hydrology-Vault'
    vault_path = sys.argv[1] if len(sys.argv) > 1 else str(default_vault)

    # Create and start watcher
    watcher = GmailWatcher(vault_path, check_interval=60)
    watcher.start()


if __name__ == "__main__":
    main()
