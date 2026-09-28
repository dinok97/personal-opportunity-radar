import httpx

from .config import Settings
from .models import ChatMessage
from .profile_prompts import PROFILE_EXTRACTION_SYSTEM_PROMPT


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, messages: list[ChatMessage], job_context: str) -> str:
        provider_messages = [
            {
                "role": "system",
                "content": (
                    "You are the Personal Opportunity Radar career assistant. "
                    "Give concise, practical, honest career guidance. Use the supplied "
                    "user profile and opportunity context when answering. Do not invent "
                    "facts about the user or jobs. Explain why a role may fit the profile.\n\n"
                    f"Context:\n{job_context}"
                ),
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

    async def extract_profile(self, cv_text: str) -> str:
        endpoint = f"{self.settings.ollama_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": PROFILE_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"CV text:\n<cv>\n{cv_text}\n</cv>"},
            ],
            "temperature": 0,
            "stream": False,
            "response_format": {"type": "json_object"},
        }
        print(payload)

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama profile extraction failed") from exc

        if response.is_error:
            raise OllamaError(f"Ollama returned HTTP {response.status_code}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OllamaError("Ollama returned an invalid profile response") from exc

        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama returned an empty profile response")

        return content.strip()