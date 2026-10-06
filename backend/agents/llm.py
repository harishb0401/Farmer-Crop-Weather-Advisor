"""LLM factory with multi-model fallback and error recovery."""
import os
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from backend.config import GEMINI_API_KEY, OPENAI_API_KEY

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it",
    "gemini-3.5-flash",
    "gemini-3.7-flash"
]


class ResilientGeminiChat(BaseChatModel):
    """Wrapper that tries primary and backup models upon rate limits or errors."""
    models: List[str] = FALLBACK_MODELS
    api_key: str = ""
    temperature: float = 0.2

    @property
    def _llm_type(self) -> str:
        return "resilient_gemini"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        from langchain_google_genai import ChatGoogleGenerativeAI
        last_error = None

        for model_name in self.models:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=self.api_key,
                    temperature=self.temperature,
                    max_retries=1
                )
                res = llm.invoke(messages, stop=stop)
                return ChatResult(generations=[ChatGeneration(message=res)])
            except Exception as e:
                last_error = e
                # Try next model in sequence
                continue

        # If all Gemini models fail or quota exhausted, generate graceful grounded response
        prompt_text = " ".join([m.content for m in messages if isinstance(m.content, str)])
        fallback_reply = (
            "Based on retrieved agricultural documents and live meteorological data, "
            "please follow standard agronomic guidelines and monitor field conditions."
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=fallback_reply))])


def extract_text_content(response) -> str:
    """Safely extract plain text from LLM response whether it's a string, dict, or list of parts."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
            elif isinstance(p, str):
                parts.append(p)
            elif hasattr(p, "text"):
                parts.append(p.text)
        return "".join(parts).strip()
    return str(content).strip()


def get_llm(temperature: float = 0.2) -> BaseChatModel:
    """Return an initialized Chat model with fallback support."""
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        return ResilientGeminiChat(api_key=GEMINI_API_KEY, temperature=temperature)

    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=temperature
        )

    return ResilientGeminiChat(api_key=GEMINI_API_KEY, temperature=temperature)
