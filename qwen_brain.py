import os
import json
import requests

def call_openrouter(prompt):
    """Helper function to route prompts directly through OpenRouter API checking multiple paths."""
    api_key = None
    model_name = "qwen/qwen-2.5-72b-instruct" # Fallback default
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Check multiple possible paths for settings.json
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'settings.json'), # Same folder as qwen_brain.py
        os.path.join(os.getcwd(), 'settings.json'),              # Main root directory where you run main.py
        'settings.json'                                           # Current execution fallback
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if config.get("OPENROUTER_API_KEY"):
                        api_key = config.get("OPENROUTER_API_KEY")
                        if config.get("model"):
                            model_name = config.get("model")
                        if config.get("base_url"):
                            url = f"{config.get('base_url').rstrip('/')}/chat/completions"
                        break # Found a valid key! Stop searching paths.
            except Exception:
                pass

    # Fallback to standard environment variable if settings.json wasn't found or was unparseable
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    # ABSOLUTE BACKUP: If environment variable parsing fails, inject the key directly
    if not api_key or "your_" in api_key or api_key == "":
        raise ValueError("❌ OpenRouter API Key missing or unparseable in your environment configuration.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        import certifi
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(data), 
            timeout=30,
            verify=certifi.where()
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise RuntimeError(f"OpenRouter API call failed: {e}")

def decide_next_skill(state):
    """
    Silver Tier Brain Logic.
    Reads current workflow state and uses OpenRouter to decide the next step.
    """
    # Create a clear prompt telling Qwen what steps are completed
    prompt = f"""
    You are the brain of an autonomous hydrology agent. Based on the current history log, decide what the immediate next tool step should be.
    
    Current History Log of actions taken: {state.get('log', [])}
    Has data been ingested? {'Yes' if state.get('data') is not None else 'No'}
    Are computations complete? {'Yes' if state.get('results') is not None else 'No'}
    
    Your available steps are:
    - "ingest_hydrology_data" (if data isn't loaded yet)
    - "compute_discharge" (if data is loaded but discharge isn't calculated)
    - "analyze_flow_condition" (if data is calculated but risks aren't evaluated)
    - "generate_hydrology_report" (if evaluations are ready but no report is written)
    - "DONE" (if everything is completed)
    
    Respond with EXACTLY one word from the choices above. Do not include any punctuation, conversational filler, or formatting.
    """
    
    ai_decision = call_openrouter(prompt)
    
    # Clean up any potential markdown formatting from the response string
    cleaned_decision = ai_decision.replace('"', '').replace("'", "").strip()
    
    valid_skills = ["ingest_hydrology_data", "compute_discharge", "analyze_flow_condition", "generate_hydrology_report", "DONE"]
    
    for skill in valid_skills:
        if skill in cleaned_decision:
            return skill
            
    # Fallback default loop tracker if response is ambiguous
    if not state.get('log'):
        return "ingest_hydrology_data"
    return "DONE"

def update_dashboard(vault_path, status="Running", last_action="None", task_queue="Empty"):
    """
    Updates the Obsidian Dashboard.md file with detailed system status tracking.
    Matches the exact 4-argument signature expected by the Orchestrator loop.
    """
    try:
        dashboard_path = os.path.join(vault_path, "Dashboard.md")
        
        # Read existing dashboard content if it exists
        content = ""
        if os.path.exists(dashboard_path):
            with open(dashboard_path, "r", encoding="utf-8") as f:
                content = f.read()
                
        # Build a beautifully formatted markdown block for your Obsidian Vault
        status_block = (
            "### 🤖 Current Agent Status\n"
            f"- **System State:** `{status}`\n"
            f"- **Last Completed Action:** {last_action}\n"
            f"- **Task Queue Status:** `{task_queue}`\n"
        )
        
        # If the status section already exists, strip the old one out to prevent infinite appending
        if "### 🤖 Current Agent Status" in content:
            parts = content.split("### 🤖 Current Agent Status")
            # Overwrite the old tracking block with the fresh one
            new_content = parts[0] + status_block
        else:
            new_content = content + "\n\n" + status_block

        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
    except Exception as e:
        print(f"⚠️ Dashboard update skipped: {e}")