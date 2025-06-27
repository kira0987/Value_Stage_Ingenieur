import os
import json
import requests
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import hashlib
import time
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env')
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Forbidden keywords to exclude irrelevant sites
forbidden_keywords = ["facebook.com", "linkedin.com", "instagram.com", "huggingface.co", "login", "signin", "recaptcha"]

# Utility functions
def safe_filename(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def safe_dirname(s):
    name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s)[:50]
    return name.strip() or "query"

def search_urls(query: str, max_results: int = 10) -> list:
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERP_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": min(max_results, 20)}
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            results = response.json().get("organic", [])
            return [
                {"url": result["link"], "title": result.get("title", ""), "snippet": result.get("snippet", "")}
                for result in results
            ]
        except Exception as e:
            st.warning(f"Search attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    st.error("Failed to fetch URLs after retries")
    return []

def download_file(url, dest_folder):
    try:
        local_filename = os.path.join(dest_folder, os.path.basename(urlparse(url).path))
        r = requests.get(url, stream=True, timeout=15)
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_filename
    except Exception as e:
        st.warning(f"Failed to download {url}: {e}")
        return None

def parse_and_download_files(html, base_url, dest_folder):
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    downloaded = []
    for link in links:
        href = link['href']
        if any(href.lower().endswith(ext) for ext in ['.pdf', '.csv', '.xls', '.xlsx']):
            file_url = urljoin(base_url, href)
            local_file = download_file(file_url, dest_folder)
            if local_file:
                downloaded.append(local_file)
    return downloaded

def extract_api_endpoints_with_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    api_results = []
    try:
        driver.get(url)
        time.sleep(10)
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                message = json.loads(entry['message'])['message']
                if message['method'] == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    api_url = request['url']
                    method = request['method']
                    if method in ['GET', 'POST'] and (
                        '/api/' in api_url or api_url.endswith('.json') or 'rest' in api_url or 'service' in api_url
                    ):
                        api_results.append(api_url)
            except Exception:
                continue
    finally:
        driver.quit()
    return list(set(api_results))

def fetch_and_save_api_data(api_urls, dest_folder):
    api_data = []
    for api_url in api_urls:
        try:
            r = requests.get(api_url, timeout=10)
            r.raise_for_status()
            filename = safe_filename(api_url) + '.json'
            file_path = os.path.join(dest_folder, filename)
            with open(file_path, 'wb') as f:
                f.write(r.content)
            api_data.append({'url': api_url, 'file': file_path, 'status': r.status_code})
        except Exception as e:
            api_data.append({'url': api_url, 'error': str(e)})
    return api_data

def process_url(url, base_folder):
    url_hash = safe_filename(url)
    url_folder = os.path.join(base_folder, url_hash)
    os.makedirs(url_folder, exist_ok=True)
    summary = {'url': url, 'downloaded_files': [], 'api_data': []}
    # Download HTML
    try:
        html = requests.get(url, timeout=15).text
        with open(os.path.join(url_folder, 'page.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        summary['html_saved'] = True
    except Exception as e:
        summary['html_saved'] = False
        summary['error'] = str(e)
        return summary
    # Download files (PDF, CSV, XLS, etc.)
    summary['downloaded_files'] = parse_and_download_files(html, url, url_folder)
    # Extract and download API data
    api_endpoints = extract_api_endpoints_with_selenium(url)
    summary['api_endpoints'] = api_endpoints
    summary['api_data'] = fetch_and_save_api_data(api_endpoints, url_folder)
    # Save summary
    with open(os.path.join(url_folder, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary

def main():
    st.set_page_config(page_title="Tunisian Professional Data Downloader", page_icon="📥")
    st.title("📥 Tunisian Professional Data Downloader")
    st.markdown("""
        Enter a query to find and download public data (HTML, PDFs, CSVs, APIs) about Tunisian professionals (doctors, lawyers, engineers).
        The app will search, download, and organize all found data for you.
    """)
    user_query = st.text_input("Search query:", placeholder="Tunisian lawyers in Tunis")
    if st.button("Search and Download"):
        with st.spinner("Searching and downloading data..."):
            search_query = f"{user_query} site:.tn OR site:.gov.tn OR site:.org.tn"
            st.write(f"Searching: {search_query}")
            results = search_urls(search_query, max_results=10)
            if not results:
                st.warning("No results found.")
                return
            safe_query = safe_dirname(user_query)
            base_folder = os.path.join('downloads', safe_query)
            os.makedirs(base_folder, exist_ok=True)
            all_summaries = []
            for i, res in enumerate(results, 1):
                url = res['url']
                if any(k in url.lower() for k in forbidden_keywords):
                    st.write(f"Skipping {url} (forbidden)")
                    continue
                st.write(f"Processing {i}/{len(results)}: {url}")
                summary = process_url(url, base_folder)
                all_summaries.append(summary)
                st.write(f"Done: {url}")
            # Save all summaries
            with open(os.path.join(base_folder, 'all_summaries.json'), 'w', encoding='utf-8') as f:
                json.dump(all_summaries, f, indent=2, ensure_ascii=False)
            st.success(f"All data downloaded and organized in {base_folder}/")
            st.download_button(
                label="Download Summary JSON",
                data=json.dumps(all_summaries, ensure_ascii=False, indent=2),
                file_name=f"summary_{safe_query}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()