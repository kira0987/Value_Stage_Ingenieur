from langchain_ollama import OllamaLLM
from autogen import AssistantAgent

# Initialize Ollama LLM (ensure Ollama server is running with llama3.1:8b)
llm = OllamaLLM(model="llama3.1:latest", base_url="http://localhost:11434")

# Initialize AutoGen agents
fetcher = AssistantAgent(
    name="Fetcher",
    system_message="Fetch raw data from INS API, INS websites, or CIA Factbook."
)
parser = AssistantAgent(
    name="Parser",
    llm_config=False,
    system_message="Parse raw data to extract indicators using LangChain."
)
validator = AssistantAgent(
    name="Validator",
    llm_config=False,
    system_message="Validate data for 2018–2025 and ensure correct units (e.g., MD, thousands, percent)."
) 