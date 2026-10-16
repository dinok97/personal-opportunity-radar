from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from typing import TypeVar, Type
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

import os
import sys 
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from helpers.constants import (
    QWEN_MODEL, 
    QWEN_SKIP_REASONING,
    OLLAMA_MODEL, 
    GROQ_WAIT_SECONDS, 
    MAX_WAIT_SECONDS, 
    MAX_NUM_RETRIES
)

load_dotenv()


T = TypeVar("T", bound=BaseModel)


def get_groq(llm, 
             max_tokens, 
             reasoning_effort: str,
             temperature = 0):
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


def get_generated_result(model: Type[T], 
                         messages: list[BaseMessage],
                         max_tokens: int,
                         llm: str = QWEN_MODEL,
                         reasoning_effort: str = QWEN_SKIP_REASONING, 
                         retries: int = MAX_NUM_RETRIES) -> Type[T] | None:    
    
    llm_client = get_groq(llm=llm, max_tokens=max_tokens, reasoning_effort=reasoning_effort)
    structured_llm = llm_client.with_structured_output(model)

    for attempt in range(retries + 1):
        try:
            output: Type[T] = structured_llm.invoke(messages)
            if output is not None:
                return output

            print(f"Groq attempt {attempt + 1}: empty response")
            wait = GROQ_WAIT_SECONDS[min(attempt, len(GROQ_WAIT_SECONDS) - 1)]
        except Exception as e:
            print(f"Groq attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            wait = get_wait_seconds(e, attempt)

        if wait > MAX_WAIT_SECONDS:
            print(f"Groq needs {wait:.0f}s (likely the daily limit), switching to Ollama")
            break

        if attempt < retries:
            print(f"Retrying in {wait:.0f}s...")
            time.sleep(wait)

    
    print("Groq failed, falling back to Ollama (slower)...")
    try:
        ollama_llm = get_ollama().with_structured_output(model)
        return ollama_llm.invoke(messages)
    except Exception as e:
        print(f"Ollama failed too: {type(e).__name__}: {e}")
        return None
