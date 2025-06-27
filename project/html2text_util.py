import streamlit as st
import requests
import sys
import os
from urllib.parse import urljoin
import io

# Add the path to the local html2text module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../html2text/html2text-master')))
import html2text

def html_from_url_requests(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text, None
    except Exception as e:
        return None, str(e)

def html_from_url_selenium(url):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        html = driver.page_source
        driver.quit()
        return html, None
    except Exception as e:
        return None, f"Selenium error: {e}"

def html_from_url_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
        def get_html():
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                html = page.content()
                browser.close()
                return html
        html = get_html()
        return html, None
    except Exception as e:
        return None, f"Playwright error: {e}"

def html2text_convert(html):
    return html2text.html2text(html)

def find_next_page_link(html, base_url):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None, 'BeautifulSoup4 is required for pagination extraction.'
    soup = BeautifulSoup(html, 'html.parser')
    # Try rel="next" first
    next_link = soup.find('a', rel=lambda x: x and 'next' in x)
    if next_link and next_link.get('href'):
        return urljoin(base_url, next_link['href']), None
    # Fallback: look for pagination div and find the next increment
    pag_div = soup.find('div', class_=lambda c: c and 'pagination' in c)
    if pag_div:
        # Find all page number links
        page_links = pag_div.find_all('a', href=True)
        current_found = False
        for a in page_links:
            # Try to find the current page, then pick the next one
            if 'active' in (a.get('class') or []):
                current_found = True
                continue
            if current_found:
                return urljoin(base_url, a['href']), None
        # Or just pick the last one if no active found
        if page_links:
            return urljoin(base_url, page_links[-1]['href']), None
    return None, None

st.title('HTML to Text (Markdown) Converter')

url = st.text_input('Enter a URL to convert its HTML to text:')
method = st.selectbox('Choose fetching method:', ['requests (fast, static)', 'selenium (dynamic)', 'playwright (dynamic)'])
paginate = st.checkbox('Follow pagination (extract all pages incrementally)', value=True)

if url:
    with st.spinner('Fetching and converting...'):
        fetch_func = {
            'requests (fast, static)': html_from_url_requests,
            'selenium (dynamic)': html_from_url_selenium,
            'playwright (dynamic)': html_from_url_playwright
        }[method]
        all_htmls = []
        visited = set()
        page_url = url
        page_num = 1
        while page_url and page_url not in visited:
            html, error = fetch_func(page_url)
            if error:
                st.warning(f"Failed to fetch {page_url}: {error}")
                break
            all_htmls.append((page_url, html))
            visited.add(page_url)
            if not paginate:
                break
            next_url, err = find_next_page_link(html, page_url)
            if err:
                st.error(err)
                break
            if next_url and next_url not in visited:
                st.write(f"Fetching page {page_num+1}: {next_url}")
            page_url = next_url
            page_num += 1
        # Paginate output in UI
        num_pages = len(all_htmls)
        if num_pages == 0:
            st.error('No pages fetched.')
        else:
            if num_pages > 50:
                st.warning(f"Large result: {num_pages} pages. Only one page is shown at a time. Use the download button for the full result.")
            page_options = [f"Page {i+1}: {url}" for i, (url, _) in enumerate(all_htmls)]
            selected = st.selectbox('Select page to display:', page_options, index=0)
            selected_idx = page_options.index(selected)
            page_url, html = all_htmls[selected_idx]
            text = html2text_convert(html)
            st.subheader(f'Converted Text for {page_url}:')
            st.code(text)
            # Download full result
            combined_text = ''
            for page_url, html in all_htmls:
                combined_text += f"\n\n--- Page: {page_url} ---\n\n"
                combined_text += html2text_convert(html)
            st.download_button('Download full result as .txt', data=combined_text, file_name='all_pages.txt')
