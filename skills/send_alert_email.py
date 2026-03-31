"""
Send Alert Email Skill for Hydrology FTE Agent

This skill creates HUMAN-IN-THE-LOOP approval requests for flood alert emails.
When HIGH RISK conditions are detected, it creates an approval request file
and waits for human decision before sending any emails.

Workflow:
1. Detect HIGH RISK condition
2. Create APPROVAL_[river]_[timestamp].md file
3. Wait for human to edit file with DECISION: YES or NO
4. Approval watcher will process the decision
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import mcp_email_server
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed")


def run(results, df=None, vault_path=None):
    """
    Create approval requests for HIGH RISK flood alert emails.
    
    Instead of sending emails immediately, this creates approval request files
    that require human decision before any email is sent.

    Args:
        results: List of dicts from analyze_flow_condition with River, Discharge, Condition, Risk
        df: Optional DataFrame with original measurements (Width_m, Depth_m, Velocity_mps)
        vault_path: Path to Hydrology-Vault folder

    Returns:
        dict with approval_requests_created count and details
    """
    try:
        # Validate results
        if not results:
            print("⚠️  No results to process for email alerts")
            return {
                'approval_requests_created': 0,
                'success': False,
                'message': 'No results provided'
            }

        # Validate vault_path
        if not vault_path:
            vault_path = Path(__file__).parent.parent / 'Hydrology-Vault'
        
        vault_path = Path(vault_path)
        needs_action_dir = vault_path / 'Needs_Action'
        needs_action_dir.mkdir(exist_ok=True)

        print("\n📧 Checking for HIGH RISK conditions...")
        
        approval_requests = 0
        alert_details = []

        # Get recipient from .env
        alert_recipient = os.getenv('ALERT_RECIPIENT', 'recipient@gmail.com')

        # Check each river for high risk
        for result in results:
            river_name = result.get('River', 'Unknown')
            discharge = result.get('Discharge', 0)
            risk_level = result.get('Risk', 'Unknown')
            condition = result.get('Condition', 'Unknown')

            print(f"\n  Checking {river_name}:")
            print(f"    Discharge: {discharge:.2f} m³/s")
            print(f"    Condition: {condition}")
            print(f"    Risk Level: {risk_level}")

            # Only create approval request for HIGH risk
            if risk_level.lower() == 'high':
                print(f"    ⚠️  HIGH RISK DETECTED - Creating approval request...")

                # Get river dimensions from DataFrame if available
                width = depth = velocity = None
                if df is not None:
                    river_row = df[df['River'] == river_name]
                    if not river_row.empty:
                        width = river_row['Width_m'].values[0] if 'Width_m' in river_row.columns else None
                        depth = river_row['Depth_m'].values[0] if 'Depth_m' in river_row.columns else None
                        velocity = river_row['Velocity_mps'].values[0] if 'Velocity_mps' in river_row.columns else None

                # Create approval request file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                approval_filename = f"APPROVAL_{river_name}_{timestamp}.md"
                approval_path = needs_action_dir / approval_filename

                # Generate email preview
                if width and depth and velocity:
                    formula_text = f"Q = {width}m × {depth}m × {velocity}m/s = {discharge:.2f} m³/s"
                else:
                    formula_text = f"Q = Width × Depth × Velocity = {discharge:.2f} m³/s"

                email_preview = f"""
Subject: FLOOD ALERT - {river_name} - {datetime.now().strftime('%Y-%m-%d')}

⚠️ FLOOD ALERT
Hydrology FTE Agent - Automated Warning System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

River: {river_name}
Discharge: {discharge:.2f} m³/s
Risk Level: HIGH

DISCHARGE CALCULATION
=====================
Formula: Q = Width × Depth × Velocity
Calculation: {formula_text}

CLASSIFICATION CRITERIA
=======================
- Q < 50 m³/s: Low condition, Low risk
- 50 ≤ Q ≤ 150 m³/s: Moderate condition, Medium risk
- Q > 150 m³/s: High condition, High risk ← CURRENT CONDITION

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
"""

                # Create approval request content
                approval_content = f"""---
type: approval_request
category: flood_alert_email
river_name: {river_name}
discharge: {discharge}
risk_level: {risk_level}
recipient: {alert_recipient}
created: {datetime.now().isoformat()}
status: pending_approval
---

# ⚠️ APPROVAL REQUIRED — Flood Alert Email

**The AI wants to send a flood alert email.**

---

## 📊 Detection Details

