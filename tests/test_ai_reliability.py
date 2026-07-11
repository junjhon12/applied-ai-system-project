from unittest.mock import MagicMock

from ai_hints import validate_ai_hint, get_hint_with_fallback, score_hint_confidence
from logic_utils import get_hint_message


def _mock_client_returning(text):
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=text))]
    client.chat.completions.create.return_value = response
    return client


def _mock_client_raising():
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("API down")
    return client


# ---------------------------------------------------------------------------
# validate_ai_hint (guardrail)
# ---------------------------------------------------------------------------

def test_validate_hint_rejects_contradictory_direction():
    assert validate_ai_hint("Try going a bit lower next time!", "Too Low") is False


def test_validate_hint_rejects_leaked_number():
    assert validate_ai_hint("The secret is close to 42, keep trying!", "Too High") is False


def test_validate_hint_rejects_empty():
    assert validate_ai_hint("", "Too High") is False
    assert validate_ai_hint(None, "Too High") is False


def test_validate_hint_rejects_overlong():
    assert validate_ai_hint("go higher! " * 30, "Too Low") is False


def test_validate_hint_accepts_consistent_hint():
    assert validate_ai_hint("Aim higher, you're getting closer!", "Too Low") is True
    assert validate_ai_hint("Try a smaller guess next time.", "Too High") is True


# ---------------------------------------------------------------------------
# get_hint_with_fallback (reliability system)
# ---------------------------------------------------------------------------

def test_fallback_used_when_ai_raises():
    client = _mock_client_raising()
    hint_text, source, confidence = get_hint_with_fallback("Too High", 60, 1, 100, [60], client=client)
    assert source == "fallback"
    assert hint_text == get_hint_message("Too High")
    assert confidence == 1.0


def test_fallback_used_when_ai_response_invalid():
    client = _mock_client_returning("Go lower, you're at 60!")
    hint_text, source, confidence = get_hint_with_fallback("Too High", 60, 1, 100, [60], client=client)
    assert source == "fallback"
    assert hint_text == get_hint_message("Too High")
    assert confidence == 1.0


def test_ai_hint_used_when_response_valid():
    client = _mock_client_returning("Try a smaller number next time.")
    hint_text, source, confidence = get_hint_with_fallback("Too High", 60, 1, 100, [60], client=client)
    assert source == "ai"
    assert hint_text == "Try a smaller number next time."
    assert confidence == 1.0


def test_consistency_across_repeated_calls():
    client = _mock_client_returning("Try a smaller number next time.")
    first = get_hint_with_fallback("Too High", 60, 1, 100, [60], client=client)
    second = get_hint_with_fallback("Too High", 60, 1, 100, [60], client=client)
    assert first == second


# ---------------------------------------------------------------------------
# score_hint_confidence
# ---------------------------------------------------------------------------

def test_confidence_high_for_clean_encouraging_hint():
    assert score_hint_confidence("Try a smaller number next time.", "Too High") == 1.0


def test_confidence_low_for_leaked_digit():
    assert score_hint_confidence("Try something closer to 50 next time!", "Too Low") <= 0.4


def test_confidence_low_for_contradictory_direction():
    assert score_hint_confidence("Try going a bit lower next time!", "Too Low") <= 0.4


def test_confidence_zero_for_empty_hint():
    assert score_hint_confidence("", "Too High") == 0.0
    assert score_hint_confidence(None, "Too High") == 0.0


def test_confidence_always_within_bounds():
    samples = [
        ("", "Too High"),
        ("go higher! " * 30, "Too Low"),
        ("The secret is close to 42, keep trying!", "Too High"),
        ("Try a smaller number next time.", "Too High"),
        ("Nice guess!", "Win"),
    ]
    for hint_text, outcome in samples:
        confidence = score_hint_confidence(hint_text, outcome)
        assert 0.0 <= confidence <= 1.0
