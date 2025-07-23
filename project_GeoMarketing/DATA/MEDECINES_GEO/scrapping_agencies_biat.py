from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json
import re

# Setup Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Load page
driver.get("https://www.biat.com.tn/nos-agences")
time.sleep(5)

# Scroll to the bottom to trigger lazy loading
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# Force reveal hidden content (if applicable)
driver.execute_script("""
    let hidden = document.querySelectorAll('.js-hide, [style="display: none;"]');
    hidden.forEach(el => el.style.display = 'block');
""")
time.sleep(2)

# Extract the full DOM
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
driver.quit()

agences = []

# Loop through rows from 0 to 202
for index in range(203):  # 0 to 202 inclusive
    try:
        # Construct the selector for the row
        row_selector = f'div[data-views-row-index="{index}"]'
        row = soup.select_one(row_selector)
        if not row:
            continue

        # Extract latitude and longitude
        latitude = row.select_one('meta[property="latitude"]')['content']
        longitude = row.select_one('meta[property="longitude"]')['content']

        # Extract agency name
        name_tag = row.select_one('div.field--name-node-title.field--type-ds.field--label-hidden.field__item h2')
        name = name_tag.get_text(strip=True) if name_tag else ""

        # Extract other fields
        gouvernorat_tag = row.select_one('div.field--name-field-gouvernorat .field__item')
        address_tag = row.select_one('div.field--name-field-adresse .field__item')
        fax_tag = row.select_one('div.field--name-field-fax .field__item')
        tel_tag = row.select_one('div.field--name-field-tel- .field__item')

        gouvernorat = gouvernorat_tag.get_text(strip=True) if gouvernorat_tag else ""
        address_full = address_tag.get_text(strip=True) if address_tag else ""
        fax = fax_tag.get_text(strip=True) if fax_tag else ""
        tel = tel_tag.get_text(strip=True) if tel_tag else ""

        # Extract postal code from address
        postal_code_match = re.search(r'\b\d{4}\b', address_full)
        code_postal = postal_code_match.group() if postal_code_match else ""

        agences.append({
            "Nom_Agence": name,
            "Gouvernorat": gouvernorat,
            "Adresse": address_full,
            "Code_Postal": code_postal,
            "Fax": fax,
            "Tel": tel,
            "latitude": latitude,
            "longitude": longitude
        })

    except Exception as e:
        print(f"Error at index {index}: {e}")
        continue

# Save to JSON file
with open('agences_biat_4.json', 'w', encoding='utf-8') as f:
    json.dump(agences, f, ensure_ascii=False, indent=4)

print(f"{len(agences)} agences saved.")