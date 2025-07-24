import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.biat.com.tn/biat-la-une/actualites?meta_key=&keyword=&filter_theme=All&current_path=%2Fnode%2F49"
SITE_BASE = "https://www.biat.com.tn"
OUTPUT_FILE = "actualite_biat.json"


def get_soup(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_detail_links(soup):
    # Find all <a> under <div class="view-content row">
    container = soup.find("div", class_="view-content row")
    if not container:
        return []
    links = []
    for a in container.find_all("a", href=True):
        href = a["href"]
        # Only keep internal links (not anchors or JS)
        if href.startswith("/"):
            links.append(SITE_BASE + href)
        elif href.startswith("http"):
            links.append(href)
    return list(set(links))  # Remove duplicates


def get_next_page_url(soup):
    # Find the pagination section
    pag = soup.find("ul", class_="pagination js-pager__items")
    if not pag:
        return None
    next_li = pag.find("a", rel="next")
    if next_li:
        next_href = next_li.get("href")
        if next_href:
            if next_href.startswith("/"):
                return SITE_BASE + next_href
            else:
                return SITE_BASE + "/biat-la-une/actualites" + next_href
    return None


def scrape_detail_page(url):
    soup = get_soup(url)
    ps = [p.get_text(strip=True) for p in soup.find_all("p")]
    return ps


def main():
    results = []
    page_url = BASE_URL
    id_counter = 1
    visited_detail_urls = set()
    while page_url:
        print(f"Scraping page: {page_url}")
        soup = get_soup(page_url)
        detail_links = get_detail_links(soup)
        for link in detail_links:
            if link in visited_detail_urls:
                continue
            print(f"  Scraping detail: {link}")
            try:
                ps = scrape_detail_page(link)
            except Exception as e:
                print(f"    Failed: {e}")
                continue
            results.append({
                "id": id_counter,
                "url": link,
                "paragraphs": ps
            })
            id_counter += 1
            visited_detail_urls.add(link)
            time.sleep(0.5)  # Be polite
        next_page = get_next_page_url(soup)
        if next_page and next_page != page_url:
            page_url = next_page
            time.sleep(1)
        else:
            break
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done. {len(results)} detail pages scraped. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
