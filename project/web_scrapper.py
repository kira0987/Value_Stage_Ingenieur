from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
import os
import streamlit as st
import requests
from groq import Groq
import time

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
    Use Groq's Llama model to generate three targeted search queries for finding lists or tables.
    The queries must be strictly Tunisia-oriented, focusing on Tunisia, its states, and governorates.
    Includes timing and timeout for debugging.
    """
    prompt = (
        "You are an expert at crafting Google search queries for Tunisian data. "
        "Generate three distinct Google search queries separated by '|||' to find public URLs containing lists or tables of professionals as specified in the user request. "
        "All queries must be strictly Tunisia-oriented: only use Tunisia, its states, or governorates as locations. "
        "Use Tunisian local terms, French language, and relevant domains (e.g., .tn, site:.gov.tn, site:.org.tn, site:.tn, etc.). "
        "The user request is: " + user_query + ". "
        "The first query should target Tunisian government websites using 'site:.gov.tn'. "
        "The second should target Tunisian professional directories or associations using 'inurl:annuaire', 'ordre', or similar. "
        "The third should target downloadable files like PDFs or CSVs using 'filetype:pdf' or 'filetype:csv' and Tunisian domains. "
        "Use operators like 'intext:\"liste des\"', 'intext:\"Nom\" intext:\"Spécialité\"', or French/Tunisian professional terms to prioritize structured data such as lists or tables. "
        "Avoid pages that require login by excluding terms like 'login' or 'sign in' where possible. "
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
            timeout=30  # If Groq SDK supports timeout
        )
        elapsed = time.time() - start
        st.write(f"Groq LLM response time: {elapsed:.2f} seconds")
        queries = response.choices[0].message.content.strip().split("|||")
        queries = [q.strip() for q in queries if q.strip()]
        while len(queries) < 3:
            queries.append(user_query)
    except Exception as e:
        st.warning(f"LLM failed to generate search queries: {e}. Using user query as fallback.")
        queries = [user_query] * 3
    return queries

def search_with_serper(query: str, max_results: int) -> list:
    """
    Perform a search using the Serper API and return formatted results. Includes timing and timeout.
    """
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERP_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": min(max_results, 20)}
    try:
        st.info(f"Searching Serper with query: {query}")
        start = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        elapsed = time.time() - start
        st.write(f"Serper API response time: {elapsed:.2f} seconds for query: {query}")
        response.raise_for_status()
        results = response.json().get("organic", [])
        return [
            {"url": result["link"], "title": result.get("title", ""), "snippet": result.get("snippet", "")}
            for result in results
        ]
    except Exception as e:
        st.error(f"Serper API search failed: {e}. No results available.")
        return []

def find_websites(user_query: str) -> dict:
    """
    Generate search queries and fetch relevant website results with lists or tables.
    Includes debug output for timing.
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
            fallback_query = user_query + " list directory"
            st.write(f"No results found with generated queries. Trying fallback query: {fallback_query}")
            fallback_results = search_with_serper(fallback_query, max_results=10)
            for res in fallback_results:
                url = res["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append(res)
        return {"results": results}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}

def main():
    st.set_page_config(page_title="Professional Directory Search", page_icon="🔍")
    st.title("🔍 Professional Directory Search")
    st.markdown("""
        Enter a query to find public websites with lists or tables of professionals, including names, specialties, phone numbers, addresses, and emails.
        **Examples**:
        - Doctors in Béja
        - Lawyers in Tunis
        - Engineers in Sousse
    """)

    with st.form(key="search_form"):
        query = st.text_input("Enter your search query:", placeholder="Doctors in Béja")
        submit_button = st.form_submit_button(label="Search")

    if submit_button and query:
        with st.spinner("Searching for directories..."):
            result = find_websites(query)
        if "error" in result:
            st.error(result["error"])
        else:
            results = result["results"]
            if results:
                st.success(f"Found {len(results)} websites that may contain professional directories:")
                for i, res in enumerate(results, 1):
                    st.markdown(f"### Result {i}: **{res['title']}**")
                    st.markdown(f"{res['snippet']}")
                    st.markdown(f"[Visit URL]({res['url']})")
                    st.markdown("---")
            else:
                st.warning("No results found, even with the fallback query. Try a different search term.")

if __name__ == "__main__":
    main()