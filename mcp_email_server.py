"""
MCP Email Server for Hydrology FTE Agent

This module provides email sending capabilities via Gmail SMTP.
It reads credentials from environment variables (loaded from .env file).

Requirements:
    - Gmail account with App Password enabled
    - .env file with GMAIL_ADDRESS and GMAIL_APP_PASSWORD

Setup Instructions:
    1. Create .env file in project root
    2. Add your Gmail credentials (see .env.example)
    3. Enable 2FA on Gmail and generate App Password
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import logging
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCPEmailServer')

# Email configuration
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')
ALERT_RECIPIENT = os.getenv('ALERT_RECIPIENT', '')

# SMTP configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # TLS port


def send_flood_alert(river_name, discharge, risk_level, recipient_email=None, width=None, depth=None, velocity=None):
    """
    Send a flood alert email via Gmail SMTP.

    Args:
        river_name: Name of the river (e.g., "Chenab")
        discharge: Discharge value in m³/s
        risk_level: Risk level (Low, Medium, High)
        recipient_email: Email address to send alert to (uses ALERT_RECIPIENT from .env if None)
        width: River width in meters (optional, for formula display)
        depth: River depth in meters (optional, for formula display)
        velocity: River velocity in m/s (optional, for formula display)

    Returns:
        True if email sent successfully, False otherwise
    """
    # Use default recipient if not specified
    if recipient_email is None:
        recipient_email = ALERT_RECIPIENT

    # Validate inputs
    if not river_name or not discharge:
        logger.error("Missing required parameters: river_name or discharge")
        log_email_attempt(river_name, discharge, recipient_email, False, "Missing parameters")
        return False

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not configured. Check .env file.")
        log_email_attempt(river_name, discharge, recipient_email, False, "Gmail credentials not configured")
        return False

    if not recipient_email:
        logger.error("No recipient email address provided")
        log_email_attempt(river_name, discharge, recipient_email, False, "No recipient email")
        return False

    # Generate timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Create email subject
    subject = f"FLOOD ALERT - {river_name} - {date_str}"

    # Calculate formula if dimensions provided
    if width is not None and depth is not None and velocity is not None:
        formula_text = f"Q = {width}m × {depth}m × {velocity}m/s = {discharge:.2f} m³/s"
    else:
        formula_text = f"Q = Width × Depth × Velocity = {discharge:.2f} m³/s"

    # Determine recommended action based on risk level
    if risk_level == "High":
        recommended_action = """
<strong>IMMEDIATE ACTIONS REQUIRED:</strong>
<ul>
  <li>Notify emergency management authorities</li>
  <li>Issue flood warnings to downstream communities</li>
  <li>Monitor water levels hourly</li>
  <li>Prepare evacuation plans if discharge continues to rise</li>
  <li>Coordinate with upstream dam operators if applicable</li>
</ul>
"""
    elif risk_level == "Medium":
        recommended_action = """
<strong>RECOMMENDED ACTIONS:</strong>
<ul>
  <li>Increase monitoring frequency</li>
  <li>Review flood preparedness plans</li>
  <li>Notify stakeholders of elevated conditions</li>
  <li>Check weather forecasts for upstream areas</li>
</ul>
"""
    else:
        recommended_action = """
<strong>ACTIONS:</strong>
<ul>
  <li>Continue routine monitoring</li>
  <li>Document current conditions</li>
  <li>Update historical records</li>
