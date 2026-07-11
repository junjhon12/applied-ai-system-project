"""AI-generated hints with a validation guardrail and fallback.

Uses the OpenAI API to generate a natural-language hint after each guess.
Every AI response is checked for consistency with the actual game outcome
before it is shown to the player; if the call fails or the response fails
validation, the game falls back to the deterministic hint in logic_utils.
"""
import logging
import re

from logic_utils import get_hint_message

logging.basicConfig(
    filename="ai_reliability.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("ai_hints")

MAX_HINT_LENGTH = 200

_TOO_HIGH_CONTRADICTIONS = ["higher", "increase", "bigger", "go up", "larger"]
_TOO_LOW_CONTRADICTIONS = ["lower", "decrease", "smaller", "go down"]


def _build_prompt(outcome, guess, low, high, history):
    return (
        f"You are a hint generator for a number-guessing game. "
        f"The valid range is {low} to {high}. The player just guessed {guess} "
        f"and the outcome was '{outcome}'. Guess history so far: {history}. "
        f"Write ONE short, encouraging sentence telling the player which direction "
        f"to guess next. Never state or imply the secret number itself."
    )


def generate_ai_hint(outcome, guess, low, high, history, client=None):
    """Call the OpenAI API for a hint. Returns the hint text, or None on failure."""
    prompt = _build_prompt(outcome, guess, low, high, history)
    try:
        if client is None:
            import openai
            client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            timeout=10,
        )
        hint_text = response.choices[0].message.content.strip()
        logger.info("AI call ok | prompt=%s | response=%s", prompt[:200], hint_text[:200])
        return hint_text
    except Exception as exc:
        logger.warning("AI call failed | prompt=%s | error=%s", prompt[:200], exc)
        return None


def validate_ai_hint(hint_text, outcome):
    """Guardrail: reject empty, overlong, secret-leaking, or contradictory hints."""
    if not hint_text:
        return False
    if len(hint_text) > MAX_HINT_LENGTH:
        return False
    if re.search(r"\d", hint_text):
        return False

    lowered = hint_text.lower()
    if outcome == "Too High" and any(phrase in lowered for phrase in _TOO_HIGH_CONTRADICTIONS):
        return False
    if outcome == "Too Low" and any(phrase in lowered for phrase in _TOO_LOW_CONTRADICTIONS):
        return False

    return True


def score_hint_confidence(hint_text, outcome):
    """Heuristic confidence (0.0-1.0) that a hint is safe and correct.

    Graded version of the same signals validate_ai_hint checks as a hard
    gate, so a passing hint can still be flagged as low-confidence.
    """
    if not hint_text:
        return 0.0

    confidence = 1.0

    if re.search(r"\d", hint_text):
        confidence -= 0.6

    lowered = hint_text.lower()
    if outcome == "Too High" and any(phrase in lowered for phrase in _TOO_HIGH_CONTRADICTIONS):
        confidence -= 0.6
    if outcome == "Too Low" and any(phrase in lowered for phrase in _TOO_LOW_CONTRADICTIONS):
        confidence -= 0.6

    if len(hint_text) < 10 or len(hint_text) > MAX_HINT_LENGTH:
        confidence -= 0.3

    if outcome in ("Too High", "Too Low") and not any(
        phrase in lowered
        for phrase in _TOO_HIGH_CONTRADICTIONS + _TOO_LOW_CONTRADICTIONS + ["higher", "lower"]
    ):
        confidence -= 0.1

    return max(0.0, min(1.0, confidence))


def get_hint_with_fallback(outcome, guess, low, high, history, client=None):
    """Return (hint_text, source, confidence) where source is 'ai' or 'fallback'."""
    ai_hint = generate_ai_hint(outcome, guess, low, high, history, client=client)

    if validate_ai_hint(ai_hint, outcome):
        confidence = score_hint_confidence(ai_hint, outcome)
        logger.info("Guardrail passed | outcome=%s | confidence=%.2f", outcome, confidence)
        return ai_hint, "ai", confidence

    logger.info("Guardrail failed or AI unavailable, using fallback | outcome=%s | confidence=1.00", outcome)
    return get_hint_message(outcome), "fallback", 1.0
