from langchain_groq import ChatGroq
from dotenv import load_dotenv

import os
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import JOBEVALUATOR_MODEL

load_dotenv()

def get_llm(model = JOBEVALUATOR_MODEL, 
            max_tokens = 2000, 
            temperature = 0, 
            reasoning_effort = "none"):
    
    # TODO: Use locally loaded quantized model
    model = ChatGroq(
        api_key=os.getenv('GROQ_API_KEY'),
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort
    )

    return model


