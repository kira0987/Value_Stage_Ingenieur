import requests
from bs4 import BeautifulSoup
import os

# URL of the directory to scrape
url = "https://www.bct.gov.tn/bct/siteprod/documents/"

# Output text file to store PDF names
output_file = "pdf_names.txt"

try:
    # Send HTTP request without proxies
    response = requests.get(url)
    response.raise_for_status()  # Check for HTTP errors

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links in the page
    pdf_files = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Check if the link ends with .pdf
        if href.lower().endswith('.pdf'):
            # Extract the filename from the URL
            filename = os.path.basename(href)
            pdf_files.append(filename)

    # Remove duplicates and sort
    pdf_files = sorted(set(pdf_files))

    # Write PDF names to a text file
    with open(output_file, 'w', encoding='utf-8') as f:
        for pdf in pdf_files:
            f.write(pdf + '\n')

    print(f"Found {len(pdf_files)} PDF files. Saved to {output_file}")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        print("Error: 403 Forbidden - The server is denying access. The directory may require authentication or be restricted.")
    else:
        print(f"HTTP Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to the site: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# If no PDFs were found, indicate possible issues
if 'pdf_files' in locals() and not pdf_files:
    print("No PDF files found. The directory may not list files, or access is restricted.")