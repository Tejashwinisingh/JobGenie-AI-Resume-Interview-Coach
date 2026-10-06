"""
apps/mock_interview/openai_client.py

AI client service for generating mock interview questions sequentially.
Supports OpenRouter (free LLMs) → OpenAI → Rule-based fallback.
"""
import json
import logging
import os
from typing import Any, Dict, Tuple

from .constants import (
    DEFAULT_MOCK_MODEL,
    MOCK_TIMEOUT_SECONDS,
    OPENROUTER_BASE_URL,
)
from .prompts import QUESTION_GENERATION_PROMPT, SYSTEM_PROMPT
from .utils import generate_fallback_question

logger = logging.getLogger(__name__)


class MockInterviewAIClient:
    """
    AI client for interactive mock interview question generation.

    Priority chain:
      1. OPENROUTER_API_KEY → free LLMs (Llama 3.1, Mistral, Gemma)
      2. OPENAI_API_KEY     → OpenAI GPT-3.5/4
      3. No key             → Rule-based offline fallback
    """

    def __init__(self, api_key: str = None, model: str = None):
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        openai_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()

        if openrouter_key in ("", "sk-or-paste-your-key-here"):
            openrouter_key = ""

        if openrouter_key:
            self.api_key = openrouter_key
            self.base_url = OPENROUTER_BASE_URL
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", DEFAULT_MOCK_MODEL)
            self.provider = "OpenRouter"
        elif openai_key:
            self.api_key = openai_key
            self.base_url = None
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            self.provider = "OpenAI"
        else:
            self.api_key = ""
            self.base_url = None
            self.model = DEFAULT_MOCK_MODEL
            self.provider = "Fallback"

    def generate_next_question(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate the next single interview question for a session.

        Args:
            context: Dict from build_session_context().

        Returns:
            Tuple[category, question_text]
        """
        if not self.api_key:
            logger.info("No API key set. Using rule-based offline fallback question generator.")
            return generate_fallback_question(context)

        user_prompt = QUESTION_GENERATION_PROMPT.format(**{
            k: v for k, v in context.items() if not k.startswith("_")
        })

        try:
            import openai

            logger.info(f"Calling {self.provider} ({self.model}) for Q#{context.get('question_number')}.")

            client_kwargs: Dict[str, Any] = {
                "api_key": self.api_key,
                "timeout": MOCK_TIMEOUT_SECONDS,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = openai.OpenAI(**client_kwargs)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # Try JSON mode
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=0.6,
                )
            except Exception:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.6,
                )

            raw = response.choices[0].message.content or ""

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)
            category = data.get("category", "Technical")
            question_text = data.get("question", "").strip()

            if not question_text:
                raise ValueError("AI response returned empty question text.")

            logger.info(f"Generated Q#{context.get('question_number')} [{category}] via {self.provider}.")
            return category, question_text

        except Exception as exc:
            logger.warning(f"{self.provider} API call failed: {exc}. Using fallback question generator.")
            return generate_fallback_question(context)
