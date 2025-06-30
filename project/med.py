import requests
from bs4 import BeautifulSoup
import time
import os
from tqdm import tqdm
import sys

# Add the path to the local html2text module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../html2text/html2text-master')))
import html2text

BASE_URL = "https://www.med.tn/pagesmd_load.php"
HEADERS = {
    "accept": "*/*",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.med.tn",
    "referer": "https://www.med.tn/doctor",
    "user-agent": "Mozilla/5.0",
    "x-requested-with": "XMLHttpRequest"
}
COOKIES = {
    "_medid": "ac2d334d692f4057ad6c6401d91a0e03",
    "PHPSESSID": "3748acb21aaae500a8303146e8465abb",
    # (add any additional cookies if needed)
}

OUTPUT_FILE = "all_doctors.md"

def fetch_batch(start):
    payload = {
        "start": start, "spe": "", "gov": "", "del": "",
        "grandtunis": 0, "nearest": 0, "speciality": "",
        "arract": "", "city_country": "tn", "geo_country": "tn",
        "proximity": 0, "sponsor": "", "act_id": "",
        "nbMainList": 1679, "is_medinter": 0
    }
    r = requests.post(BASE_URL, headers=HEADERS, cookies=COOKIES, data=payload)
    r.raise_for_status()
    return r.text

def extract_profile_urls(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="card-doctor-block")
    urls = []
    for card in cards:
        a = card.find("a", href=True)
        if a and "med.tn/doctor/" in a["href"]:
            url = a["href"].strip()
            if url.startswith("/"):
                url = "https://www.med.tn" + url
            urls.append(url)
    return list(set(urls))

def fetch_profile_html(url):
    r = requests.get(url, headers=HEADERS, cookies=COOKIES)
    r.raise_for_status()
    return r.text

def main():
    visited = set()
    markdowns = []
    all_urls = []
    # First, collect all unique profile URLs
    for start in tqdm(range(0, 2001, 30), desc="Collecting profile URLs"):
        batch_html = fetch_batch(start)
        urls = extract_profile_urls(batch_html)
        if not urls:
            print("No profiles found in this batch. Ending early.")
            break
        for url in urls:
            if url not in visited:
                all_urls.append(url)
                visited.add(url)
        time.sleep(1)
    print(f"\nTotal unique profiles found: {len(all_urls)}")
    # Now, fetch and process each profile
    for url in tqdm(all_urls, desc="Processing profiles"):
        try:
            html = fetch_profile_html(url)
            md = html2text.html2text(html)
            markdowns.append(f"\n\n---\n# Doctor Profile: {url}\n\n" + md)
            time.sleep(1)
        except Exception as e:
            print("Error processing", url, e)
    # Write all markdown to a single file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(markdowns))
    print(f"\nDone! {len(markdowns)} profiles processed and saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
