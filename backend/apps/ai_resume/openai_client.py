"""
apps/ai_resume/openai_client.py

AI Resume Suggestions client — supports both OpenRouter (free models) and OpenAI.

Priority:
  1. OPENROUTER_API_KEY → calls OpenRouter (free Llama, Mistral, Gemma models)
  2. OPENAI_API_KEY     → calls OpenAI directly (gpt-3.5-turbo / gpt-4o)
  3. No key found       → uses built-in rule-based fallback engine (no API needed)
"""
import json
import os
import logging
from typing import Dict, Any

from .constants import DEFAULT_OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from .utils import generate_fallback_ai_suggestions

logger = logging.getLogger(__name__)

# OpenRouter base URL (OpenAI-compatible)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"


class OpenAIResumeClient:
    """
    AI client wrapper supporting OpenRouter (free) and OpenAI, with offline fallback.
    """

    def __init__(self, api_key: str = None, model: str = None):
        # Check OpenRouter first (free models), then fallback to OpenAI key
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.openai_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()

        # Remove placeholder value
        if self.openrouter_key in ("", "sk-or-paste-your-key-here"):
            self.openrouter_key = ""

        # Determine which provider to use
        if self.openrouter_key:
            self.api_key = self.openrouter_key
            self.base_url = OPENROUTER_BASE_URL
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", DEFAULT_OPENROUTER_MODEL)
            self.provider = "OpenRouter"
        elif self.openai_key:
            self.api_key = self.openai_key
            self.base_url = None  # uses default OpenAI URL
            self.model = model or os.environ.get("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)
            self.provider = "OpenAI"
        else:
            self.api_key = ""
            self.base_url = None
            self.model = DEFAULT_OPENAI_MODEL
            self.provider = "Fallback"

    def generate_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI suggestions for a candidate resume context.

        Returns:
            Dict with: summary, strengths, weaknesses, suggestions,
            priority_skills, improved_project_description.
        """
        # No API key found — use built-in offline rule engine
        if not self.api_key:
            logger.info("No API key configured. Using offline rule-based fallback AI engine.")
            return generate_fallback_ai_suggestions(context)

        # Build the user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            name=context.get("name", "Candidate"),
            skills=", ".join(context.get("skills", [])) or "None detected",
            education=json.dumps(context.get("education", [])),
            experience=json.dumps(context.get("experience", [])),
            projects=json.dumps(context.get("projects", [])),
            certifications=json.dumps(context.get("certifications", [])),
            ats_score=context.get("ats_score", 0),
            ats_grade=context.get("ats_grade", "N/A"),
            missing_sections=", ".join(context.get("missing_sections", [])) or "None",
            ats_warnings="; ".join(context.get("ats_warnings", [])) or "None",
            matched_skills=", ".join(context.get("matched_skills", [])) or "N/A",
            missing_skills=", ".join(context.get("missing_skills", [])) or "N/A",
        )

        try:
            import openai

            logger.info(f"Calling {self.provider} — Model: {self.model}")

            # Build client — OpenRouter uses base_url override
            client_kwargs = {"api_key": self.api_key, "timeout": OPENAI_TIMEOUT_SECONDS}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = openai.OpenAI(**client_kwargs)

            # Some free OpenRouter models don't support json_object mode
            # So we request JSON via the prompt and parse manually
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # Try with json_object mode first (works for most models)
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages,
                    temperature=0.4,
                )
            except Exception:
                # Fallback: call without response_format (some free models don't support it)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.4,
                )

            raw_content = response.choices[0].message.content

            # Extract JSON from response (handles markdown code fences too)
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()

            data = json.loads(raw_content)

            # Ensure all required fields exist
            required_fields = [
                "summary", "strengths", "weaknesses",
                "suggestions", "priority_skills", "improved_project_description"
            ]
            for field in required_fields:
                if field not in data:
                    data[field] = [] if field in ["strengths", "weaknesses", "suggestions", "priority_skills"] else ""

            logger.info(f"{self.provider} AI suggestions generated successfully.")
            return data

        except Exception as exc:
            logger.warning(f"{self.provider} API call failed: {exc}. Using offline fallback engine.")
            return generate_fallback_ai_suggestions(context)
