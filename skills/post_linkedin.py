"""
LinkedIn Auto-Posting Skill for Hydrology FTE Agent

This skill automatically generates and posts LinkedIn content 
to promote Zainab's hydrology consulting services.

TWO MODES:
Mode A: Real LinkedIn API (when LINKEDIN_ACCESS_TOKEN exists)
Mode B: Smart workaround fallback (when token not available)

The system auto-detects which mode to use based on .env configuration.

Post Structure:
- HOOK: Striking fact using real data
- INSIGHT: Real numbers from reports
- VALUE: What I can do for clients
- CALL TO ACTION: Invite consulting inquiries
- HASHTAGS: Relevant tags
"""

import os
import sys
import requests
import pyperclip
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
import re

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_recent_reports(vault_path, days=7):
    """
    Get all report files from the past N days.
    
    Args:
        vault_path: Path to Hydrology-Vault
        days: Number of days to look back (default 7)
    
    Returns:
        List of report file paths and their content
    """
    done_dir = Path(vault_path) / 'Done'
    
    if not done_dir.exists():
        return []
    
    # Get all report files
    report_files = list(done_dir.glob('report_*.md'))
    
    # Filter by date (past 7 days)
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_reports = []
    
    for report_file in report_files:
        try:
            # Extract timestamp from filename if possible
            # Format: report_[name]_YYYYMMDD_HHMMSS.md
            match = re.search(r'(\d{8}_\d{6})', report_file.name)
            if match:
                file_date_str = match.group(1)
                file_date = datetime.strptime(file_date_str, '%Y%m%d_%H%M%S')
                
                if file_date >= cutoff_date:
                    content = report_file.read_text(encoding='utf-8')
                    recent_reports.append({
                        'file': report_file,
                        'content': content,
                        'date': file_date
                    })
            else:
                # If no timestamp, include if modified recently
                mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                if mtime >= cutoff_date:
                    content = report_file.read_text(encoding='utf-8')
                    recent_reports.append({
                        'file': report_file,
                        'content': content,
                        'date': mtime
                    })
        except Exception as e:
            print(f"⚠️  Error reading {report_file.name}: {e}")
    
    return recent_reports


def extract_data_from_reports(reports):
    """
    Extract key data points from reports for post generation.
    
    Returns:
        dict with rivers, discharges, conditions, and notable findings
    """
    data = {
        'rivers': [],
        'high_risk_count': 0,
        'total_reports': len(reports),
        'max_discharge': 0,
        'max_discharge_river': '',
        'notable_findings': []
    }
    
    for report in reports:
        content = report['content']
        
        # Extract river names and discharges
        river_matches = re.findall(r'## River: ([^\n]+)', content)
        discharge_matches = re.findall(r'Discharge.*?\*\*([\d.]+)\s*m', content)
        condition_matches = re.findall(r'\*\*Condition:\*\*\s*(\w+)', content)
        
        for i, river in enumerate(river_matches):
            data['rivers'].append(river.strip())
            
            if i < len(discharge_matches):
                try:
                    discharge = float(discharge_matches[i])
                    if discharge > data['max_discharge']:
                        data['max_discharge'] = discharge
                        data['max_discharge_river'] = river.strip()
                    
                    # Count high risk
                    if i < len(condition_matches):
                        if condition_matches[i].lower() == 'high':
                            data['high_risk_count'] += 1
                except ValueError:
                    pass
        
        # Extract notable findings
        if 'HIGH' in content.upper() or 'FLOOD' in content.upper():
            data['notable_findings'].append('High risk flood conditions detected')
        
        if 'rainfall' in content.lower():
            data['notable_findings'].append('Heavy rainfall impacts observed')
    
    return data


