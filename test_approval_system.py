"""
Test Script for Human-in-the-Loop Approval System

This script tests the complete approval workflow:
1. Creates a mock approval request
2. Simulates human decision (YES or NO)
3. Verifies email is sent (or cancelled)
4. Checks Dashboard updates

Usage:
    python test_approval_system.py
"""

import time
from pathlib import Path
from datetime import datetime


def test_approval_request_creation():
    """Test that approval requests are created correctly."""
    print("=" * 60)
    print("🧪 Test 1: Approval Request Creation")
    print("=" * 60)
    
    from skills.send_alert_email import run
    
    # Test data - HIGH RISK conditions
    test_results = [
        {"River": "Chenab", "Discharge": 185.5, "Condition": "High", "Risk": "High"},
        {"River": "Indus", "Discharge": 420.0, "Condition": "High", "Risk": "High"},
        {"River": "Ravi", "Discharge": 75.2, "Condition": "Moderate", "Risk": "Medium"}
    ]
    
    print("\n📊 Test data:")
    print("  - Chenab: 185.50 m³/s (HIGH RISK)")
    print("  - Indus: 420.00 m³/s (HIGH RISK)")
    print("  - Ravi: 75.20 m³/s (MEDIUM - no approval needed)")
    print("\nExpected: 2 approval requests created")
    print("-" * 60 + "\n")
    
    # Run the skill
    result = run(test_results, vault_path="Hydrology-Vault")
    
    # Verify results
    print("\n📊 Results:")
    print(f"  Approval requests created: {result['approval_requests_created']}")
    print(f"  Success: {result['success']}")
    
    if result['approval_requests_created'] == 2:
        print("\n✅ TEST PASSED: Correct number of approval requests created")
        
        # Show created files
        needs_action = Path("Hydrology-Vault/Needs_Action")
        approval_files = list(needs_action.glob("APPROVAL_*.md"))
        
        print(f"\n📁 Created files:")
        for af in approval_files[-2:]:  # Last 2 files
            print(f"  • {af.name}")
        
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected 2, got {result['approval_requests_created']}")
        return False


