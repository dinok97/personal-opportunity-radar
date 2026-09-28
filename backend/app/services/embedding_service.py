from functools import lru_cache
from typing import Protocol


class EmbeddingClient(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


@lru_cache(maxsize=2)
def _load_embedding_model(model_name: str, model_revision: str):
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "revision": model_revision,
            "trust_remote_code": True,
            "model_kwargs": {"default_task": "retrieval"},
        },
        encode_kwargs={
            "task": "retrieval",
            "prompt_name": "document",
            "convert_to_numpy": True,
        },
        query_encode_kwargs={"normalize_embeddings": True, "prompt_name": "query"}
    )


class HuggingFaceEmbeddingClient:
    def __init__(self, model_name: str, model_revision: str) -> None:
        self.model = _load_embedding_model(model_name, model_revision)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)