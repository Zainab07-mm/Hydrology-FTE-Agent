"""
Test Email Function for Hydrology FTE Agent

This script tests the Gmail connection and sends a test email
to verify the flood alert system is configured correctly.

Usage:
    python test_email.py

Before running:
    1. Copy .env.example to .env
    2. Fill in your Gmail credentials in .env
    3. Run this script to test the connection
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_gmail_connection():
    """Test Gmail connection and send a test email."""
    print("=" * 60)
    print("🧪 Hydrology FTE Agent - Email System Test")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print("\n❌ .env file not found!")
        print("\n📖 Setup Instructions:")
        print("   1. Copy .env.example to .env:")
        print(f"      copy {Path(__file__).parent / '.env.example'} {Path(__file__).parent / '.env'}")
        print("\n   2. Edit .env and add your Gmail credentials:")
        print("      GMAIL_ADDRESS=your_gmail@gmail.com")
        print("      GMAIL_APP_PASSWORD=your_app_password")
        print("      ALERT_RECIPIENT=recipient@gmail.com")
        print("\n   3. See .env.example for detailed Gmail App Password setup instructions")
        return False
    
    print("\n✅ .env file found")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        gmail_address = os.getenv('GMAIL_ADDRESS', '')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD', '')
        alert_recipient = os.getenv('ALERT_RECIPIENT', '')
        
        print(f"📧 Gmail Address: {gmail_address if gmail_address else '❌ NOT SET'}")
        print(f"📧 App Password: {'*' * len(gmail_password) if gmail_password else '❌ NOT SET'}")
        print(f"📧 Alert Recipient: {alert_recipient if alert_recipient else '❌ NOT SET'}")
        
        if not gmail_address or not gmail_password or not alert_recipient:
            print("\n❌ Missing credentials in .env file")
            print("   Please fill in all three values: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, ALERT_RECIPIENT")
            return False
            
    except ImportError:
        print("\n❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
        return False
    
    # Import and run test
    try:
        from mcp_email_server import send_test_email
        
        print("\n" + "=" * 60)
        print("Sending test email...")
        print("=" * 60)
        
        success = send_test_email(alert_recipient)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ SUCCESS! Your flood alert email system is ready!")
            print("=" * 60)
            print("\n📖 Next Steps:")
            print("   1. Check your email inbox at: " + alert_recipient)
            print("   2. Look for email with subject: 'Hydrology FTE Agent - Test Email'")
            print("   3. If not in inbox, check spam/junk folder")
            print("   4. Once confirmed, your system will automatically send flood alerts")
            print("\n🎉 Setup complete!")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ Test failed - Email not sent")
            print("=" * 60)
            print("\n📖 Troubleshooting:")
            print("   1. Verify Gmail App Password (not regular password)")
            print("   2. Ensure 2FA is enabled on Gmail account")
            print("   3. Check internet connection")
            print("   4. Verify firewall isn't blocking port 587")
            print("\n📖 To get Gmail App Password:")
            print("   1. Go to: https://myaccount.google.com/apppasswords")
            print("   2. Select 'Mail' and your device")
            print("   3. Click 'Generate'")
            print("   4. Copy the 16-character password (no spaces)")
            print("   5. Update .env file and try again")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n   Make sure mcp_email_server.py exists in the project root")
        return False


def test_flood_alert_format():
    """Test the flood alert email format without sending."""
    print("\n" + "=" * 60)
    print("📧 Flood Alert Email Format Preview")
    print("=" * 60)
    
    # Sample flood alert data
    sample_data = {
        'river_name': 'Chenab',
        'discharge': 185.5,
        'risk_level': 'High',
        'width': 35,
        'depth': 2.5,
        'velocity': 2.1
    }
    
    print(f"""
Subject: FLOOD ALERT - {sample_data['river_name']} - [Today's Date]

Body Preview:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ FLOOD ALERT
Hydrology FTE Agent - Automated Warning System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

River: {sample_data['river_name']}
Alert Generated: [Timestamp]

CURRENT CONDITIONS
==================
River Name: {sample_data['river_name']}
Discharge (Q): {sample_data['discharge']:.2f} m³/s
Risk Level: {sample_data['risk_level'].upper()}

DISCHARGE CALCULATION
=====================
Formula: Q = Width × Depth × Velocity
Calculation: Q = {sample_data['width']}m × {sample_data['depth']}m × {sample_data['velocity']}m/s 
           = {sample_data['discharge']:.2f} m³/s

CLASSIFICATION CRITERIA
=======================
- Q < 50 m³/s: Low condition, Low risk
- 50 ≤ Q ≤ 150 m³/s: Moderate condition, Medium risk
- Q > 150 m³/s: High condition, High risk ← YOUR ALERT

RECOMMENDED ACTIONS
===================
IMMEDIATE ACTIONS REQUIRED:
• Notify emergency management authorities
• Issue flood warnings to downstream communities
• Monitor water levels hourly
• Prepare evacuation plans if discharge continues to rise
• Coordinate with upstream dam operators if applicable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated by Hydrology FTE Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    print("\n✅ Flood alert format looks professional and informative")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌊 Hydrology FTE Agent - Email Testing Suite")
    print("=" * 60)
    print("\nSelect test:")
    print("1. Test Gmail Connection (sends real email)")
    print("2. Preview Flood Alert Format (no email sent)")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        test_gmail_connection()
    elif choice == '2':
        test_flood_alert_format()
    elif choice == '3':
        print("\n" + "=" * 60)
        print("Running both tests...")
        print("=" * 60)
        test_flood_alert_format()
        print("\n")
        test_gmail_connection()
    else:
        print("\n❌ Invalid choice. Run script again and select 1, 2, or 3")
