"""
Analyze Flow Condition Skill

Analyzes flow condition and risk level based on discharge values.

Classification:
- Q < 50 m³/s: Low condition, Low risk
- 50 ≤ Q ≤ 150 m³/s: Moderate condition, Medium risk
- Q > 150 m³/s: High condition, High risk

Returns:
    dict with:
    - success: True/False
    - results: List of analysis results (if successful)
    - error: Error message (if failed)
"""

from datetime import datetime


def run(df=None, **kwargs):
    """
    Analyze flow condition and risk level based on discharge.

    Args:
        df: DataFrame with Discharge column
        **kwargs: Additional arguments (ignored)

    Returns:
        dict with success status and results or error
    """
    result = {
        'success': False,
        'results': None,
        'error': None,
        'skill': 'analyze_flow_condition',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Validate input
        if df is None:
            result['error'] = 'No DataFrame provided'
            print(f"❌ Error: No DataFrame provided")
            return result
        
        # Validate required columns
        if 'Discharge' not in df.columns:
            result['error'] = "Missing 'Discharge' column. Run compute_discharge first."
            print(f"❌ Error: Missing 'Discharge' column. Run compute_discharge first.")
            return result
        
        if 'River' not in df.columns:
            result['error'] = "Missing 'River' column"
            print(f"❌ Error: Missing 'River' column")
            return result
        
        # Analyze each river
        results = []
        
        for _, row in df.iterrows():
            Q = row["Discharge"]
            
            if Q < 50:
                condition = "Low"
                risk = "Low"
            elif Q <= 150:
                condition = "Moderate"
                risk = "Medium"
            else:
                condition = "High"
                risk = "High"
            
            results.append({
                "River": row["River"],
                "Discharge": Q,
                "Condition": condition,
                "Risk": risk
            })
        
        # Success
        result['success'] = True
        result['results'] = results
        result['rivers_analyzed'] = len(results)
        
        print(f"✅ Analyzed flow conditions for {len(results)} rivers")
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error analyzing flow: {e}")
        return result
