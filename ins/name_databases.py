# Requirements: pip install selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def extract_labels(url, output_txt):
    # Setup Chrome WebDriver (download chromedriver and ensure it's in PATH)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # wait for JS to render

    labels = set()

    def recurse(parent):
        # find all checkboxes and tree items under this parent
        elems = parent.find_elements(By.CSS_SELECTOR, 'label, .tree-node, input[type="checkbox"]')
        for el in elems:
            txt = el.text.strip()
            if txt:
                labels.add(txt)
        # recursively traverse child containers if any
        containers = parent.find_elements(By.CSS_SELECTOR, '.tree-node-children, .subtree')
        for cont in containers:
            recurse(cont)

    recurse(driver)

    driver.quit()

    with open(output_txt, 'w', encoding='utf-8') as f:
        for label in sorted(labels):
            f.write(label + '\n')

if __name__ == '__main__':
    url = 'http://dataportal.ins.tn/fr/DataAnalysis'
    extract_labels(url, 'tree_and_checkbox_labels.txt')
    print(f"✅ Extracted {len(open('tree_and_checkbox_labels.txt').read().splitlines())} labels.")
