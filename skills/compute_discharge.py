def run(df):
    """
    Compute discharge from width, depth, and velocity.
    
    Formula: Q = Width × Depth × Velocity
    
    Args:
        df: DataFrame with Width_m, Depth_m, Velocity_mps columns
        
    Returns:
        DataFrame with added Discharge column, or None if error
    """
    try:
        # Validate required columns
        required_cols = ['Width_m', 'Depth_m', 'Velocity_mps']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            print(f"Error: Missing required columns for computation: {missing}")
            return None
        
        df = df.copy()  # Avoid modifying original
        df["Discharge"] = df["Width_m"] * df["Depth_m"] * df["Velocity_mps"]
        
        print(f"✅ Computed discharge for {len(df)} records")
        return df

    except KeyError as e:
        print(f"Error: Missing column in DataFrame: {e}")
        return None
    except Exception as e:
        print(f"Error computing discharge: {e}")
        return None