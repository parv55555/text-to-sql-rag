"""
LLM Factory for Multi-Provider BYOK (Bring Your Own Key) Support.
Supports Google Gemini, OpenAI, Anthropic Claude, Groq, and OpenRouter/Custom endpoints.
"""

from typing import Dict, List, Tuple, Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


PROVIDER_METADATA = {
    "Google Gemini": {
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        "default_model": "gemini-1.5-flash",
        "key_url": "https://aistudio.google.com/app/apikey",
        "description": "Fast & cost-effective, high context window (Google AI Studio)."
    },
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "key_url": "https://platform.openai.com/api-keys",
        "description": "Industry benchmark for code and reasoning accuracy."
    },
    "Anthropic": {
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "default_model": "claude-3-5-sonnet-20241022",
        "key_url": "https://console.anthropic.com/settings/keys",
        "description": "State-of-the-art coding and complex SQL logic synthesis."
    },
    "Groq": {
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "default_model": "llama-3.3-70b-versatile",
        "key_url": "https://console.groq.com/keys",
        "description": "Lightning-fast inference speeds powered by LPU hardware."
    },
    "Custom / OpenRouter": {
        "models": ["meta-llama/llama-3.3-70b-instruct", "deepseek/deepseek-chat", "mistralai/mistral-large"],
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "key_url": "https://openrouter.ai/keys",
        "description": "Connect to any OpenAI-compatible API base URL."
    }
}


class LLMFactory:
    """Instantiates and tests LangChain chat models dynamically based on user BYOK credentials."""

    @staticmethod
    def get_supported_providers() -> List[str]:
        return list(PROVIDER_METADATA.keys())

    @staticmethod
    def get_provider_details(provider: str) -> Dict[str, Any]:
        return PROVIDER_METADATA.get(provider, {})

    @staticmethod
    def create_llm(
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0
    ) -> BaseChatModel:
        """Instantiates the appropriate LangChain BaseChatModel instance."""
        if not api_key:
            raise ValueError(f"API Key for {provider} cannot be empty.")

        meta = PROVIDER_METADATA.get(provider, {})
        selected_model = model_name or meta.get("default_model")

        if provider == "Google Gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=selected_model,
                google_api_key=api_key,
                temperature=temperature
            )

        elif provider == "OpenAI":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=selected_model,
                api_key=api_key,
                temperature=temperature
            )

        elif provider == "Anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model_name=selected_model,
                api_key=api_key,
                temperature=temperature
            )

        elif provider == "Groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=selected_model,
                api_key=api_key,
                temperature=temperature
            )

        elif provider == "Custom / OpenRouter":
            from langchain_openai import ChatOpenAI
            resolved_base_url = base_url.strip() if base_url else "https://openrouter.ai/api/v1"
            return ChatOpenAI(
                model=selected_model,
                api_key=api_key,
                base_url=resolved_base_url,
                temperature=temperature
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def test_connection(
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Tests the credentials by sending a lightweight 1-token message."""
        try:
            llm = LLMFactory.create_llm(
                provider=provider,
                api_key=api_key,
                model_name=model_name,
                base_url=base_url
            )
            response = llm.invoke([HumanMessage(content="Reply with the single word 'READY'.")])
            reply_text = response.content if hasattr(response, "content") else str(response)
            return True, f"Connection successful! Model response: {reply_text.strip()}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
