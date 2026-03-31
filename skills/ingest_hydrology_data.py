"""
Ingest Hydrology Data Skill

Reads hydrology data from CSV file and validates required columns.

Returns:
    dict with:
    - success: True/False
    - data: DataFrame (if successful)
    - error: Error message (if failed)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def run(file_path=None, **kwargs):
    """
    Ingest hydrology data from CSV file.

    Expected columns: River, Width_m, Depth_m, Velocity_mps

    Args:
        file_path: Path to CSV file
        **kwargs: Additional arguments (ignored)

    Returns:
        dict with success status and data or error
    """
    result = {
        'success': False,
        'data': None,
        'error': None,
        'skill': 'ingest_hydrology_data',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Validate input
        if not file_path:
            result['error'] = 'No file_path provided'
            print(f"❌ Error: No file_path provided")
            return result
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            result['error'] = f'File not found: {file_path}'
            print(f"❌ Error: File not found: {file_path}")
            return result
        
        # Read CSV
        df = pd.read_csv(file_path)
        
        if df.empty:
            result['error'] = 'File is empty'
            print(f"❌ Error: File is empty: {file_path}")
            return result
        
        # Validate required columns
        required_cols = ['River', 'Width_m', 'Depth_m', 'Velocity_mps']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            result['error'] = f'Missing required columns: {missing}'
            print(f"❌ Error: Missing required columns: {missing}")
            print(f"   Expected: {required_cols}")
            print(f"   Found: {list(df.columns)}")
            return result
        
        # Success
        result['success'] = True
        result['data'] = df
        result['records'] = len(df)
        
        print(f"✅ Ingested {len(df)} records from {file_path}")
        return result
        
    except pd.errors.EmptyDataError:
        result['error'] = 'File is empty or invalid CSV'
        print(f"❌ Error: File is empty or invalid CSV: {file_path}")
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error reading file: {e}")
        return result
