import requests
import pandas as pd
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Possible base URLs to try
BASE_URLS = [
    "http://fr-api.data.gov.tn/api/1.0/",
    "http://dataportal.ins.tn/api/1.0/",
    "https://fr-api.data.gov.tn/api/1.0/"
]

# Optional: Add your API token here if authenticated
API_TOKEN = None  # Replace with "YOUR_TOKEN" if available
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

# Configure retry mechanism
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

# Function to fetch all datasets
def get_all_datasets(base_url):
    datasets = []
    try:
        url = f"{base_url}dataset?pretty=1"
        print(f"Trying URL: {url}")
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        datasets.extend(data.get('results', []))
        total = data.get('total', 0)
        size = data.get('size', 10)
        fetched = len(datasets)
        
        while fetched < total:
            page = (fetched // size) + 1
            url = f"{base_url}dataset?pretty=1&from={fetched}"
            print(f"Fetching page {page}: {url}")
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            datasets.extend(data.get('results', []))
            fetched += len(data.get('results', []))
            time.sleep(1)  # Avoid rate limit
        return datasets
    except requests.exceptions.RequestException as e:
        print(f"Error fetching datasets from {base_url}: {str(e)}")
        return []

# Function to fetch records for a dataset and filter by years (2018-2025)
def fetch_dataset_records(dataset_code, base_url, years=range(2018, 2026)):
    records = []
    try:
        url = f"{base_url}dataset/{dataset_code}?pretty=1"
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        records_url = f"{base_url}dataset/{dataset_code}/records?pretty=1"
        response = session.get(records_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        records_data = response.json()
        
        for record in records_data.get('records', []):
            record_year = None
            for field, value in record.items():
                if field.lower() in ['year', 'annee', 'date'] and value:
                    try:
                        year = int(str(value)[:4]) if isinstance(value, str) else int(value)
                        if year in years:
                            record_year = year
                            break
                    except (ValueError, TypeError):
                        continue
            if record_year:
                records.append(record)
        
        return records, data.get('title', dataset_code), data.get('fields', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching records for dataset {dataset_code} from {base_url}: {str(e)}")
        return [], dataset_code, []

# Main function to fetch all indicators
def fetch_tunisia_indicators():
    all_data = []
    for base_url in BASE_URLS:
        print(f"\nAttempting to fetch data using base URL: {base_url}")
        try:
            datasets = get_all_datasets(base_url)
            if not datasets:
                print(f"No datasets found for {base_url}. Trying next URL...")
                continue
            
            for dataset in datasets:
                dataset_code = dataset.get('code')
                if not dataset_code:
                    continue
                
                print(f"Fetching records for dataset: {dataset.get('title', dataset_code)}")
                records, dataset_title, fields = fetch_dataset_records(dataset_code, base_url)
                
                if records:
                    df = pd.DataFrame(records)
                    df['Dataset'] = dataset_title
                    all_data.append(df)
                time.sleep(1)  # Avoid rate limit
            
            if all_data:
                break  # Exit loop if data was successfully retrieved
        except Exception as e:
            print(f"Failed to fetch data from {base_url}: {str(e)}")
            continue
    
    if not all_data:
        print("No data retrieved from any base URL.")
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    output_file = 'tunisia_ins_indicators_2018_2025.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"Data successfully saved to {output_file}")
    
    return combined_df

# Main execution
if __name__ == "__main__":
    result = fetch_tunisia_indicators()
    if result is not None:
        print("\nSample of retrieved data:")
        print(result.head())
    else:
        print("Failed to retrieve data from all base URLs.")