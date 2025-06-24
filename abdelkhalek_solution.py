from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import wbdata
import pandas as pd
from datetime import datetime
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
import os
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pdfplumber
from urllib.robotparser import RobotFileParser
import re
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Economic Data API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Constants
DATA_DIR = "economic_data"
PDFS_DIR = os.path.join(DATA_DIR, "pdfs")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

# Create directories
os.makedirs(PDFS_DIR, exist_ok=True)

# Indicator mapping
INDICATOR_SOURCES = {
    "Produit Intérieur Brut (aux prix du marché)": {"source": "World Bank", "code": "NY.GDP.MKTP.KD.ZG", "frequency": "quarterly", "url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=TN"},
    "Revenus des facteurs reçus de l'extérieur nets": {"source": "World Bank", "code": "NY.GNP.MKTP.CD - NY.GDP.MKTP.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.GNP.MKTP.CD?locations=TN"},
    "REVENU NATIONAL": {"source": "World Bank", "code": "NY.GNP.MKTP.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.GNP.MKTP.CD?locations=TN"},
    "Autres transferts courants extérieurs nets": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "REVENU NATIONAL DISPONIBLE BRUT": {"source": "World Bank", "code": "NY.ADJ.NNAT.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.ADJ.NNAT.CD?locations=TN"},
    "Sociétés non financières": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Institutions financières": {"source": "BCT", "url": "https://www.bct.gov.tn/bct/siteprod/stat_index.jsp?la=AN", "frequency": "monthly"},
    "Administration Publique": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Ménages": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Amortissements": {"source": "World Bank", "code": "NY.GDP.MKTP.CD - NY.GNP.MKTP.KD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=TN"},
    "REVENU NATIONAL NET": {"source": "World Bank", "code": "NY.ADJ.NNAT.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.ADJ.NNAT.CD?locations=TN"},
    "REVENU NATIONAL DISPONIBLE": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Consommation Finale": {"source": "World Bank", "code": "NE.CON.TOTL.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NE.CON.TOTL.CD?locations=TN"},
    "EPARGNE NATIONALE (BRUTE)": {"source": "World Bank", "code": "NY.GNS.ICTR.CD", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.GNS.ICTR.CD?locations=TN"},
    "EPARGNE NATIONALE (NETTE)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Taux d'épargne par agent": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "TAUX D'EPARGNE": {"source": "World Bank", "code": "NY.GNS.ICTR.ZS", "frequency": "annual", "url": "https://data.worldbank.org/indicator/NY.GNS.ICTR.ZS?locations=TN"},
    "Population (en milliers)": {"source": "World Bank", "code": "SP.POP.TOTL", "frequency": "annual", "url": "https://data.worldbank.org/indicator/SP.POP.TOTL?locations=TN"},
    "Nombre de ménage (en milliers)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Taille moyenne d'un ménage": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "INDICE DES PRIX A LA CONSOMMATION FAMILIALE (IPC; 2015=100)": {"source": "INS", "url": "http://www.ins.tn/en/statistiques/72", "frequency": "monthly"},
    "REVENU DISPONIBLE BRUT DES MENAGES en MD": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Accroissement": {"source": "Derived", "method": "Calculate growth rates from other indicators"},
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars courants": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "REVENU DISPONIBLE BRUT PAR MENAGE en Dinars de 2015": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "GFCF by Institutional Sectors (MD)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Non-Financial Corporations (NFCs)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Financial Institution": {"source": "BCT", "url": "https://www.bct.gov.tn/bct/siteprod/stat_index.jsp?la=AN", "frequency": "monthly"},
    "Public Administration": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Householders (housing)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "TOTAL GENERAL": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "Inflation": {"source": "World Bank", "code": "FP.CPI.TOTL.ZG", "frequency": "annual", "url": "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=TN"},
    "RNDB (MD 2015)": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"},
    "RNDB/Personne": {"source": "INS", "url": "http://dataportal.ins.tn/en/DataAnalysis?oEf11IVGkSLU1lTd7LA", "frequency": "annual"}
}

# Check robots.txt
def is_allowed(url, user_agent="*"):
    rp = RobotFileParser()
    base_url = "/".join(url.split("/")[:3])
    rp.set_url(f"{base_url}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return True

# LangChain tools
def scrape_world_bank(indicator_code: str, country_code: str = "TN"):
    try:
        data = wbdata.get_data(indicator_code, country=country_code)
        df = pd.DataFrame(data)
        df = df[["date", "value"]].dropna()
        df["date"] = df["date"].astype(int)
        df = df[(df["date"] >= 2018) & (df["date"] <= 2025)]
        result = df.to_dict(orient="records")
        return json.dumps({"status": "success", "data": result, "message": "World Bank data fetched"})
    except Exception as e:
        return json.dumps({"status": "error", "data": [], "message": str(e)})

def scrape_ins_data(url: str, indicator_name: str):
    if not is_allowed(url):
        return json.dumps({"status": "error", "data": [], "message": "Blocked by robots.txt"})
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=re.compile(r"\.(csv|xls|xlsx)$"))
        if not links:
            return json.dumps({"status": "error", "data": [], "message": "No CSV/XLS file found"})
        file_url = links[0]["href"]
        if not file_url.startswith("http"):
            file_url = "/".join(url.split("/")[:3]) + file_url
        response = requests.get(file_url)
        df = pd.read_excel(response.content) if file_url.endswith((".xls", ".xlsx")) else pd.read_csv(response.content)
        if "Year" in df.columns:
            df = df[df["Year"].astype(int).between(2018, 2025)]
        result = df.to_dict(orient="records")
        return json.dumps({"status": "success", "data": result, "message": f"INS {indicator_name} scraped"})
    except Exception as e:
        return json.dumps({"status": "error", "data": [], "message": str(e)})

def scrape_bct_pdf(url: str, indicator_name: str):
    if not is_allowed(url):
        return json.dumps({"status": "error", "data": [], "message": "Blocked by robots.txt"})
    try:
        response = requests.get(url)
        pdf_path = os.path.join(PDFS_DIR, f"temp_{datetime.now().timestamp()}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        os.remove(pdf_path)
        prompt = f"Extract monthly data for '{indicator_name}' for 2018–2025 from:\n{text}"
        llm_result = llm.invoke(prompt)
        return json.dumps({"status": "success", "data": llm_result, "message": f"BCT {indicator_name} processed"})
    except Exception as e:
        return json.dumps({"status": "error", "data": [], "message": str(e)})

tools = [
    Tool(name="WorldBankScraper", func=scrape_world_bank, description="Fetches World Bank data. Input: indicator_code (str)."),
    Tool(name="INSScraper", func=scrape_ins_data, description="Scrapes INS data. Input: URL (str), indicator_name (str)."),
    Tool(name="BCTPDFScraper", func=scrape_bct_pdf, description="Scrapes BCT PDFs. Input: URL (str), indicator_name (str).")
]

# LangChain agent setup
llm = OllamaLLM(model="llama3.1:latest", temperature=0.7, num_ctx=4096, num_thread=4)
prompt = PromptTemplate.from_template("""
You are an economic data agent for Tunisia, extracting monthly indicators for 2018–2025. Use the provided tools.

Tools available: {tool_names}
Tool details: {tools}

Query: {query}

Instructions:
1. Select the appropriate tool based on the indicator and source.
2. Use WorldBankScraper for indicators with codes.
3. Use INSScraper for INS data, BCTPDFScraper for BCT data.
4. Ensure data is monthly where possible; otherwise, note frequency.
5. Handle units (MD, thousands, Dinars) and temporal contexts (2015 base).
6. Return JSON with status, data, and message.

Agent scratchpad: {agent_scratchpad}

Final Answer:
```json
{{
  "status": "success" or "error",
  "data": [] or [{{}}] or "string",
  "message": "string"
}}
```
""")

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3, handle_parsing_errors=True)

# Pydantic model
class ScrapeRequest(BaseModel):
    indicator_name: str
    input_data: str

# Save to JSON
def save_to_json(data, indicator_name, source):
    metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    metadata[indicator_name] = {
        'data': data,
        'timestamp': datetime.now().isoformat(),
        'source': source,
        'frequency': INDICATOR_SOURCES[indicator_name].get('frequency', 'unknown')
    }
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

# API endpoints
@app.post("/scrape")
async def scrape_data(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Processing scrape request for {request.indicator_name}")
        indicator_name = request.indicator_name
        input_data = request.input_data
        if indicator_name not in INDICATOR_SOURCES:
            return {"status": "error", "message": "Indicator not found", "data": []}
        source = INDICATOR_SOURCES[indicator_name]['source']
        if source == "World Bank":
            query = f"Fetch {indicator_name} for Tunisia using WorldBankScraper with code {INDICATOR_SOURCES[indicator_name]['code']}"
            source_name = "World Bank"
        elif source == "INS":
            query = f"Fetch {indicator_name} for Tunisia using INSScraper with URL {INDICATOR_SOURCES[indicator_name]['url']}"
            source_name = "INS Tunisia"
        elif source == "BCT":
            query = f"Fetch {indicator_name} for Tunisia using BCTPDFScraper with URL {INDICATOR_SOURCES[indicator_name]['url']}"
            source_name = "BCT"
        elif source == "Derived":
            return {"status": "error", "message": "Derived indicators not yet implemented", "data": []}
        else:
            return {"status": "error", "message": "Unknown source", "data": []}

        result = agent_executor.invoke({"query": query})
        output = json.loads(result["output"]) if result["output"] else {"status": "error", "data": [], "message": "No output"}

        if output.get("status") == "success" and output.get("data"):
            background_tasks.add_task(save_to_json, output["data"], indicator_name, source_name)
        return output
    except Exception as e:
        logger.error(f"Error in scrape_data: {e}")
        return {"status": "error", "message": f"Scraping failed: {str(e)}", "data": []}

@app.get("/data/indicators")
async def get_indicators():
    try:
        if not os.path.exists(METADATA_FILE):
            return []
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return [
            {
                "indicator_name": name,
                "data": data["data"],
                "timestamp": data["timestamp"],
                "source": data["source"],
                "frequency": data["frequency"]
            }
            for name, data in metadata.items()
        ]
    except Exception as e:
        logger.error(f"Error in get_indicators: {e}")
        return []

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Economic Data API is running", "status": "healthy"}

if __name__ == "__main__":
    try:
        logger.info("Starting the FastAPI application...")
        uvicorn.run(
            "abdelkhalek_solution:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting the server: {e}")