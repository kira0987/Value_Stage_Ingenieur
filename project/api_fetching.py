import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import hashlib

# Configure Chrome options
options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

# Enable performance logging for network events
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

# Start Chrome driver
print("Starting Chrome driver...")
driver = webdriver.Chrome(options=options)

# Navigate to the website
url = "https://www.imf.org/external/datamapper/profile/TUN"
print(f"Navigating to {url}")
driver.get(url)
time.sleep(12)  # Wait longer for page and API calls to complete

# Extract network logs
print("Extracting network logs...")
logs = driver.get_log('performance')
api_data = []

# Prepare folder for API responses
download_folder = 'api_responses'
os.makedirs(download_folder, exist_ok=True)

def safe_filename(url):
    # Use a hash to avoid issues with special characters and long filenames
    return hashlib.sha256(url.encode('utf-8')).hexdigest() + '.bin'

# Process network logs to find all GET/POST requests
print("Processing network logs...")
for entry in logs:
    try:
        message = json.loads(entry['message'])['message']
        if message['method'] == 'Network.requestWillBeSent':
            request = message['params']['request']
            api_url = request['url']
            method = request['method']
            print(f"Request URL: {api_url} | Method: {method}")  # Debug: print all URLs
            if method in ['GET', 'POST']:
                # Get cookies for the domain
                cookies = {c['name']: c['value'] for c in driver.get_cookies() if urlparse(api_url).netloc in c['domain']}
                response_file = None
                status = None
                response_size = 0
                error = None
                try:
                    response = requests.get(api_url, cookies=cookies, timeout=5)
                    status = response.status_code
                    response_size = len(response.content)
                    filename = safe_filename(api_url)
                    response_file = os.path.join(download_folder, filename)
                    with open(response_file, 'wb') as rf:
                        rf.write(response.content)
                except requests.RequestException as e:
                    error = str(e)
                    filename = safe_filename(api_url)
                    response_file = os.path.join(download_folder, filename)
                    with open(response_file, 'wb') as rf:
                        rf.write(b'')  # Save empty file if error
                api_data.append({
                    'url': api_url,
                    'method': method,
                    'cookies': cookies,
                    'status': status,
                    'response_size': response_size,
                    'domain': urlparse(api_url).netloc,
                    'response_file': response_file,
                    'error': error
                })
    except Exception as e:
        print(f"Error processing log entry: {e}")
        continue

# Save to JSON file
output_file = 'api_results_response.json'
with open(output_file, 'w') as f:
    json.dump(api_data, f, indent=2)

# Cleanup
driver.quit()

print(f"API data saved to {output_file}")
print(f"Found and tested {len(api_data)} API endpoints")
print(f"Downloaded responses are saved in the '{download_folder}' folder.")