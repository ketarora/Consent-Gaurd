"""
LLM classifier for Consent Guard.

Supports multiple LLM providers (Gemini, OpenAI, Anthropic) to classify
messages against four CCPA dark-pattern categories: confirm_shaming,
forced_continuity, drip_pricing, basket_sneaking. Also serves as a
fallback for ambiguous false-urgency cases that the regex pre-filter
can't confidently resolve.

Provider priority: GEMINI_API_KEY → OPENAI_API_KEY → ANTHROPIC_API_KEY.
Set whichever key you have in your .env file.

FAIL-SAFE INVARIANT: If the classifier errors out, times out, or returns
malformed output after one retry, the message is HELD with a classifier_error
flag — never silently passed as clean. A compliance tool that fails open is
worse than no tool at all.
"""

from __future__ import annotations

import json
import os
import logging
from typing import Optional

from models import DarkPatternCategory, Flag

logger = logging.getLogger(__name__)

# Categories the LLM classifier handles.
_LLM_CATEGORIES = {
    DarkPatternCategory.CONFIRM_SHAMING,
    DarkPatternCategory.FORCED_CONTINUITY,
    DarkPatternCategory.DRIP_PRICING,
    DarkPatternCategory.BASKET_SNEAKING,
    DarkPatternCategory.FALSE_URGENCY,  # fallback for ambiguous urgency
}

_SYSTEM_PROMPT = """You are a compliance classifier for India's Consumer Protection Act (CCPA) dark-pattern taxonomy.

Your job: analyze the given agent-to-customer message and determine if it contains any of these dark-pattern categories:

1. **confirm_shaming**: The decline/reject option is worded to guilt, shame, or belittle the user for choosing it. Example: "No thanks, I don't want to save money." A neutral decline (e.g., "No thanks, continue with Basic") is NOT confirm_shaming.

2. **forced_continuity**: Cancellation is deliberately made harder, slower, or more obscure than sign-up. Example: "Call our support line during business hours to cancel." Easy self-service cancellation (e.g., "Cancel anytime from Settings") is NOT forced_continuity.

3. **drip_pricing**: Mandatory fees (taxes, service charges, platform fees) are withheld from the headline price and revealed only at checkout or payment. Example: "₹999 — plus a ₹79 convenience fee shown only at final payment." An all-inclusive upfront price is NOT drip_pricing.

4. **basket_sneaking**: Paid items or services are pre-added to the user's cart or order without explicit opt-in. Example: "We've included Express Delivery (₹149) by default." An optional add-on requiring explicit user action is NOT basket_sneaking.

5. **false_urgency**: A deadline, scarcity claim, or time pressure is manufactured with no real system-recorded basis. Example: "Last chance — this price won't be shown again." A genuine renewal notice tied to a real date/mandate is NOT false_urgency.

Respond with a JSON object exactly matching this structure (no markdown fences):
{
  "flagged": true/false,
  "category": "category_name" or null,
  "confidence": 0.0-1.0 or null,
  "quoted_span": "exact substring from the message" or null,
  "reasoning": "brief explanation",
  "suggested_rewrite": "a recommended compliant rewrite of the message (or null if not flagged)"
}

Rules:
- If the message is clean (no dark pattern), set flagged=false and all other fields to null.
- If flagged, quoted_span MUST be an exact substring of the original message — do not paraphrase or summarize.
- confidence should reflect how clear-cut the violation is (0.9+ for obvious, 0.6-0.8 for borderline).
- Only flag ONE category per message (the most prominent).
- Be precise: a message that LOOKS like a pattern but has a neutral/factual alternative is NOT a violation.
- If flagged, always provide a neutral, factual `suggested_rewrite` that removes the manipulation but achieves the core sales goal."""

