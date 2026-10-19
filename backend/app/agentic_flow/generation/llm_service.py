import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


AGENT_LLM="qwen/qwen3.8-27b"
AGENT_REASONING="none"


def get_groq(temp, max_tokens, model=AGENT_LLM, reasoning_effort=AGENT_REASONING):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=model,
        temperature=temp,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort
    )


