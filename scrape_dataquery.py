import time
import json
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

URL = "http://dataportal.ins.tn/fr/DataQuery"
ROBOTS_URL = "http://dataportal.ins.tn/robots.txt"
INDICATORS = [
    "Produit Intérieur Brut (aux prix du marché)", "Revenus des facteurs reçus de l'extérieur nets",
    "REVENU NATIONAL", "Autres transferts courants extérieurs nets", "REVENU NATIONAL DISPONIBLE BRUT",
    "Sociétés non financières", "Institutions financières", "Administration Publique", "Ménages",
    "Amortissements", "REVENU NATIONAL NET", "REVENU NATIONAL DISPONIBLE", "Consommation Finale",
    "EPARGNE NATIONALE (BRUTE)", "EPARGNE NATIONALE (NETTE)", "Taux d'épargne par agent",
    "TAUX D'EPARGNE", "Population (en milliers)", "Nombre de ménage (en milliers)",
    "Taille moyenne d'un ménage", "INDICE DES PRIX A LA CONSOMMATION FAMILIALE (IPC; 2015=100)",
    "REVENU DISPONIBLE BRUT DES MENAGES en MD", "Accroissement",
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars courants",
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars de 2015",
    "GFCF by Institutional Sectors (MD)", "Non-Financial Corporations (NFCs)",
    "Financial Institution", "Public Administration", "Householders (housing)",
    "TOTAL GENERAL", "Inflation", "RNDB (MD 2015)", "RNDB/Personne"
]

PROMPT = PromptTemplate(
    input_variables=["html", "indicator", "matched_name"],
    template=(
        "You are an expert at reading web page HTML. "
        "Given the following HTML from a data portal, extract all available data for the indicator: {indicator}. "
        "The indicator may appear under a similar or related name: {matched_name}. "
        "The HTML may contain folders, buttons, and dynamic elements. "
        "Analyze the structure, and if you see folders or buttons, describe what you see and extract any visible data for the indicator. "
        "Return your answer as a JSON list of objects with keys: indicator, year, value, unit, source. "
        "If you cannot find the indicator, return an empty list. "
        "HTML: {html}"
    )
)

llm = OllamaLLM(model="llama3.1:latest", base_url="http://localhost:11434")
nlp_model = SentenceTransformer('all-MiniLM-L6-v2')

def check_robots_txt(url, robots_url):
    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    allowed = rp.can_fetch("*", url)
    print(f"Robots.txt allows scraping {url}: {allowed}")
    return allowed

def interact_with_page(driver):
    time.sleep(2)
    # Try to click all expandable elements (generic selectors)
    buttons = driver.find_elements(By.CSS_SELECTOR, "button, .folder, .expand, .toggle")
    for btn in buttons:
        try:
            btn.click()
            time.sleep(0.5)
        except Exception:
            continue
    time.sleep(2)  # Wait for content to load

def get_full_html(url):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    interact_with_page(driver)
    html = driver.page_source
    driver.quit()
    return html

def extract_possible_indicators(soup):
    # Try to extract all possible indicator names from tables, headers, etc.
    found = set()
    for tag in soup.find_all(['th', 'td', 'a', 'span', 'div', 'label', 'button']):
        text = tag.get_text(strip=True)
        if text and len(text) > 3:
            found.add(text)
    return list(found)

def find_best_indicator_match(target, candidates, threshold=0.7):
    target_emb = nlp_model.encode([target])
    candidates_emb = nlp_model.encode(candidates)
    sims = cosine_similarity(target_emb, candidates_emb)[0]
    best_idx = np.argmax(sims)
    if sims[best_idx] >= threshold:
        return candidates[best_idx], float(sims[best_idx])
    return None, None

def main():
    if not check_robots_txt(URL, ROBOTS_URL):
        print("Scraping is not allowed by robots.txt. Exiting.")
        return

    html = get_full_html(URL)
    soup = BeautifulSoup(html, "html.parser")
    found_indicators = extract_possible_indicators(soup)
    results = []

    for indicator in INDICATORS:
        matched_name, score = find_best_indicator_match(indicator, found_indicators)
        if matched_name:
            print(f"'{indicator}' best matches '{matched_name}' (score: {score:.2f})")
        else:
            print(f"No good match found for '{indicator}', using original name.")
            matched_name = indicator
        try:
            llm_result = llm(PROMPT.format(html=html[:12000], indicator=indicator, matched_name=matched_name))
            data = json.loads(llm_result)
            results.extend(data)
            print(f"Extracted for {indicator}: {data}")
        except Exception as e:
            print(f"LLM extraction failed for {indicator}: {e}")

    with open("output_dataquery_llm.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved results to output_dataquery_llm.json")

if __name__ == "__main__":
    main() 