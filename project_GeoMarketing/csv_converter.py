import pandas as pd
import json

# Read the JSON file
with open('agences_biat_4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert to DataFrame
if isinstance(data, dict):
    # If the JSON is a dict of records
    df = pd.DataFrame([data])
else:
    df = pd.DataFrame(data)

# Save to CSV
csv_path = 'agences_biat.csv'
df.to_csv(csv_path, index=False, encoding='utf-8')
print(f"Saved to {csv_path}")