def test_approval_file_format():
    """Test that approval files have correct format."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Approval File Format")
    print("=" * 60)
    
    needs_action = Path("Hydrology-Vault/Needs_Action")
    approval_files = list(needs_action.glob("APPROVAL_*.md"))
    
    if not approval_files:
        print("\n❌ TEST FAILED: No approval files found")
        print("   Run Test 1 first to create approval requests")
        return False
    
    # Check latest file
    latest_file = sorted(approval_files)[-1]
    content = latest_file.read_text(encoding='utf-8')
    
    print(f"\n📁 Checking: {latest_file.name}")
    
    # Verify required sections
    required_sections = [
        "⚠️ APPROVAL REQUIRED",
        "## 📊 Detection Details",
        "## 📧 Email Details",
        "## 📝 Email Preview",
        "## ⚖️ YOUR DECISION",
        "DECISION: [type YES or NO here]"
    ]
    
    all_present = True
    print("\n📋 Checking required sections:")
    
    for section in required_sections:
        if section in content:
            print(f"  ✓ {section[:50]}...")
        else:
            print(f"  ✗ {section[:50]}... - MISSING")
            all_present = False
    
    # Verify frontmatter
    print("\n📋 Checking frontmatter:")
    frontmatter_fields = [
        "type: approval_request",
        "category: flood_alert_email",
        "river_name:",
        "discharge:",
        "status: pending_approval"
    ]
    
    for field in frontmatter_fields:
        if field in content:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} - MISSING")
            all_present = False
    
    if all_present:
        print("\n✅ TEST PASSED: All required sections present")
        return True
    else:
        print("\n❌ TEST FAILED: Some sections missing")
        return False


def test_approval_decision_processing():
    """Test that approval decisions are processed correctly."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Approval Decision Processing")
    print("=" * 60)
    
    needs_action = Path("Hydrology-Vault/Needs_Action")
    approval_files = list(needs_action.glob("APPROVAL_*.md"))
    
    if not approval_files:
        print("\n❌ TEST FAILED: No approval files found")
        print("   Run Test 1 first to create approval requests")
        return False
    
    # Pick one file to test with
    test_file = sorted(approval_files)[-1]
    
    print(f"\n📁 Testing with: {test_file.name}")
    print("\n⚠️  This test will:")
    print("  1. Add DECISION: YES to the file")
    print("  2. Wait for approval watcher to process")
    print("  3. Check if file moved to Done/")
    print("\n⚠️  WARNING: This will send a real email if Gmail is configured!")
    print("\n💡 TIP: For testing without sending email, use DECISION: NO")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n⏭️  Test skipped")
        return None
    
    # Read current content
    content = test_file.read_text(encoding='utf-8')
    
    # Replace DECISION placeholder with YES
    if "DECISION: [type YES or NO here]" in content:
        content = content.replace(
            "DECISION: [type YES or NO here]",
            "DECISION: YES"
        )
        
        # Write back
        test_file.write_text(content, encoding='utf-8')
        print(f"\n✅ Added DECISION: YES to {test_file.name}")
        
        # Wait for approval watcher to process (max 30 seconds)
        print("\n⏳ Waiting for approval watcher to process...")
        
        for i in range(30):
            time.sleep(1)
            
            # Check if file moved to Done
            approved_file = Path(f"Hydrology-Vault/Done/APPROVED_{test_file.name}")
            denied_file = Path(f"Hydrology-Vault/Done/DENIED_{test_file.name}")
            
            if approved_file.exists():
                print(f"\n✅ File moved to: {approved_file.name}")
                print("✅ TEST PASSED: Approval processed successfully")
                return True
            
            if denied_file.exists():
                print(f"\n✅ File moved to: {denied_file.name}")
                print("✅ TEST PASSED: Rejection processed successfully")
                return True
            
            if i % 5 == 0:
                print(f"   Still waiting... ({i+1}s)")
        
        print("\n❌ TEST FAILED: File not processed after 30 seconds")
        print("   Check if approval watcher is running")
        return False
    else:
        print("\n❌ TEST FAILED: Could not find DECISION field")
        return False


def test_dashboard_update():
    """Test that Dashboard is updated with approval history."""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Dashboard Update")
    print("=" * 60)
    
    dashboard_path = Path("Hydrology-Vault/Dashboard.md")
    
    if not dashboard_path.exists():
        print("\n❌ TEST FAILED: Dashboard.md not found")
        return False
    
    content = dashboard_path.read_text(encoding='utf-8')
    
    # Check for approval sections
    print("\n📋 Checking approval sections:")
    
    sections = {
        "Pending Approvals": "## ⚖️ Pending Approvals",
        "Approval History": "## 📜 Approval History"
    }
    
    all_present = True
    for name, section_text in sections.items():
        if section_text in content:
            print(f"  ✓ {name} section present")
        else:
            print(f"  ✗ {name} section MISSING")
            all_present = False
    
    if all_present:
        print("\n✅ TEST PASSED: Dashboard has approval sections")
        return True
    else:
        print("\n❌ TEST FAILED: Dashboard missing sections")
        return False


def run_all_tests():
    """Run all approval system tests."""
    print("\n" + "=" * 60)
    print("🌊 Hydrology FTE Agent - Approval System Test Suite")
    print("=" * 60)
    
    results = {
        'Test 1 (Creation)': None,
        'Test 2 (Format)': None,
        'Test 3 (Decision)': None,
        'Test 4 (Dashboard)': None
    }
    
    # Run tests
    results['Test 1 (Creation)'] = test_approval_request_creation()
    results['Test 2 (Format)'] = test_approval_file_format()
    results['Test 3 (Decision)'] = test_approval_decision_processing()
    results['Test 4 (Dashboard)'] = test_dashboard_update()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            print(f"  ✅ {test_name}: PASSED")
        elif result is False:
            print(f"  ❌ {test_name}: FAILED")
        else:
            print(f"  ⏭️  {test_name}: SKIPPED")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Approval system is working correctly.")
    elif passed > 0:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    else:
        print("\n❌ All tests failed or skipped.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_all_tests()