def generate_linkedin_post(reports, vault_path='Hydrology-Vault'):
    """
    Generate a LinkedIn sales post using Qwen AI.
    
    Post structure:
    - HOOK: Striking fact using real data
    - INSIGHT: Real numbers from reports
    - VALUE: What I can do for clients
    - CALL TO ACTION: Invite consulting inquiries
    - HASHTAGS: Relevant tags
    
    Args:
        reports: List of recent report dicts
        vault_path: Path to Hydrology-Vault
    
    Returns:
        Generated post text (150-250 words)
    """
    from qwen_brain import decide_next_skill
    
    # Extract data from reports
    data = extract_data_from_reports(reports)
    
    # Get user info from .env
    my_name = os.getenv('MY_NAME', 'Zainab Mukhtar')
    my_email = os.getenv('MY_EMAIL', 'zainabmukhtar2277@gmail.com')
    
    # Build prompt for Qwen AI
    prompt = f"""You are helping {my_name}, a hydrology student offering freelance consulting services.

Generate a LinkedIn post (150-250 words) to attract consulting clients.

Use this EXACT structure:

HOOK (1 sentence):
A striking fact using real data from this week's reports.
Example: "This week my AI monitoring system detected HIGH RISK flooding conditions on the Chenab River 6 hours before any official warning."

INSIGHT (2-3 sentences):
Real numbers from reports. River names. What it means.
Example: "Discharge reached 180 m³/s — 20% above flood threshold. Combined with 62mm catchment rainfall, downstream communities faced genuine risk."

VALUE (2 sentences):
What I can do for clients with this expertise.
Example: "Early flood detection saves lives and reduces infrastructure damage. I help NGOs, municipalities and engineering firms understand water risk before it becomes a crisis."

CALL TO ACTION (1-2 sentences):
Invite consulting inquiries.
Example: "Need a flood risk assessment or hydrology report for your project? DM me or email {my_email}"

HASHTAGS:
#Hydrology #WaterResources #Pakistan #FloodRisk #FreelanceConsulting #WaterManagement #ClimateResilience

REAL DATA FROM REPORTS THIS WEEK:
- Total reports generated: {data['total_reports']}
- Rivers monitored: {', '.join(set(data['rivers'])) if data['rivers'] else 'Multiple rivers'}
- High risk detections: {data['high_risk_count']}
- Maximum discharge: {data['max_discharge']:.2f} m³/s on {data['max_discharge_river'] if data['max_discharge_river'] else 'unknown river'}
- Notable findings: {', '.join(set(data['notable_findings'])) if data['notable_findings'] else 'Routine monitoring completed'}

MY DETAILS:
- Name: {my_name}
- Email: {my_email}

Write the complete post now. Make it sound human and professional. Include real numbers. Keep it 150-250 words."""

    # Call Qwen AI
    try:
        import subprocess

        # Try to find Qwen CLI
        qwen_cli_path = None
        possible_paths = [
            os.path.join(os.getenv('APPDATA', ''), 'npm', 'node_modules', '@qwen-code', 'qwen-code', 'cli.js'),
            r'C:\Users\zaina\AppData\Roaming\npm\node_modules\@qwen-code\qwen-code\cli.js',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                qwen_cli_path = path
                break

        if qwen_cli_path:
            process = subprocess.run(
                ['node', qwen_cli_path, '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            process = subprocess.run(
                ['qwen', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

        if process.returncode != 0:
            raise RuntimeError(f"Qwen CLI error: {process.stderr}")
        
        output = process.stdout.strip()
        
        if not output:
            raise RuntimeError("Qwen returned empty response")

        post_content = output
        print("✅ Post generated by Qwen AI")
        return post_content

    except FileNotFoundError:
        print("\n" + "="*60)
        print("❌ CRITICAL ERROR: Qwen CLI not found!")
        print("="*60)
        print("\nQwen CLI is required for LinkedIn post generation.")
        print("There is NO fallback - Qwen MUST be installed.")
        print("\n📦 Install Qwen CLI:")
        print("   npm install -g @qwen-code/qwen-code")
        print("\n🔗 Or visit: https://github.com/QwenLM/Qwen")
        print("="*60)
        raise
    except subprocess.TimeoutExpired:
        print("\n" + "="*60)
        print("❌ CRITICAL ERROR: Qwen request timed out (60s limit)")
        print("="*60)
        raise
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ CRITICAL ERROR: {e}")
        print("="*60)
        print("Qwen AI is required - no fallback available.")
        print("="*60)
        raise


def post_via_api(post_content):
    """
    Mode A: Post to LinkedIn using official API.
    
    Requires:
    - LINKEDIN_ACCESS_TOKEN in .env
    - LINKEDIN_PERSON_ID in .env
    
    Args:
        post_content: Text content of the post
    
    Returns:
        True if successful, False otherwise
    """
    print("\n🔌 Using LinkedIn API mode...")
    
    # Get credentials from .env
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    person_id = os.getenv('LINKEDIN_PERSON_ID', '')
    
    # Validate credentials
    if not access_token or access_token == 'your_token_here':
        print("❌ LINKEDIN_ACCESS_TOKEN not configured in .env")
        return False
    
    if not person_id or person_id == 'your_person_id_here':
        print("❌ LINKEDIN_PERSON_ID not configured in .env")
        return False
    
    # LinkedIn API endpoint
    url = 'https://api.linkedin.com/v2/ugcPosts'
    
    # Headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    # Request body
    body = {
        "author": f"urn:li:person:{person_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        print(f"📤 Posting to LinkedIn API...")
        print(f"   Author: urn:li:person:{person_id}")
        print(f"   Content length: {len(post_content)} characters")
        
        response = requests.post(url, json=body, headers=headers, timeout=30)
        
        # Log the attempt
        log_linkedin_attempt(post_content, response.status_code, response.text, mode='API')
        
        if response.status_code in [200, 201]:
            print("✅ LinkedIn post successful via API!")
            print(f"   Status code: {response.status_code}")
            return True
        else:
            print(f"❌ LinkedIn API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {e}")
        log_linkedin_attempt(post_content, 0, str(e), mode='API')
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def post_via_workaround(post_content):
    """
    Mode B: Smart workaround fallback.
    
    - Saves post to Hydrology-Vault/LinkedIn_Posts/
    - Copies post to clipboard automatically
    - Opens LinkedIn in browser
    - Shows clear instructions
    
    Args:
        post_content: Text content of the post
    
    Returns:
        True if successful, False otherwise
    """
    print("\n📋 Using workaround mode...")
    
    try:
        # Create LinkedIn_Posts directory
        posts_dir = Path('Hydrology-Vault/LinkedIn_Posts')
        posts_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        post_filename = f"Post_{timestamp}.md"
        post_path = posts_dir / post_filename
        
        # Create post content with frontmatter
        post_markdown = f"""---
type: linkedin_post
created: {datetime.now().isoformat()}
status: ready_to_post
word_count: {len(post_content.split())}
---

# 📝 LinkedIn Post

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Status:** Ready to post

---

{post_content}

---

## 📤 Posting Instructions

1. The post text has been copied to your clipboard
2. LinkedIn is opening in your browser
3. Click in the "Start a post" box
4. Press Ctrl+V to paste
5. Click the "Post" button
6. Done! Takes 10 seconds!

---

*Generated by Hydrology FTE Agent - LinkedIn Auto-Poster*
"""
        
        # Save the post file
        post_path.write_text(post_markdown, encoding='utf-8')
        print(f"✅ Post saved to: {post_path}")
        
        # Copy to clipboard
        pyperclip.copy(post_content)
        print("✅ Post copied to clipboard")
        
        # Open LinkedIn in browser
        print("🌐 Opening LinkedIn in your browser...")
        webbrowser.open('https://www.linkedin.com/feed/')
        
        # Show instructions
        print("\n" + "=" * 60)
        print("=== LINKEDIN POST READY ===")
        print("=" * 60)
        print("\n✅ Post has been copied to your clipboard")
        print("🌐 LinkedIn is opening in your browser")
        print("\n📝 NEXT STEPS:")
        print("   1. Click in the 'Start a post' box")
        print("   2. Press Ctrl+V to paste")
        print("   3. Click the 'Post' button")
        print("   4. Done! Takes 10 seconds!")
        print("\n" + "=" * 60)
        
        # Log the attempt
        log_linkedin_attempt(post_content, 200, "Workaround mode - manual posting required", mode='Workaround')
        
        return True
        
    except Exception as e:
        print(f"❌ Workaround error: {e}")
        log_linkedin_attempt(post_content, 0, str(e), mode='Workaround')
        return False


def post_to_linkedin(post_content):
    """
    Auto-detect which mode to use and post to LinkedIn.
    
    Priority:
    1. Try Mode A (API) if token exists
    2. Fall back to Mode B (workaround) if API fails or no token
    
    Args:
        post_content: Text content of the post
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("📤 LinkedIn Auto-Poster")
    print("=" * 60)
    
    # Check for API token
    token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    
    if token and token != 'your_token_here':
        print("✅ LINKEDIN_ACCESS_TOKEN found")
        print("🔌 Attempting Mode A: LinkedIn API...")
        
        success = post_via_api(post_content)
        
        if success:
            print("\n🎉 Post successful via API!")
            return True
        else:
            print("\n⚠️  API failed, switching to Mode B: Workaround...")
            return post_via_workaround(post_content)
    else:
        print("⚠️  No API token found in .env")
        print("📋 Using Mode B: Workaround mode...")
        return post_via_workaround(post_content)


def log_linkedin_attempt(post_content, status_code, response_text, mode):
    """
    Log LinkedIn post attempt to linkedin_log.txt
    
    Args:
        post_content: The post text
        status_code: HTTP status code (or 0 for workaround)
        response_text: API response or error message
        mode: 'API' or 'Workaround'
    """
    log_path = Path('Hydrology-Vault/linkedin_log.txt')
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    success = status_code in [200, 201] if mode == 'API' else True
    
    status_str = "✅ SUCCESS" if success else "❌ FAILED"
    
    log_entry = f"""
{'='*60}
{status_str} - LinkedIn Post ({mode} Mode)
{'='*60}
Timestamp: {timestamp}
Mode: {mode}
Status Code: {status_code}
Word Count: {len(post_content.split())}
Character Count: {len(post_content)}

Response/Notes:
{response_text[:500]}{'...' if len(response_text) > 500 else ''}

Post Preview (first 200 chars):
{post_content[:200]}...
{'='*60}
"""
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def run(vault_path='Hydrology-Vault'):
    """
    Main entry point for LinkedIn posting skill.
    
    Workflow:
    1. Get recent reports from past 7 days
    2. Generate LinkedIn post using Qwen AI
    3. Post to LinkedIn (API or workaround)
    4. Log result
    
    Args:
        vault_path: Path to Hydrology-Vault
    
    Returns:
        dict with success status and post content
    """
    print("\n" + "=" * 60)
    print("📝 LinkedIn Post Generator")
    print("=" * 60)
    
    # Step 1: Get recent reports
    print("\n📊 Scanning for recent reports...")
    reports = get_recent_reports(vault_path, days=7)
    
    if not reports:
        print("⚠️  No reports found from past 7 days")
        print("   Generate some hydrology reports first")
        return {
            'success': False,
            'message': 'No reports found',
            'post_content': None
        }
    
    print(f"✅ Found {len(reports)} recent report(s)")
    
    # Step 2: Generate post
    print("\n🧠 Generating LinkedIn post...")
    post_content = generate_linkedin_post(reports, vault_path)
    
    if not post_content:
        print("❌ Failed to generate post")
        return {
            'success': False,
            'message': 'Post generation failed',
            'post_content': None
        }
    
    # Show generated post
    print("\n" + "=" * 60)
    print("📝 GENERATED POST:")
    print("=" * 60)
    print(post_content)
    print("=" * 60)
    print(f"\n📊 Word count: {len(post_content.split())}")
    print(f"📊 Character count: {len(post_content)}")
    
    # Step 3: Post to LinkedIn
    print("\n📤 Posting to LinkedIn...")
    success = post_to_linkedin(post_content)
    
    return {
        'success': success,
        'message': f'Post {"successful" if success else "failed"}',
        'post_content': post_content,
        'reports_used': len(reports)
    }


if __name__ == "__main__":
    # Test the LinkedIn posting skill
    print("=" * 50)
    print("🧪 Testing LinkedIn Auto-Poster")
    print("=" * 50)
    
    result = run()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Success: {result['success']}")
    print(f"  Message: {result['message']}")
    print(f"  Reports used: {result['reports_used']}")
    print("=" * 50)
