import requests
import json
from playwright.sync_api import sync_playwright

# Correct API endpoint (adjust if you find a different one in the network tab)
url = "http://dataportal.ins.tn/PPService.axd"

# Example: You MUST inspect the network tab for the real parameters!
params = {
    # "action": "gettree",  # Example only!
    # "cube": "...",        # Example only!
    # Add all required params here
}

headers = {
    "User-Agent": "Mozilla/5.0"
    # Add cookies or other headers if needed
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print("Status code:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print(response.text)  # or response.json() if JSON
except Exception as e:
    print("Error:", e)

# If you want to pretty-print JSON:
# try:
#     print(response.json())
# except Exception:
#     print(response.text)

robots_url = "http://dataportal.ins.tn/robots.txt"
resp = requests.get(robots_url)
print(resp.text)

def log_ppservice_requests_and_responses(url="http://dataportal.ins.tn/fr/DataAnalysis"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # List to store all API call data
        api_calls = []

        # Listen for all requests and responses
        def handle_response(response):
            if "PPService.axd" in response.url:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        body = response.json()
                    else:
                        body = response.text()
                except Exception:
                    body = "<Failed to decode response>"
                api_calls.append({
                    "url": response.url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": body
                })
                print(f"API CALL: {response.url} (status: {response.status})")

        page.on("response", handle_response)

        # Go to the main page
        page.goto(url)
        print("Interact with the page to trigger API calls...")
        input("When done, press Enter here to finish and close the browser...")

        browser.close()

        # Save all found API calls and responses to a JSON file
        with open("ppservice_api_calls.json", "w", encoding="utf-8") as f:
            json.dump(api_calls, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(api_calls)} API calls and responses to ppservice_api_calls.json")

if __name__ == "__main__":
    log_ppservice_requests_and_responses()

# Example: Replace with your actual indicator list
indicators = [
    "Agriculture"  # ... fill with real indicator codes/names
]

years = range(2018, 2026)
months = range(1, 13)

results = []

for indicator in indicators:
    for year in years:
        for month in months:
            params = {
                "indicator": indicator,  # Adjust key as needed
                "year": year,
                "month": month
                # Add any other required params
            }
            url = "http://dataportal.ins.tn/PPService.axd"  # Adjust if needed
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        "indicator": indicator,
                        "year": year,
                        "month": month,
                        "value": data.get("value"),
                        "unit": data.get("unit"),
                        "source": "INS API"
                    })
            except Exception as e:
                print(f"Error for {indicator} {year}-{month}: {e}")

with open("indicators_2018_2025_monthly.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ Saved all indicator data to indicators_2018_2025_monthly.json")