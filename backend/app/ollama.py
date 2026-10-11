import httpx

from .config import Settings
from .models import ChatMessage


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, settings: Settings, *, system_prompt: str | None = None) -> None:
        self.settings = settings
        self.system_prompt = system_prompt

    async def complete(self, messages: list[ChatMessage], job_context: str) -> str:
        system_content = self.system_prompt or (
            "You are the Personal Opportunity Radar career assistant. "
            "Give concise, practical, honest career guidance. Use the supplied "
            "opportunity context when answering, and do not invent job facts. "
            "Explain why a role may fit the user's profile.\n\n"
            "User skills: Python, Machine Learning, NLP, SQL, LLMs, Research.\n"
            f"Opportunity context:\n{job_context}"
        )
        provider_messages = [
            {
                "role": "system",
                "content": system_content,
            },
            *[message.model_dump() for message in messages],
        ]
        endpoint = f"{self.settings.ollama_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.ollama_model,
            "messages": provider_messages,
            "temperature": 0.4,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama request failed") from exc

        if response.is_error:
            raise OllamaError(f"Ollama returned HTTP {response.status_code}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OllamaError("Ollama returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama returned an empty response")

        return content.strip()