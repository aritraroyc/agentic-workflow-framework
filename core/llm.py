"""
LLM Client wrapper for unified interface across different LLM providers.

Supports:
- OpenAI (via langchain ChatOpenAI)
- Anthropic Claude (via langchain ChatAnthropic)

Provides:
- Unified async/sync invoke interface
- Consistent response handling
- Error handling and retries
- Message formatting for different providers
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: int = 2048):
        """
        Initialize LLM client.

        Args:
            model_name: Name of the model
            temperature: Temperature for sampling (0-1)
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client: Optional[Any] = None

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize and return the LLM client."""
        pass

    @abstractmethod
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        Invoke the LLM with messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Response content string
        """
        pass

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """
        Convert message dicts to LangChain BaseMessage objects.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            List of BaseMessage objects
        """
        formatted: List[BaseMessage] = []

        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")

            if role == "system":
                formatted.append(SystemMessage(content=content))
            elif role == "user":
                formatted.append(HumanMessage(content=content))
            else:
                # Default to user message for unknown roles
                formatted.append(HumanMessage(content=content))

        return formatted

    def _extract_response(self, response: Any) -> str:
        """
        Extract string content from LLM response.

        Args:
            response: Response from LLM

        Returns:
            String content
        """
        if hasattr(response, "content"):
            return response.content
        return str(response)


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client using LangChain ChatOpenAI."""

    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
    ):
        """
        Initialize OpenAI client.

        Args:
            model_name: OpenAI model name (default: gpt-4-turbo-preview)
            temperature: Temperature for sampling
            max_tokens: Maximum response tokens
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        super().__init__(model_name, temperature, max_tokens)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set, OpenAI client may not work")

        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[ChatOpenAI]:
        """Initialize ChatOpenAI client."""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not provided, client will use heuristic fallbacks")
            return None

        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
        )

    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        Invoke OpenAI API with messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Response content string
        """
        try:
            formatted_messages = self._format_messages(messages)

            # Use asyncio.to_thread for blocking operation
            response = await asyncio.to_thread(
                self.client.invoke,
                formatted_messages
            )

            return self._extract_response(response)

        except Exception as e:
            logger.error(f"OpenAI invocation failed: {str(e)}", exc_info=True)
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude LLM client using LangChain ChatAnthropic."""

    def __init__(
        self,
        model_name: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Anthropic client.

        Args:
            model_name: Claude model name (default: claude-3-sonnet-20240229)
            temperature: Temperature for sampling
            max_tokens: Maximum response tokens
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        super().__init__(model_name, temperature, max_tokens)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set, Anthropic client may not work")

        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[ChatAnthropic]:
        """Initialize ChatAnthropic client."""
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not provided, client will use heuristic fallbacks")
            return None

        return ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
        )

    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        Invoke Anthropic API with messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Response content string
        """
        try:
            formatted_messages = self._format_messages(messages)

            # Use asyncio.to_thread for blocking operation
            response = await asyncio.to_thread(
                self.client.invoke,
                formatted_messages
            )

            return self._extract_response(response)

        except Exception as e:
            logger.error(f"Anthropic invocation failed: {str(e)}", exc_info=True)
            raise


def get_llm_client(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> BaseLLMClient:
    """
    Factory function to get the appropriate LLM client.

    Args:
        provider: LLM provider ('openai' or 'anthropic').
                 If None, uses LLM_PROVIDER env var or defaults to 'openai'
        model_name: Model name. If None, uses provider-specific env var or provider's default.
        temperature: Temperature for sampling
        max_tokens: Maximum response tokens

    Returns:
        Initialized LLM client instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        model = model_name or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        logger.info(f"Creating OpenAI client with model {model}")
        return OpenAIClient(
            model_name=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "anthropic":
        model = model_name or os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        logger.info(f"Creating Anthropic client with model {model}")
        return AnthropicClient(
            model_name=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Convenience function for getting default client
def get_default_llm_client() -> BaseLLMClient:
    """
    Get the default LLM client based on environment configuration.

    Returns:
        Initialized LLM client instance
    """
    return get_llm_client()
