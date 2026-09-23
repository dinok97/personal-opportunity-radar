import sys
from dotenv import load_dotenv
from pathlib import Path
import os

from langchain_huggingface import HuggingFaceEmbeddings

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helpers.constants import EMBEDDING_MODEL, EMBEDDING_MODEL_REVISION

load_dotenv()

hf_token = os.getenv("HF_TOKEN")
if hf_token is None:
    raise ValueError("HF_TOKEN not found - check your .env file or environment")

class EmbeddingService():
    def __init__(self) -> None:
        self.model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={
                "revision": EMBEDDING_MODEL_REVISION, 
                "trust_remote_code": True, 
                "model_kwargs": {"default_task": "retrieval"}
            },
            encode_kwargs={"normalize_embeddings": True, "prompt_name": "document"},
            query_encode_kwargs={"normalize_embeddings": True, "prompt_name": "query"}
        )
