import httpx

from .config import Settings
from .models import ChatMessage
from .profile_prompts import PROFILE_EXTRACTION_SYSTEM_PROMPT


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, messages: list[ChatMessage], job_context: str) -> str:
        if not self.settings.openrouter_api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured")

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

        endpoint = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_site_url,
            "X-Title": self.settings.openrouter_app_name,
        }
        payload = {
            "model": self.settings.openrouter_model,
            "messages": provider_messages,
            "temperature": 0.4,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise OpenRouterError("OpenRouter request failed") from exc

        if response.is_error:
            raise OpenRouterError(f"OpenRouter returned HTTP {response.status_code}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OpenRouterError("OpenRouter returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise OpenRouterError("OpenRouter returned an empty response")

        return content.strip()

    async def extract_profile(self, cv_text: str) -> str:
        if not self.settings.openrouter_api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured")

        endpoint = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_site_url,
            "X-Title": self.settings.openrouter_app_name,
        }
        payload = {
            "model": self.settings.openrouter_model,
            "messages": [
                {"role": "system", "content": PROFILE_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"CV text:\n<cv>\n{cv_text}\n</cv>"},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise OpenRouterError("OpenRouter profile extraction failed") from exc

        if response.is_error:
            raise OpenRouterError(f"OpenRouter returned HTTP {response.status_code}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OpenRouterError("OpenRouter returned an invalid profile response") from exc

        if not isinstance(content, str) or not content.strip():
            raise OpenRouterError("OpenRouter returned an empty profile response")

        return content.strip()
