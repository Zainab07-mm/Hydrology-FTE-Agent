import pandas as pd

def run(file_path):
    """
    Ingest hydrology data from CSV file.
    
    Expected columns: River, Width_m, Depth_m, Velocity_mps
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        pandas DataFrame or None if error
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['River', 'Width_m', 'Depth_m', 'Velocity_mps']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            print(f"Error: Missing required columns: {missing}")
            print(f"Expected: {required_cols}")
            print(f"Found: {list(df.columns)}")
            return None
        
        print(f"✅ Ingested {len(df)} records from {file_path}")
        return df

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: File is empty: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None