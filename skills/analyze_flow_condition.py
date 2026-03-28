def run(df):
    """
    Analyze flow condition and risk level based on discharge.
    
    Classification:
    - Q < 50 m³/s: Low condition, Low risk
    - 50 ≤ Q ≤ 150 m³/s: Moderate condition, Medium risk
    - Q > 150 m³/s: High condition, High risk
    
    Args:
        df: DataFrame with Discharge column
        
    Returns:
        List of dicts with River, Discharge, Condition, Risk, or None if error
    """
    try:
        # Validate required columns
        if 'Discharge' not in df.columns:
            print("Error: Missing 'Discharge' column. Run compute_discharge first.")
            return None
        
        if 'River' not in df.columns:
            print("Error: Missing 'River' column")
            return None
        
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

        print(f"✅ Analyzed flow conditions for {len(results)} rivers")
        return results

    except KeyError as e:
        print(f"Error: Missing column in DataFrame: {e}")
        return None
    except Exception as e:
        print(f"Error analyzing flow: {e}")
        return None