| Parameter | Value |
|-----------|-------|
| **River Name** | {river_name} |
| **Discharge** | {discharge:.2f} m³/s |
| **Risk Level** | **HIGH** |
| **Condition** | {condition} |
| **Detection Time** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

---

## 📧 Email Details

**Proposed Recipient:** `{alert_recipient}`

**Email Subject:** `FLOOD ALERT - {river_name} - {datetime.now().strftime('%Y-%m-%d')}`

---

## 📝 Email Preview

```
{email_preview}
```

---

## 🧮 Original Data

**Source Formula:** Q = Width × Depth × Velocity

"""
                
                if width and depth and velocity:
                    approval_content += f"""
| Measurement | Value |
|-------------|-------|
| Width | {width} m |
| Depth | {depth} m |
| Velocity | {velocity} m/s |
| **Calculated Q** | **{discharge:.2f} m³/s** |
"""
                else:
                    approval_content += f"""
*Original measurements not available in current dataset.*
"""

                approval_content += f"""

---

## ⚖️ YOUR DECISION

**Type your decision below and save this file:**

```
DECISION: [type YES or NO here]
```

**Options:**
- **YES** = Send the flood alert email now
- **NO** = Cancel, do not send the email

---

## ℹ️ What Happens Next

1. **If you type YES:**
   - The Approval Watcher will detect your decision
   - The flood alert email will be sent to {alert_recipient}
   - This file will be moved to /Done/ folder
   - The email will be logged in email_log.txt

2. **If you type NO:**
   - The email will NOT be sent
   - This file will be moved to /Done/ folder with "rejected" status
   - The decision will be logged for audit purposes

3. **If you take no action:**
   - The approval request will remain in /Needs_Action/
   - No email will be sent
   - The system will continue monitoring for new high-risk conditions

---

*Generated by Hydrology FTE Agent - Human-in-the-Loop System*
"""

                # Save approval request file
                approval_path.write_text(approval_content, encoding='utf-8')
                
                print(f"    ✅ Approval request created: {approval_filename}")
                print(f"    📁 Location: {approval_path}")
                print(f"    ⏳ Waiting for human decision...")
                
                approval_requests += 1
                alert_details.append({
                    'river': river_name,
                    'discharge': discharge,
                    'approval_file': str(approval_path),
                    'status': 'pending'
                })
            else:
                print(f"    ✓ No alert needed (risk level: {risk_level})")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Flood Alert Approval Summary")
        print("=" * 60)
        print(f"Total rivers analyzed: {len(results)}")
        print(f"High risk detected: {approval_requests}")
        print(f"Approval requests created: {approval_requests}")
        
        if approval_requests > 0:
            print(f"\n⚠️  Awaiting human approval for {approval_requests} flood alert(s)")
            print(f"   Check Hydrology-Vault/Needs_Action/ for approval files")
            print(f"   Edit file with DECISION: YES or NO to proceed")
        else:
            print(f"\nℹ️  No flood alerts required (all rivers at low/medium risk)")

        print("=" * 60)

        return {
            'approval_requests_created': approval_requests,
            'emails_pending': approval_requests,
            'success': True,
            'details': alert_details,
            'message': f'Created {approval_requests} approval request(s) awaiting human decision'
        }

    except Exception as e:
        print(f"❌ Error creating approval requests: {e}")
        import traceback
        traceback.print_exc()
        return {
            'approval_requests_created': 0,
            'success': False,
            'message': f'Error: {e}'
        }


if __name__ == "__main__":
    # Test the send_alert_email skill
    print("=" * 50)
    print("🧪 Testing Send Alert Email Skill (HITL Mode)")
    print("=" * 50)

    # Test data - simulate HIGH RISK conditions
    test_results = [
        {"River": "Chenab", "Discharge": 180.5, "Condition": "High", "Risk": "High"},
        {"River": "Indus", "Discharge": 420.0, "Condition": "High", "Risk": "High"},
        {"River": "Ravi", "Discharge": 75.2, "Condition": "Moderate", "Risk": "Medium"},
        {"River": "Jhelum", "Discharge": 35.0, "Condition": "Low", "Risk": "Low"}
    ]

    print("\nTest scenario: 2 HIGH RISK, 1 MEDIUM, 1 LOW")
    print("Expected: 2 approval requests created (Chenab and Indus)")
    print("=" * 50 + "\n")

    result = run(test_results, vault_path="Hydrology-Vault")

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Approval requests created: {result['approval_requests_created']}")
    print(f"  Success: {result['success']}")
    print(f"  Message: {result['message']}")
    print("=" * 50)
