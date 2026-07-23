import pandas as pd
import requests
import time
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
ENROLLMENT_FILE = BASE_DIR / "data" / "tricorder_enrollment_20260503 anonymised with identifier codes.xlsx"
EPRACCUR_FILE = BASE_DIR / "data" / "epraccur.xlsx"
OUTPUT_FILE = BASE_DIR / "data" / "practice_coordinates.csv"

def get_coordinates(postcodes):
    """Fetch coordinates in bulk from postcodes.io"""
    url = "https://api.postcodes.io/postcodes"
    # the api accepts up to 100 postcodes at a time
    results = {}
    
    # Split into chunks of 100
    chunk_size = 100
    for i in range(0, len(postcodes), chunk_size):
        chunk = postcodes[i:i + chunk_size]
        response = requests.post(url, json={"postcodes": chunk})
        
        if response.status_code == 200:
            data = response.json().get('result', [])
            for item in data:
                pc = item.get('query')
                result = item.get('result')
                if result:
                    results[pc] = (result.get('latitude'), result.get('longitude'))
                else:
                    results[pc] = (None, None)
        else:
            print(f"Error fetching chunk {i}: HTTP {response.status_code}")
            
        time.sleep(0.5)  # respectful delay between bulk requests
        
    return results

def main():
    print("Loading enrollment data...")
    df_enroll = pd.read_excel(ENROLLMENT_FILE, sheet_name="site_level")
    site_names = df_enroll['site_name'].dropna().unique()
    print(f"Found {len(site_names)} unique practices in enrollment data.")
    
    print("Loading epraccur.xlsx...")
    # epraccur has no headers. Col 1 = Name, Col 9 = Postcode
    df_ep = pd.read_excel(EPRACCUR_FILE, header=None)
    df_ep.columns = [str(i) for i in range(len(df_ep.columns))]
    df_ep = df_ep.rename(columns={'1': 'Practice Name', '9': 'Postcode'})
    
    # Clean up strings for merging
    df_enroll['clean_name'] = df_enroll['site_name'].str.upper().str.strip()
    df_ep['clean_name'] = df_ep['Practice Name'].astype(str).str.upper().str.strip()
    
    # Drop duplicates just in case there are multiple entries for a practice in epraccur
    df_ep_unique = df_ep.drop_duplicates(subset=['clean_name'], keep='first')
    
    print("Matching postcodes...")
    # Map practice names to postcodes
    mapping = pd.merge(
        pd.DataFrame({'site_name': site_names, 'clean_name': [name.upper().strip() for name in site_names]}),
        df_ep_unique[['clean_name', 'Postcode']],
        on='clean_name',
        how='left'
    )
    
    matched = mapping.dropna(subset=['Postcode'])
    missing = mapping[mapping['Postcode'].isna()]
    
    print(f"Matched {len(matched)} practices. {len(missing)} practices could not be found in epraccur.")
    if not missing.empty:
        print("Missing practices:")
        for name in missing['site_name']:
            print(f" - {name}")
            
    postcodes_to_fetch = matched['Postcode'].dropna().unique().tolist()
    print(f"Fetching coordinates for {len(postcodes_to_fetch)} unique postcodes...")
    
    coords = get_coordinates(postcodes_to_fetch)
    
    # Add lat/lon to our mapping
    mapping['latitude'] = mapping['Postcode'].map(lambda p: coords.get(p, (None, None))[0] if pd.notna(p) else None)
    mapping['longitude'] = mapping['Postcode'].map(lambda p: coords.get(p, (None, None))[1] if pd.notna(p) else None)
    
    # Save the output (site_name, postcode, latitude, longitude)
    output_cols = ['site_name', 'Postcode', 'latitude', 'longitude']
    mapping[output_cols].rename(columns={'Postcode': 'postcode'}).to_csv(OUTPUT_FILE, index=False)
    
    print(f"Successfully saved coordinates to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
