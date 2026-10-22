import os 
from dotenv import load_dotenv

from langchain_groq import ChatGroq

load_dotenv()

AGENT_LLM="openai/gpt-oss-120b"
AGENT_REASONING="low"

def get_groq(temp, model=AGENT_LLM, reasoning_effort=AGENT_REASONING):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=model,
        temperature=temp,
        reasoning_effort=reasoning_effort
    )