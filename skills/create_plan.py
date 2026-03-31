"""
Create Plan Skill for Hydrology FTE Agent

This skill uses Qwen AI to create a reasoning plan BEFORE processing data.
The plan includes:
- What data was received
- Risk pre-assessment
- Analysis steps
- Decision criteria
- Expected output

The plan is saved as a .md file in Hydrology-Vault/Plans/
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime


def run(df, source_file, vault_path):
    """
    Create a reasoning plan for hydrology data processing.

    Args:
        df: pandas DataFrame with hydrology data
        source_file: Path to the source CSV file
        vault_path: Path to the Hydrology-Vault folder

    Returns:
        dict with plan content and file path, or None if error
    """
    try:
        # Extract key information from data
        river_names = df['River'].unique().tolist() if 'River' in df.columns else ['Unknown']
        
        # Calculate preliminary statistics for risk assessment
        if 'Discharge' in df.columns:
            max_discharge = df['Discharge'].max()
            avg_discharge = df['Discharge'].mean()
        else:
            # Estimate discharge if not yet calculated
            if all(col in df.columns for col in ['Width_m', 'Depth_m', 'Velocity_mps']):
                estimated_q = (df['Width_m'] * df['Depth_m'] * df['Velocity_mps']).max()
                max_discharge = estimated_q
                avg_discharge = (df['Width_m'] * df['Depth_m'] * df['Velocity_mps']).mean()
            else:
                max_discharge = 0
                avg_discharge = 0

        # Build prompt for Qwen AI
        prompt = _build_plan_prompt(df, source_file, river_names, max_discharge, avg_discharge)

        # Call Qwen AI
        plan_content = _call_qwen(prompt)

        if not plan_content:
            raise RuntimeError("Qwen returned empty plan content")

        # Create Plans directory if it doesn't exist
        plans_dir = Path(vault_path) / 'Plans'
        plans_dir.mkdir(exist_ok=True)

        # Generate plan filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        river_name = river_names[0] if river_names else 'unknown'
        plan_filename = f"Plan_{river_name}_{timestamp}.md"
        plan_path = plans_dir / plan_filename

        # Add frontmatter to plan
        frontmatter = f"""---
type: reasoning_plan
source_file: {Path(source_file).name}
river_names: {', '.join(river_names)}
created: {datetime.now().isoformat()}
max_discharge_estimate: {max_discharge:.2f}
status: active
---

"""
        full_content = frontmatter + plan_content

        # Save plan to file
        plan_path.write_text(full_content, encoding='utf-8')
        print(f"📝 Plan created: {plan_path.name}")

        return {
            'plan_path': str(plan_path),
            'content': full_content,
            'river_names': river_names,
            'timestamp': timestamp
        }

    except Exception as e:
        print(f"❌ Error creating plan: {e}")
        raise  # Re-raise to stop processing


def _build_plan_prompt(df, source_file, river_names, max_q, avg_q):
    """Build a structured prompt for Qwen AI to create the plan."""

    # Create data summary
    data_summary = []
    for _, row in df.head(5).iterrows():  # First 5 rows as sample
        if 'River' in row:
            data_summary.append(f"- {row['River']}: Width={row.get('Width_m', 'N/A')}m, Depth={row.get('Depth_m', 'N/A')}m, Velocity={row.get('Velocity_mps', 'N/A')}m/s")

    data_text = "\n".join(data_summary)

    return f"""You are an expert hydrology data analyst creating a processing plan.

Based on the data below, write a structured plan with these EXACT sections:

## What I received
Describe the input file and data it contains. Mention:
- Filename: {Path(source_file).name}
- Rivers monitored: {', '.join(river_names)}
- Number of measurements: {len(df)}
- Data sample:
{data_text}

## Risk pre-assessment
Look at these preliminary values:
- Maximum estimated discharge: {max_q:.2f} m³/s
- Average estimated discharge: {avg_q:.2f} m³/s

Based on these values, make a preliminary risk guess:
- Low risk: Q < 50 m³/s (normal flow conditions)
- Medium risk: 50-150 m³/s (elevated flow, monitor closely)
- High risk: Q > 150 m³/s (potential flood conditions)

State your assessment and reasoning.

## My analysis steps
List the exact steps you will take:
Step 1: Which skill runs first and why
Step 2: Which skill runs second and why
Step 3: Which skill runs third and why
Step 4: Which skill runs last and why

Be specific about what each skill does.

## Decision criteria
Define what thresholds will trigger alerts:
- At what discharge value will you flag for human review?
- What conditions warrant a flood warning?
- What email/notification actions might be needed?

Example format:
"If discharge exceeds 150 m³/s, I will recommend sending a flood alert email to stakeholders."

## Expected output
Describe what report will be generated:
- Report filename pattern
- What sections will it contain
- Who is the intended audience

Write the complete plan now. Use markdown formatting."""


def _call_qwen(prompt):
    """Call Qwen AI CLI to generate the plan."""
    try:
        # Try to find Qwen CLI path
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

        return output

    except FileNotFoundError:
        print("\n" + "="*60)
        print("❌ CRITICAL ERROR: Qwen CLI not found!")
        print("="*60)
        print("\nQwen CLI is required for plan generation.")
        print("There is NO fallback - Qwen MUST be installed.")
        print("\n📦 Install Qwen CLI:")
        print("   npm install -g @qwen-code/qwen-code")
        print("\n🔗 Or visit: https://github.com/QwenLM/Qwen")
        print("\n💡 After installation, verify:")
        print("   qwen --version")
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


if __name__ == "__main__":
    # Test the create_plan skill
    import pandas as pd
    
    print("=" * 50)
    print("🧪 Testing Create Plan Skill")
    print("=" * 50)
    
    # Create test data
    test_df = pd.DataFrame({
        'River': ['Chenab', 'Indus', 'Ravi'],
        'Width_m': [30, 50, 25],
        'Depth_m': [2, 3, 1.5],
        'Velocity_mps': [1.5, 2.0, 1.2]
    })
    
    result = run(test_df, "hydrology_data/sample.csv", "Hydrology-Vault")
    
    if result:
        print(f"\n✅ Plan created successfully")
        print(f"📄 Plan file: {result['plan_path']}")
        print(f"🌊 Rivers: {result['river_names']}")
    else:
        print("\n❌ Failed to create plan")
    
    print("\n" + "=" * 50)
