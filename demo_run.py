"""End-to-end reproducible demo of the AI hint reliability system.

Runs three scripted guesses through the real game logic and hint pipeline,
using a mocked OpenAI client (no API key or network access needed) so the
output below is deterministic and free to reproduce with:

    python demo_run.py
"""
from unittest.mock import MagicMock

from ai_hints import get_hint_with_fallback
from logic_utils import check_guess, update_score


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


def run_case(label, secret, guess, low, high, attempt, max_attempts, score, client):
    outcome = check_guess(guess, secret)
    hint_text, source, confidence = get_hint_with_fallback(
        outcome, guess, low, high, [guess], client=client
    )
    new_score = update_score(score, outcome, attempt, max_attempts)

    print(f"=== {label} ===")
    print(f"Input:  secret={secret}, guess={guess}, range=({low},{high}), "
          f"attempt={attempt}/{max_attempts}")
    print(f"Outcome: {outcome}")
    print(f"Hint shown: \"{hint_text}\" (source={source}, confidence={confidence:.2f})")
    print(f"Score: {score} -> {new_score}")
    print()


if __name__ == "__main__":
    print("Glitchy Guesser — AI hint reliability demo\n")

    # Case 1: guardrail PASSES (clean AI response, no digits, no contradiction)
    run_case(
        "Case 1: Guardrail passes",
        secret=42, guess=70, low=1, high=100, attempt=3, max_attempts=8, score=0,
        client=_mock_client_returning("Great try — aim a bit lower on your next guess!"),
    )

    # Case 2: guardrail FAILS — AI response leaks a digit -> falls back
    run_case(
        "Case 2: Guardrail fails (leaked digit) -> fallback",
        secret=42, guess=10, low=1, high=100, attempt=4, max_attempts=8, score=2,
        client=_mock_client_returning("Try something closer to 50 next time!"),
    )

    # Case 3: AI call raises an exception entirely -> fallback
    run_case(
        "Case 3: AI call raises exception -> fallback",
        secret=42, guess=42, low=1, high=100, attempt=6, max_attempts=8, score=2,
        client=_mock_client_raising(),
    )

    print("See ai_reliability.log for the corresponding logged guardrail decisions.")
