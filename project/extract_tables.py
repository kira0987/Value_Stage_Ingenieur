import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from bs4 import BeautifulSoup
import time
import tempfile
import os

st.set_page_config(page_title="Table Extractor", page_icon="📄")
st.title("📄 HTML Table Extractor")

st.markdown("""
Enter a URL. The app will load the page, extract the first HTML table it finds, and let you download it as a CSV.
""")

url = st.text_input("Enter a URL to extract a table from:")

if st.button("Extract Table"):
    if not url:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("Loading page and extracting table..."):
            # Set up Selenium with headless Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=chrome_options)

            try:
                driver.get(url)
                time.sleep(3)  # Wait for JS to load, adjust as needed

                # Get page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "html.parser")
                table = soup.find("table")
                if table is None:
                    st.error("No table found on this page.")
                else:
                    # Read table into DataFrame
                    df = pd.read_html(str(table))[0]
                    st.dataframe(df)

                    # Download as CSV
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download table as CSV",
                        data=csv,
                        file_name="extracted_table.csv",
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                driver.quit()
