"""
apps/interview_generator/openai_client.py

AI client for generating interview questions.
Supports: OpenRouter (free LLMs) → OpenAI (paid) → Offline fallback (rule-based).

Designed to be reusable by future modules:
  - AI Mock Interview
  - AI Answer Evaluator
"""
import json
import logging
import os
from typing import Any, Dict

from .constants import (
    DEFAULT_INTERVIEW_MODEL,
    INTERVIEW_TIMEOUT_SECONDS,
    OPENROUTER_BASE_URL,
)
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from .utils import generate_fallback_questions

logger = logging.getLogger(__name__)


class InterviewAIClient:
    """
    AI client for interview question generation.

    Priority chain:
      1. OPENROUTER_API_KEY → free LLMs (Llama 3.1, Mistral, Gemma)
      2. OPENAI_API_KEY     → OpenAI GPT-3.5/4
      3. No key             → Rule-based offline fallback
    """

    def __init__(self, api_key: str = None, model: str = None):
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        openai_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()

        # Clear placeholder value
        if openrouter_key in ("", "sk-or-paste-your-key-here"):
            openrouter_key = ""

        if openrouter_key:
            self.api_key = openrouter_key
            self.base_url = OPENROUTER_BASE_URL
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", DEFAULT_INTERVIEW_MODEL)
            self.provider = "OpenRouter"
        elif openai_key:
            self.api_key = openai_key
            self.base_url = None
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            self.provider = "OpenAI"
        else:
            self.api_key = ""
            self.base_url = None
            self.model = DEFAULT_INTERVIEW_MODEL
            self.provider = "Fallback"

    def generate_questions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interview questions for the given context dict.

        Args:
            context: Dict from build_interview_context().

        Returns:
            Dict: {job_role, difficulty, questions: [{id, category, question}]}
        """
        if not self.api_key:
            logger.info("No API key configured. Using offline rule-based interview question engine.")
            return generate_fallback_questions(context)

        # Build the prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(**{
            k: v for k, v in context.items() if not k.startswith("_")
        })

        try:
            import openai

            logger.info(f"Calling {self.provider} ({self.model}) for interview question generation.")

            client_kwargs: Dict[str, Any] = {
                "api_key": self.api_key,
                "timeout": INTERVIEW_TIMEOUT_SECONDS,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = openai.OpenAI(**client_kwargs)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # Try with JSON mode first
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=0.6,
                )
            except Exception:
                # Some free models don't support json_object mode
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.6,
                )

            raw = response.choices[0].message.content or ""

            # Strip markdown fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)

            # Ensure required fields exist
            if "questions" not in data or not isinstance(data["questions"], list):
                raise ValueError("API response missing 'questions' list.")

            # Ensure all questions have required fields
            cleaned: list = []
            for i, q in enumerate(data["questions"], start=1):
                cleaned.append({
                    "id": i,
                    "category": q.get("category", "Technical"),
                    "question": q.get("question", q.get("text", "")),
                })

            data["questions"] = cleaned
            data.setdefault("job_role", context.get("job_role", ""))
            data.setdefault("difficulty", context.get("difficulty", ""))

            logger.info(f"Successfully generated {len(cleaned)} questions via {self.provider}.")
            return data

        except Exception as exc:
            logger.warning(f"{self.provider} API call failed: {exc}. Falling back to offline engine.")
            return generate_fallback_questions(context)
