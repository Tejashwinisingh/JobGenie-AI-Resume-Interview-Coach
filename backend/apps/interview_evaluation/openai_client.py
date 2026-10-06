"""
apps/interview_evaluation/openai_client.py

AI client for evaluating completed mock interview sessions.
Supports OpenRouter (free LLMs) → OpenAI → Rule-based fallback.
"""
import json
import logging
import os
from typing import Any, Dict

from .constants import (
    DEFAULT_EVALUATION_MODEL,
    EVALUATION_TIMEOUT_SECONDS,
    OPENROUTER_BASE_URL,
)
from .prompts import EVALUATION_USER_PROMPT, SYSTEM_PROMPT
from .utils import generate_fallback_evaluation

logger = logging.getLogger(__name__)


class InterviewEvaluationAIClient:
    """
    AI client service for evaluating interview sessions.
    """

    def __init__(self, api_key: str = None, model: str = None):
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        openai_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()

        if openrouter_key in ("", "sk-or-paste-your-key-here"):
            openrouter_key = ""

        if openrouter_key:
            self.api_key = openrouter_key
            self.base_url = OPENROUTER_BASE_URL
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", DEFAULT_EVALUATION_MODEL)
            self.provider = "OpenRouter"
        elif openai_key:
            self.api_key = openai_key
            self.base_url = None
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            self.provider = "OpenAI"
        else:
            self.api_key = ""
            self.base_url = None
            self.model = DEFAULT_EVALUATION_MODEL
            self.provider = "Fallback"

    def evaluate_interview_session(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a complete interview session Q&A transcript.

        Args:
            context: Dict from build_evaluation_context().

        Returns:
            Dict formatted with overall scores, hiring recommendation, and question_analysis.
        """
        if not self.api_key:
            logger.info("No API key set. Using rule-based offline fallback interview evaluator.")
            return generate_fallback_evaluation(context)

        user_prompt = EVALUATION_USER_PROMPT.format(**{
            k: v for k, v in context.items() if not k.startswith("_")
        })

        try:
            import openai

            logger.info(f"Calling {self.provider} ({self.model}) for session evaluation.")

            client_kwargs: Dict[str, Any] = {
                "api_key": self.api_key,
                "timeout": EVALUATION_TIMEOUT_SECONDS,
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
                    temperature=0.3,
                )
            except Exception:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                )

            raw = response.choices[0].message.content or ""

            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)

            # Basic structure validations
            if "overall_score" not in data or "question_analysis" not in data:
                raise ValueError("AI evaluation output missing required fields.")

            logger.info(f"Successfully generated interview evaluation via {self.provider}.")
            return data

        except Exception as exc:
            logger.warning(f"{self.provider} API call failed: {exc}. Using fallback evaluation engine.")
            return generate_fallback_evaluation(context)
