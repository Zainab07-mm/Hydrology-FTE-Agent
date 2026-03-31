"""
Compute Discharge Skill

Calculates discharge from width, depth, and velocity measurements.

Formula: Q = Width × Depth × Velocity

Returns:
    dict with:
    - success: True/False
    - data: DataFrame with Discharge column (if successful)
    - error: Error message (if failed)
"""

from datetime import datetime


def run(df=None, **kwargs):
    """
    Compute discharge from width, depth, and velocity.

    Args:
        df: DataFrame with Width_m, Depth_m, Velocity_mps columns
        **kwargs: Additional arguments (ignored)

    Returns:
        dict with success status and data or error
    """
    result = {
        'success': False,
        'data': None,
        'error': None,
        'skill': 'compute_discharge',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Validate input
        if df is None:
            result['error'] = 'No DataFrame provided'
            print(f"❌ Error: No DataFrame provided")
            return result
        
        # Validate required columns
        required_cols = ['Width_m', 'Depth_m', 'Velocity_mps']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            result['error'] = f'Missing required columns: {missing}'
            print(f"❌ Error: Missing required columns: {missing}")
            return result
        
        # Compute discharge
        df = df.copy()  # Avoid modifying original
        df["Discharge"] = df["Width_m"] * df["Depth_m"] * df["Velocity_mps"]
        
        # Success
        result['success'] = True
        result['data'] = df
        result['records_computed'] = len(df)
        
        print(f"✅ Computed discharge for {len(df)} records")
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error computing discharge: {e}")
        return result
