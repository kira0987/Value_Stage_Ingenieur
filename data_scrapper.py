import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from fuzzywuzzy import fuzz
import time
import os

# List of indicators
INDICATORS = [
    "Produit Intérieur Brut (aux prix du marché)",
    "Revenus des facteurs reçus de l'extérieur nets",
    "REVENU NATIONAL",
    "Autres transferts courants extérieurs nets",
    "REVENU NATIONAL DISPONIBLE BRUT",
    "Sociétés non financières",
    "Institutions financières",
    "Administration Publique",
    "Ménages",
    "Amortissements",
    "REVENU NATIONAL NET",
    "REVENU NATIONAL DISPONIBLE",
    "Consommation Finale",
    "EPARGNE NATIONALE (BRUTE)",
    "EPARGNE NATIONALE (NETTE)",
    "Taux d'épargne par agent",
    "TAUX D'EPARGNE",
    "Population (en milliers)",
    "Nombre de ménage (en milliers)",
    "Taille moyenne d'un ménage",
    "INDICE DES PRIX A LA CONSOMMATION FAMILIALE (IPC; 2015=100)",
    "REVENU DISPONIBLE BRUT DES MENAGES en MD",
    "Accroissement",
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars courants",
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars de 2015",
    "GFCF by Institutional Sectors (MD)",
    "Non-Financial Corporations (NFCs)",
    "Financial Institution",
    "Public Administration",
    "Householders (housing)",
    "TOTAL GENERAL",
    "Inflation",
    "RNDB (MD 2015)",
    "RNDB/Personne"
]

# Download directory
download_dir = "C:/Users/msi/OneDrive - ESPRIT/Desktop/stage value/project/testing/downloads"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Attempt direct download using requests (preferred method)
def try_direct_download(indicator):
    try:
        # Placeholder URL and parameters (replace with actual after network inspection)
        url = "http://dataportal.ins.tn/fr/DataAnalysis/download"  # Replace with actual download URL
        params = {
            "indicator": indicator,  # May need encoding or specific format
            "start_date": "2018-01-01",
            "end_date": "2025-12-31",
            "format": "xlsx"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            file_name = f"{indicator.replace('/', '_').replace(':', '_')}.xlsx"
            file_path = os.path.join(download_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded via requests: {file_name}")
            return True
        else:
            print(f"Direct download failed for '{indicator}' (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"Direct download error for '{indicator}': {e}")
        return False

# Fallback to Selenium if direct download fails
def try_selenium_download(driver, indicator):
    print(f"Processing with Selenium: {indicator}")
    try:
        # Try dropdown (replace 'indicator-select' with actual ID)
        try:
            indicators_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "indicator-select"))  # Replace with actual ID
            )
            select = Select(indicators_select)
            options = select.options
            best_match = indicator
            best_score = 0
            for option in options:
                score = fuzz.partial_ratio(indicator.lower(), option.text.lower())
                if score > best_score and score >= 80:
                    best_score = score
                    best_match = option.text
            if best_score >= 80:
                select.select_by_visible_text(best_match)
                print(f"Selected dropdown: {best_match} (Score: {best_score})")
            else:
                print(f"No dropdown match for '{indicator}', trying search box.")
                raise Exception("No dropdown match")
        except:
            # Try search box (replace 'indicator_search' with actual ID)
            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "indicator_search"))  # Replace with actual ID
                )
                search_box.clear()
                search_box.send_keys(indicator)
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btn_search"))  # Replace with actual ID
                )
                search_button.click()
                results = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "result-item"))  # Replace with actual class
                )
                best_score = 0
                best_result = None
                for result in results:
                    text = result.text
                    score = fuzz.partial_ratio(indicator.lower(), text.lower())
                    if score > best_score and score >= 80:
                        best_score = score
                        best_result = result
                if best_score >= 80 and best_result:
                    best_result.click()
                    print(f"Selected search result: {best_result.text} (Score: {best_score})")
                else:
                    print(f"No search result match for '{indicator}'")
                    return False
            except:
                print(f"Search box failed for '{indicator}'")
                return False

        # Wait for indicator page (replace 'indicator-page' with actual ID)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "indicator-page"))  # Replace with actual ID
        )

        # Set date range (replace 'from_date' and 'to_date' with actual IDs)
        try:
            start_date = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "from_date"))  # Replace with actual ID
            )
            start_date.clear()
            start_date.send_keys("2018-01-01")
            end_date = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "to_date"))  # Replace with actual ID
            )
            end_date.clear()
            end_date.send_keys("2025-12-31")
        except Exception as e:
            print(f"Failed to set date range for '{indicator}': {e}")
            return False

        # Export (replace 'export_excel' with actual ID)
        try:
            initial_files = set(os.listdir(download_dir))
            export_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "export_excel"))  # Replace with actual ID
            )
            export_button.click()
            timeout = 30
            start_time = time.time()
            while time.time() - start_time < timeout:
                current_files = set(os.listdir(download_dir))
                new_files = current_files - initial_files
                if new_files:
                    latest_file = max(new_files, key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
                    new_name = f"{indicator.replace('/', '_').replace(':', '_')}.xlsx"
                    os.rename(
                        os.path.join(download_dir, latest_file),
                        os.path.join(download_dir, new_name)
                    )
                    print(f"Downloaded via Selenium: {new_name}")
                    return True
                time.sleep(2)
            print(f"Download timeout for '{indicator}'")
            return False
        except Exception as e:
            print(f"Export failed for '{indicator}': {e}")
            return False

    except Exception as e:
        print(f"Selenium error for '{indicator}': {e}")
        return False

# Main execution
driver = None
try:
    # Initialize Selenium driver only if needed
    for indicator in INDICATORS:
        # Try direct download first
        if try_direct_download(indicator):
            continue
        
        # Fallback to Selenium
        if driver is None:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("prefs", {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            driver = webdriver.Chrome(options=options)
            driver.get("http://dataportal.ins.tn/fr/DataAnalysis")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        if not try_selenium_download(driver, indicator):
            print(f"Failed to download '{indicator}'")
        driver.back()  # Return to main page for next indicator

finally:
    if driver:
        driver.quit()