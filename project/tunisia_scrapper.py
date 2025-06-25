from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
import os
import streamlit as st
import requests
from groq import Groq
import time
from playwright.sync_api import sync_playwright
import pandas as pd

# Load API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in .env file. Please set it in your .env file.")
    st.stop()
if not SERP_API_KEY:
    st.error("SERP_API_KEY not found in .env file. Please set it in your .env file.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def generate_search_query_with_llama(user_query: str) -> list:
    """
    Use Groq's Llama model to generate three targeted search queries for finding structured data about Tunisia.
    """
    prompt = (
        "You are an expert at crafting Google search queries for finding information about Tunisia. "
        "Generate three distinct Google search queries separated by '|||' to find public URLs containing relevant structured data about Tunisia, "
        "such as lists, tables, reports, statistics, or other organized information, based on the user's query: " + user_query + ". "
        "The queries must be strictly Tunisia-oriented, focusing on Tunisia, its states, and governorates. "
        "Use Tunisian local terms, French language, and relevant domains (e.g., .tn, site:.gov.tn, site:.org.tn, site:.tn, etc.). "
        "Tailor the queries to the specific type of information requested in the user's query. "
        "For example, if the query is about professionals, target directories or lists; if it's about economic data, target reports or statistical tables; "
        "if it's about general topics, target pages with structured content like tables or bullet points. "
        "Use operators like 'intext:', 'intitle:', 'filetype:', etc., to prioritize relevant content. "
        "Avoid pages that require login by excluding terms like 'login' or 'sign in' where possible. "
        "The first query should target Tunisian government websites using 'site:.gov.tn'. "
        "The second should target Tunisian educational or research institutions using 'site:.edu.tn' or similar. "
        "The third should target downloadable files like PDFs or CSVs using 'filetype:pdf' or 'filetype:csv' and Tunisian domains. "
        "Do not generate queries for any country other than Tunisia."
    )
    try:
        st.info("Generating search queries with Llama...")
        start = time.time()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150,
            timeout=30
        )
        elapsed = time.time() - start
        st.write(f"Groq LLM response time: {elapsed:.2f} seconds")
        queries = response.choices[0].message.content.strip().split("|||")
        queries = [q.strip() for q in queries if q.strip()]
        while len(queries) < 3:
            queries.append(user_query)
    except Exception as e:
        st.warning(f"LLM failed: {e}. Using user query as fallback.")
        queries = [user_query] * 3
    return queries

def search_with_serper(query: str, max_results: int) -> list:
    """
    Perform a search using the Serper API and return formatted results.
    """
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERP_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": min(max_results, 20)}
    try:
        st.info(f"Searching Serper with query: {query}")
        start = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        elapsed = time.time() - start
        st.write(f"Serper API response time: {elapsed:.2f} seconds")
        response.raise_for_status()
        results = response.json().get("organic", [])
        return [
            {"url": result["link"], "title": result.get("title", ""), "snippet": result.get("snippet", "")}
            for result in results
        ]
    except Exception as e:
        st.error(f"Serper API failed: {e}")
        return []

def extract_data_with_playwright(url: str, user_query: str) -> str:
    """
    Use Playwright to load a page and extract structured data (tables) relevant to the user query.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)  # Wait for JS to load
            
            # Extract all tables
            tables = page.query_selector_all("table")
            if tables:
                for table in tables:
                    # Convert table to DataFrame
                    rows = table.query_selector_all("tr")
                    data = []
                    for row in rows:
                        cols = row.query_selector_all("td, th")
                        data.append([col.inner_text() for col in cols])
                    if data:
                        df = pd.DataFrame(data[1:], columns=data[0] if len(data) > 1 else None)
                        # Check if table content relates to query
                        if any(user_query.lower() in str(cell).lower() for row in data for cell in row):
                            browser.close()
                            return df.to_html(index=False)
            browser.close()
            return "No relevant tables found on this page."
    except Exception as e:
        return f"Playwright extraction failed: {e}"

def find_websites(user_query: str) -> dict:
    """
    Generate search queries and fetch relevant website results with structured data about Tunisia.
    """
    try:
        queries = generate_search_query_with_llama(user_query)
        results = []
        seen_urls = set()
        for query in queries:
            current_results = search_with_serper(query, max_results=10)
            for res in current_results:
                url = res["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append(res)
        if not results:
            fallback_query = user_query
            st.write(f"No results with generated queries. Using fallback: {fallback_query}")
            fallback_results = search_with_serper(fallback_query, max_results=10)
            for res in fallback_results:
                url = res["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append(res)
        return {"results": results}
    except Exception as e:
        return {"error": f"Error occurred: {e}"}

def main():
    st.set_page_config(page_title="Tunisia Information Search", page_icon="🔍")
    st.title("🔍 Tunisia Information Search")
    st.markdown("""
        Enter a query to find public websites with structured information about Tunisia, such as lists, tables, reports, or statistics.
        **Examples**:
        - Economic indicators in Tunisia
        - Doctors in Béja
        - Tourist attractions in Sousse
        - History of Carthage
    """)

    with st.form(key="search_form"):
        query = st.text_input("Enter your query about Tunisia:", placeholder="Economic indicators in Tunisia")
        submit_button = st.form_submit_button(label="Search")

    if submit_button and query:
        with st.spinner("Searching for information..."):
            result = find_websites(query)
        if "error" in result:
            st.error(result["error"])
        else:
            results = result["results"]
            if results:
                st.success(f"Found {len(results)} websites with potential information:")
                for i, res in enumerate(results, 1):
                    st.markdown(f"### Result {i}: **{res['title']}**")
                    st.markdown(f"{res['snippet']}")
                    st.markdown(f"[Visit URL]({res['url']})")
                    if st.button(f"Extract Data from Result {i}", key=f"extract_{i}"):
                        with st.spinner(f"Extracting data from {res['url']}..."):
                            extracted_data = extract_data_with_playwright(res["url"], query)
                            st.markdown("#### Extracted Data:")
                            st.write(extracted_data, unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.warning("No results found. Try a different query.")

if __name__ == "__main__":
    main()