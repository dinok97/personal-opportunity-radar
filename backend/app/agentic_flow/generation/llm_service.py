import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

AGENT_LLM="openai/gpt-oss-20b"
AGENT_REASONING="low"


def get_groq(temp, max_tokens):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=AGENT_LLM,
        temperature=temp,
        max_tokens=max_tokens,
        reasoning_effort=AGENT_REASONING
    )