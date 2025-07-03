import os
import requests
from langchain.agents import initialize_agent, Tool
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import html2text
from dotenv import load_dotenv
from langchain.schema import HumanMessage

# Load environment variables from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
SCRAPINGANT_API_KEY = os.getenv("SCRAPINGANT_API_KEY")

# Initialize Groq LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

# Define tools
def refine_query(query):
    """Refine the given search query to make it more effective."""
    prompt = PromptTemplate(
        input_variables=["query"],
        template="You are an expert in search optimization. Refine the following query for better web search results using inductive reasoning. Examples:\n" +
                 "Original: 'best restaurants'\nRefined: 'top rated restaurants in New York'\n" +
                 "Original: 'latest news'\nRefined: 'breaking news today'\n" +
                 "Now, refine this query: '{query}'"
    )
    response = llm([HumanMessage(content=prompt.format(query=query))])
    # If response is a list, get the first content
    if isinstance(response, list):
        return response[0].content.strip()
    return response.content.strip()

refine_tool = Tool(
    name="Refine Query",
    func=refine_query,
    description="Refine the search query for better search results using NLP."
)

def serp_search(query):
    """Search Google using SerpAPI and return top 10 URLs."""
    url = "https://serpapi.com/search"
    params = {"q": query, "api_key": SERP_API_KEY, "num": 10}
    response = requests.get(url, params=params)
    data = response.json()
    urls = [result["link"] for result in data.get("organic_results", [])]
    return "\n".join(urls)

serp_tool = Tool(
    name="Search Google",
    func=serp_search,
    description="Search Google and return the top 10 URLs as a newline-separated string."
)

# Initialize the agent
tools = [refine_tool, serp_tool]
agent = initialize_agent(
    tools,
    llm,
    agent_type="zero-shot-react-description",
    verbose=True
)

# Main function to process query, scrape, and save
def scrape_and_save(query):
    # Agent refines query and gets URLs
    prompt = (
        "You are a web scraping assistant. For the query '{query}', "
        "first refine it using the Refine Query tool, then use the Search Google tool "
        "to get the top 10 URLs. Output the URLs as a newline-separated list."
    ).format(query=query)
    response = agent.run(prompt)
    urls = response.split("\n")

    # Scrape and extract text from each URL
    texts = []
    for url in urls:
        if url.strip():
            try:
                api_url = f"https://api.scrapingant.com/v1/general?url={url}&api_key={SCRAPINGANT_API_KEY}&return_format=html"
                response = requests.get(api_url)
                if response.status_code == 200:
                    html_content = response.text
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    text = h.handle(html_content)
                    texts.append(f"Content from {url}:\n{text}")
            except Exception as e:
                print(f"Error scraping {url}: {e}")

    # Save all content to a text file
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n---\n".join(texts))

# Example usage
if __name__ == "__main__":
    user_query = input("Enter your search query: ")
    scrape_and_save(user_query)