</ul>
"""

    # Create HTML email body
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #d9534f; color: white; padding: 20px; text-align: center; }}
        .alert-box {{ border: 2px solid #d9534f; background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .data-table th {{ background-color: #f4f4f4; font-weight: bold; }}
        .highlight {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; margin-top: 30px; }}
        .risk-high {{ color: #d9534f; font-weight: bold; }}
        .risk-medium {{ color: #f0ad4e; font-weight: bold; }}
        .risk-low {{ color: #5cb85c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ FLOOD ALERT</h1>
            <p>Hydrology FTE Agent - Automated Warning System</p>
        </div>

        <div class="alert-box">
            <h2>River: {river_name}</h2>
            <p><strong>Alert Generated:</strong> {timestamp}</p>
        </div>

        <h3>📊 Current Conditions</h3>
        <table class="data-table">
            <tr>
                <th>Parameter</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>River Name</td>
                <td>{river_name}</td>
            </tr>
            <tr>
                <td>Discharge (Q)</td>
                <td><strong>{discharge:.2f} m³/s</strong></td>
            </tr>
            <tr>
                <td>Risk Level</td>
                <td class="risk-{risk_level.lower()}">{risk_level.upper()}</td>
            </tr>
        </table>

        <h3>🧮 Discharge Calculation</h3>
        <div class="highlight">
            <p><strong>Formula:</strong> Q = Width × Depth × Velocity</p>
            <p><strong>Calculation:</strong> {formula_text}</p>
        </div>

        <h3>📋 Classification Criteria</h3>
        <table class="data-table">
            <tr>
                <th>Discharge Range</th>
                <th>Condition</th>
                <th>Risk Level</th>
            </tr>
            <tr>
                <td>Q &lt; 50 m³/s</td>
                <td>Low</td>
                <td class="risk-low">Low</td>
            </tr>
            <tr>
                <td>50 ≤ Q ≤ 150 m³/s</td>
                <td>Moderate</td>
                <td class="risk-medium">Medium</td>
            </tr>
            <tr>
                <td>Q &gt; 150 m³/s</td>
                <td>High</td>
                <td class="risk-high">High</td>
            </tr>
        </table>

        <h3>✅ Recommended Actions</h3>
        {recommended_action}

        <div class="highlight">
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Verify this alert with manual measurements if possible</li>
                <li>Share this information with relevant stakeholders</li>
                <li>Continue monitoring for changes in water levels</li>
            </ul>
        </div>

        <div class="footer">
            <p><em>This is an automated message generated by the Hydrology FTE Agent.</em></p>
            <p><em>For questions or support, contact your system administrator.</em></p>
            <p><em>Generated: {timestamp}</em></p>
        </div>
    </div>
</body>
</html>
"""

    # Also create plain text version
    text_body = f"""
FLOOD ALERT - {river_name}
Generated: {timestamp}

CURRENT CONDITIONS
==================
River Name: {river_name}
Discharge (Q): {discharge:.2f} m³/s
Risk Level: {risk_level.upper()}

DISCHARGE CALCULATION
=====================
Formula: Q = Width × Depth × Velocity
Calculation: {formula_text}

CLASSIFICATION CRITERIA
=======================
- Q < 50 m³/s: Low condition, Low risk
- 50 ≤ Q ≤ 150 m³/s: Moderate condition, Medium risk
- Q > 150 m³/s: High condition, High risk

RECOMMENDED ACTIONS
===================
{recommended_action.replace('<strong>', '').replace('</strong>', '').replace('<ul>', '').replace('</ul>', '').replace('<li>', '- ').replace('</li>', '')}

---
This is an automated message generated by the Hydrology FTE Agent.
For questions or support, contact your system administrator.
"""

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email

        # Attach plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Connect to Gmail SMTP server and send
        logger.info(f"Connecting to Gmail SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable encryption

        logger.info(f"Authenticating...")
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

        logger.info(f"Sending email to {recipient_email}...")
        server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
        server.quit()

        logger.info(f"✅ Email sent successfully to {recipient_email}")
        log_email_attempt(river_name, discharge, recipient_email, True, "Sent successfully")

        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP Authentication failed. Check Gmail App Password.")
        log_email_attempt(river_name, discharge, recipient_email, False, "SMTP Authentication failed")
        return False

    except smtplib.SMTPConnectError:
        logger.error("❌ Failed to connect to Gmail SMTP server.")
        log_email_attempt(river_name, discharge, recipient_email, False, "SMTP Connection failed")
        return False

    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP error occurred: {e}")
        log_email_attempt(river_name, discharge, recipient_email, False, f"SMTP error: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        log_email_attempt(river_name, discharge, recipient_email, False, f"Error: {e}")
        return False


def log_email_attempt(river_name, discharge, recipient_email, success, message):
    """
    Log email attempt to Hydrology-Vault/email_log.txt

    Args:
        river_name: Name of the river
        discharge: Discharge value
        recipient_email: Email recipient
        success: True if sent successfully, False otherwise
        message: Additional message or error description
    """
    log_path = Path(__file__).parent / 'Hydrology-Vault' / 'email_log.txt'

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "✅ SUCCESS" if success else "❌ FAILED"

    log_entry = f"""
{'='*60}
{status} - Email Alert
{'='*60}
Timestamp: {timestamp}
River: {river_name}
Discharge: {discharge:.2f} m³/s
Recipient: {recipient_email}
Result: {message}
{'='*60}
"""

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def send_test_email(recipient_email=None):
    """
    Send a test email to verify Gmail connection.

    Args:
        recipient_email: Email address to send test to (uses ALERT_RECIPIENT from .env if None)

    Returns:
        True if test successful, False otherwise
    """
    if recipient_email is None:
        recipient_email = ALERT_RECIPIENT

    print("=" * 60)
    print("🧪 Testing Gmail Connection")
    print("=" * 60)

    if not GMAIL_ADDRESS:
        print("❌ GMAIL_ADDRESS not set in .env file")
        return False

    if not GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD not set in .env file")
        return False

    if not recipient_email:
        print("❌ ALERT_RECIPIENT not set in .env file")
        return False

    print(f"📧 From: {GMAIL_ADDRESS}")
    print(f"📧 To: {recipient_email}")
    print(f"📧 SMTP: {SMTP_SERVER}:{SMTP_PORT}")

    # Create test email
    subject = f"Hydrology FTE Agent - Test Email {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success">
            <h2>✅ Test Email Successful!</h2>
            <p>Your Hydrology FTE Agent email system is working correctly.</p>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li>From: {GMAIL_ADDRESS}</li>
                <li>To: {recipient_email}</li>
            </ul>
        </div>
        <div class="footer">
            <p><em>Generated by Hydrology FTE Agent - MCP Email Server</em></p>
        </div>
    </div>
</body>
</html>
"""

    text_body = f"""
Hydrology FTE Agent - Test Email

This is a test email to verify your Gmail connection is working correctly.

Test Details:
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: {GMAIL_ADDRESS}
- To: {recipient_email}

If you received this email, your flood alert system is ready!

---
Generated by Hydrology FTE Agent - MCP Email Server
"""

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = recipient_email

        # Attach versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send
        print("\n📤 Sending test email...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
        server.quit()

        print("\n✅ SUCCESS! Test email sent successfully!")
        print(f"   Check inbox at: {recipient_email}")
        print("\n🎉 Your flood alert email system is ready!")

        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\n📖 Troubleshooting:")
        print("   1. Check that .env file exists with correct credentials")
        print("   2. Verify Gmail App Password (not regular password)")
        print("   3. Ensure 2FA is enabled on Gmail account")
        print("   4. Check firewall/antivirus isn't blocking SMTP")
        return False


if __name__ == "__main__":
    # Test the email server
    send_test_email()
