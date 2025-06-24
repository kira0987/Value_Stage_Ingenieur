from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://dataportal.ins.tn/fr/DataAnalysis")
    page.wait_for_selector("input.PPTextBoxInput")  # Wait for the indicators to load
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")
inputs = soup.find_all("input", class_="PPTextBoxInput")

values = [inp.get("value", "").strip() for inp in inputs if inp.get("value")]

with open("indicators.txt", "w", encoding="utf-8") as f:
    for val in values:
        f.write(val + "\n")

print(f"✅ Extracted {len(values)} indicators to indicators.txt")

# Load the HTML file
with open("Portail de données de la Tunisie, Analyse de Données.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find the "Lignes" label to locate the right section
lignes_label = soup.find("div", class_="PPLabel PPEaxDimBarLabelBase PPEaxDimBarLabel PPC Released RowsLabel")
if not lignes_label:
    print("Could not find the 'Lignes' label.")
    exit()

# The indicators box is after the "Lignes" label, so find the next input(s) in the same control bar
indicators = []
for sibling in lignes_label.find_all_next("input", class_="PPTextBoxInput"):
    value = sibling.get("value", "").strip()
    if value and value.lower() not in ["lignes", "fixe", "unité", "tunisie", "colonnes", "période"]:
        indicators.append(value)
    # Stop if we reach another section (like "Fixés" or "Régions")
    parent = sibling.find_parent("div", class_="PPLabel PPEaxDimBarLabelBase PPEaxDimBarLabel PPC Released FixedLabel")
    if parent:
        break

# Save to file
with open("indicators_from_lignes.txt", "w", encoding="utf-8") as f:
    for ind in indicators:
        f.write(ind + "\n")

print(f"Extracted {len(indicators)} indicator(s) from the Lignes box to indicators_from_lignes.txt")
