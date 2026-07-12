# Model Card: Glitchy Guesser AI Hint System

This card documents the AI-generated hint feature layered on top of the number-guessing game (`ai_hints.py`), and reflects on the responsible-AI and collaboration aspects of building it.

## What are the limitations or biases in your system?

The confidence score returned by `score_hint_confidence()` is a hand-tuned heuristic, not a calibrated probability. It starts at 1.0 and subtracts fixed penalties (-0.6 for a leaked digit, -0.6 for a direction word that contradicts the outcome, -0.3 for length outside 10-200 characters, -0.1 for a Too High/Too Low outcome with no direction word at all), clamped to [0, 1]. Those weights were chosen by judgment, not derived from data, so a "0.7" hint isn't 70% likely to be good in any statistical sense — it's a relative trust signal, and the README says as much.

The guardrail in `validate_ai_hint()` is regex/keyword-based: it rejects digits with `\d` and checks a fixed list of direction words ("higher", "bigger", "lower", "smaller", etc.) against the outcome. This catches the failure modes we tested for, but it's brittle to phrasing we didn't test — a synonym, a non-English response, or an indirect reference ("you're close to a hundred") could slip past both the digit check and the direction-word check.

Testing is also entirely mocked. `tests/test_ai_reliability.py` stubs the OpenAI client with `unittest.mock.MagicMock`, so none of the 14 AI-reliability tests exercise real network failures, rate limiting, or the actual non-deterministic phrasing GPT-4o-mini produces in production — that gap is called out directly in the README's "what didn't get tested" section.

## Could your AI be misused, and how would you prevent that?

The main misuse vector is prompt injection through the game state passed into `_build_prompt()` (the guess history and current outcome) — someone could try to manipulate that state to get the model to output the secret number directly, unrelated content, or an abnormally long response.

Several mitigations are already in place: `validate_ai_hint()` hard-rejects any hint containing a digit, so even if the model is coaxed into leaking the number, it never reaches the player; `MAX_HINT_LENGTH` bounds output length; `generate_ai_hint()` sets `max_tokens=60` and a 10-second timeout, limiting both cost exposure and runaway output; and `get_hint_with_fallback()` is fail-closed — any API exception or guardrail failure returns the deterministic fallback from `logic_utils.get_hint_message()` (confidence 1.0) instead of ever showing unvalidated model output.

The gap worth naming honestly: these guardrails validate the *output* of the model, not the *inputs* going into the prompt. There's no sanitization on what's interpolated into `_build_prompt()` itself. For this project — a solo local game with no other users' data at stake — the real-world risk is low, but the same code structure applied to a multi-user or higher-stakes context would need input-side validation too, not just output-side.

## What surprised me while testing my AI's reliability?

How easily a plausible-sounding hint failed the guardrail despite a fairly explicit prompt. `_build_prompt()` already tells the model the outcome and asks it to indicate direction without revealing the number, yet the negative-path tests in `test_ai_reliability.py` (contradictory-direction hints, digit-leaking hints) weren't edge cases dreamed up for coverage — they reflect real ways a well-instructed model can still drift. That's what justified having a second, independent guardrail layer instead of trusting prompt engineering alone.

The other surprise was in `score_hint_confidence()`'s behavior on rejected hints: per the README's test table, guardrail-rejected hints still scored 0.30-0.40, not 0. The scoring function keeps giving partial credit for things like reasonable length even when the hint fails the hard guardrail and gets swapped for a fallback. That's arguably correct (the scoring and the veto are meant to answer different questions), but it wasn't obvious until we wrote a test that asserted on the specific rejected-hint score rather than just asserting "rejected."

## Collaboration with AI during this project

**Helpful suggestion:** The fail-closed fallback design in `get_hint_with_fallback()` — always returning a safe, deterministic hint and confidence 1.0 on any exception or guardrail failure — was an AI-suggested pattern that materially improved robustness over the naive approach of just displaying whatever the API returned. It meant a network timeout or a bad model response degrades the game experience slightly (a generic hint instead of a personalized one) rather than breaking it or leaking information.

**Flawed suggestion:** AI-generated code introduced a scoring bug documented in `logic_utils.py` (`# FIX:` comment on `update_score`): the original formula used `attempt_number` (attempts *used*) directly as the score, so winning on attempt 6 of 8 scored 6 instead of 2 — backwards, since more attempts should score lower. It looked reasonable on a read-through and only surfaced once a dedicated unit test asserted the expected score for a specific attempt count. A similar case: `check_guess()` originally returned a tuple `(outcome, message)` instead of a plain string, which silently broke hint direction tests until AI itself identified and split it into `check_guess()` and `get_hint_message()`. Both cases reinforced the same lesson noted in the README: logic bugs can hide behind a UI that "looks" like it's working, and only tests — not code review by eye — caught them.
