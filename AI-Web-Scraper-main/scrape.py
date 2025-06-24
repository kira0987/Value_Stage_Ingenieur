from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import urllib.robotparser
from urllib.parse import urlparse

load_dotenv()

# SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")  # No longer needed


def can_fetch_url(url, user_agent="*"):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        print(f"Could not read robots.txt: {e}")
        # If robots.txt can't be read, default to allowing
        return True
    return rp.can_fetch(user_agent, url)


def scrape_website(website):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    if not can_fetch_url(website, user_agent):
        print("Scraping disallowed by robots.txt.")
        return "Scraping disallowed by robots.txt."
    print("Connecting to local ChromeDriver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    with webdriver.Chrome(options=options) as driver:
        driver.get(website)
        # If you have captcha solving logic, you may need to adapt or remove it
        # print("Waiting captcha to solve...")
        # solve_res = driver.execute(
        #     "executeCdpCommand",
        #     {
        #         "cmd": "Captcha.waitForSolve",
        #         "params": {"detectTimeout": 10000},
        #     },
        # )
        # print("Captcha solve status:", solve_res["value"]["status"])
        print("Navigated! Scraping page content...")
        html = driver.page_source
        return html


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text or further process the content
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]
