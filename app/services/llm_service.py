from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

import os
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import JOBEVALUATOR_MODEL, OLLAMA_MODEL, GROQ_WAIT_SECONDS

load_dotenv()


def get_groq(llm = JOBEVALUATOR_MODEL, 
             max_tokens = 1000, 
             temperature = 0, 
             reasoning_effort = "none"):
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=llm,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort
    )


def get_ollama(temperature = 0, 
               reasoning_effort = False,
               llm = OLLAMA_MODEL,
               num_ctx=6000):
    return ChatOllama(
        model=llm,
        temperature=temperature,
        num_ctx=num_ctx,
        reasoning=reasoning_effort,
    )


def get_wait_seconds(error: Exception, attempt: int) -> float:
    response = getattr(error, "response", None)
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after) + 1
            except ValueError:
                pass
    return GROQ_WAIT_SECONDS[min(attempt, len(GROQ_WAIT_SECONDS) - 1)]