def _detect_provider() -> tuple[str, str, str]:
    """
    Detect which LLM provider to use based on available API keys.
    Returns (provider_name, api_key, model).
    Priority: Gemini → OpenAI → Anthropic.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if gemini_key:
        model = os.environ.get("CLASSIFIER_MODEL", "gemini-2.0-flash")
        return ("gemini", gemini_key, model)
    elif openai_key:
        model = os.environ.get("CLASSIFIER_MODEL", "gpt-4o-mini")
        return ("openai", openai_key, model)
    elif anthropic_key:
        model = os.environ.get("CLASSIFIER_MODEL", "claude-haiku-4-5-20251001")
        return ("anthropic", anthropic_key, model)
    else:
        return ("none", "", "")


async def classify_message(text: str) -> Optional[Flag]:
    """
    Classify a message using the configured LLM provider.

    Sends the message to the LLM API and parses the structured
    JSON response. If the response is malformed (missing quoted_span,
    invalid JSON, etc.), retries once. If it still fails, returns a
    classifier_error flag — NEVER None/clean.
    """
    provider, api_key, model = _detect_provider()

    if not api_key:
        logger.warning("No LLM API key set (GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY) — failing safe to held.")
        return _make_classifier_error_flag(text, "No API key configured")

    logger.info(f"Using {provider} provider with model {model}")

    # Two attempts: original + one retry.
    for attempt in range(2):
        try:
            if provider == "gemini":
                result = await _call_gemini(api_key, model, text)
            elif provider == "openai":
                result = await _call_openai(api_key, model, text)
            else:
                result = await _call_anthropic(api_key, model, text)

            if result is None:
                return None
            return result
        except Exception as e:
            logger.warning(f"Classifier attempt {attempt + 1} failed ({provider}): {e}")
            if attempt == 0:
                continue  # Retry once.
            logger.error(f"Classifier failed after retry. Failing safe to held. Error: {e}")
            return _make_classifier_error_flag(text, str(e))
            
    return _make_classifier_error_flag(text, "Unexpected classifier flow")


async def _call_gemini(api_key: str, model: str, text: str) -> Optional[Flag]:
    """Call Google Gemini API via raw httpx."""
    import httpx
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "system_instruction": {
            "parts": {"text": _SYSTEM_PROMPT}
        },
        "contents": [
            {"parts": [{"text": f'Message to classify:\n"{text}"'}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        max_retries = 3
        for attempt in range(max_retries):
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in (503, 429):
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(10.0 * (attempt + 1))
                    continue
            response.raise_for_status()
            break
            
    data = response.json()
    try:
        candidate = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ValueError(f"Unexpected response structure from Gemini: {data}")
        
    return _parse_llm_response(candidate, text)


async def _call_openai(api_key: str, model: str, text: str) -> Optional[Flag]:
    """Call OpenAI API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f'Message to classify:\n"{text}"'},
        ],
    )

    candidate = response.choices[0].message.content
    return _parse_llm_response(candidate, text)


async def _call_anthropic(api_key: str, model: str, text: str) -> Optional[Flag]:
    """Call Anthropic Claude API."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    
    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {
                "role": "user", 
                "content": f"{_SYSTEM_PROMPT}\n\nMessage to classify:\n\"{text}\""
            }
        ]
    )
    
    candidate = response.content[0].text
    return _parse_llm_response(candidate, text)


def _parse_llm_response(candidate: str, original_text: str) -> Optional[Flag]:
    """Parse the structured JSON response from any LLM provider."""
    # Strip markdown fences if the LLM wrapped its response
    cleaned = candidate.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (the fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM output: {e}\nRaw output: {candidate}")

    if not parsed.get("flagged", False):
        return None

    category_str = parsed.get("category")
    confidence = parsed.get("confidence")
    quoted_span = parsed.get("quoted_span")
    suggested_rewrite = parsed.get("suggested_rewrite")

    if not category_str or confidence is None or not quoted_span:
        raise ValueError("Flagged response missing required fields")

    # Normalize category to fit Enum since LLMs can hallucinate capitalization and spaces
    category_str = str(category_str).strip().lower().replace(" ", "_").replace("-", "_")
    try:
        category = DarkPatternCategory(category_str)
    except ValueError:
        raise ValueError(f"Unknown category from classifier: {category_str}")

    # Validate quoted_span actually appears in the original message.
    if quoted_span.lower() not in original_text.lower():
        quoted_span = original_text[:80] + ("..." if len(original_text) > 80 else "")

    return Flag(
        category=category,
        confidence=float(confidence),
        quoted_span=quoted_span,
        cleared_by_allowlist=False,
        suggested_rewrite=suggested_rewrite
    )

def _make_classifier_error_flag(text: str, error_reason: str) -> Flag:
    span = text[:80] + ("..." if len(text) > 80 else "")
    return Flag(
        category=DarkPatternCategory.CLASSIFIER_ERROR,
        confidence=1.0,
        quoted_span=span,
        cleared_by_allowlist=False,
        suggested_rewrite="[Compliance System Offline] Agent message held. Please provide a manual rewrite."
    )
