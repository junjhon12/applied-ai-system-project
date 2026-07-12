# Glitchy Guesser: AI-Reliable Hint System

## Original Project (Modules 1–3)

This project builds on **Glitchy Guesser**, a Streamlit number-guessing game originally built in Modules 1–3. The original goal was a simple, self-contained guessing game: pick a difficulty (Easy: 1–20, Normal: 1–100, Hard: 1–200), guess the secret number within a limited number of attempts, and track a score based on attempts remaining. Hints in the original version were static, rule-based text (`get_hint_message`) with no AI involved.

## Title & Summary

This iteration layers an **AI-generated hint feature with a reliability guardrail** on top of the original game. After each guess, the app asks an LLM (OpenAI `gpt-4o-mini`) to write a short, encouraging hint in natural language — but every hint is validated before it ever reaches the player, and falls back to the original deterministic hint if the AI response can't be trusted. It matters because it's a small, concrete example of *safely* wiring an LLM into an application: instead of trusting model output blindly, the system treats it as untrusted input that must pass a guardrail, with full logging and a human-visible fallback path for when things go wrong.

## Architecture Overview

See [`assets/diagrams/system-diagram.md`](assets/diagrams/system-diagram.md) for the full Mermaid diagram. In short:

```
Player → app.py (UI/controller) → logic_utils.check_guess() → outcome ("Win" / "Too High" / "Too Low")
                                                                     │
                                                                     ▼
                                                    ai_hints.generate_ai_hint()  (calls OpenAI)
                                                                     │
                                                                     ▼
                                                    ai_hints.validate_ai_hint()  (guardrail)
                                                          │passes            │fails / API error
                                                          ▼                  ▼
                                                     AI hint shown    logic_utils.get_hint_message()
                                                          │            (deterministic fallback)
                                                          └────────────────┬───────────────┘
                                                                           ▼
                                                                     Shown to Player
```

Every AI call and every guardrail decision is logged to `ai_reliability.log`. A "Developer Debug Info" panel in the Streamlit UI shows which source (`ai` or `fallback`) produced the last hint, so a human can observe the system's reliability live. A separate offline test suite (`tests/test_ai_reliability.py`, `tests/test_game_logic.py`) exercises the guardrail and fallback logic against a **mocked** OpenAI client, so correctness can be verified without live API calls, keys, or cost.

**Key files:**
- `app.py` — Streamlit UI and game controller
- `logic_utils.py` — pure game logic (range selection, guess parsing, win/loss check, scoring, fallback hint text)
- `ai_hints.py` — AI hint generation, the `validate_ai_hint` guardrail, and the fallback wiring
- `assets/diagrams/system-diagram.md` — architecture diagram

## Setup Instructions

1. Clone the repository and `cd` into it.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. (Optional) Set your OpenAI API key so hints are AI-generated:
   ```
   set OPENAI_API_KEY=your-key-here      # Windows
   export OPENAI_API_KEY=your-key-here   # macOS/Linux
   ```
   The game works fine without a key — every hint simply falls back to the deterministic version, and this is logged.
4. Run the app:
   ```
   streamlit run app.py
   ```
5. Run the test suite:
   ```
   pytest
   ```
   No API key is required for tests — the OpenAI client is mocked.

## Sample Interactions

**1. Guess too high, AI hint passes the guardrail**
- Secret: 42 (Normal difficulty, range 1–100). Player guesses `70`.
- Outcome: `"Too High"`.
- AI response: *"Great try — aim a bit lower on your next guess!"*
- Guardrail check: no digits, no length violation, no contradictory direction words (doesn't say "higher"/"bigger") → **passes**.
- Shown to player: *"Great try — aim a bit lower on your next guess!"* (source: `ai`)

**2. Guess too low, AI hint fails the guardrail (leaks a number)**
- Secret: 42. Player guesses `10`.
- Outcome: `"Too Low"`.
- AI response: *"Try something closer to 50 next time!"*
- Guardrail check: response contains a digit (`50`), which risks revealing information about the secret → **fails**.
- System falls back: *"📈 Go HIGHER!"* (source: `fallback`), and the rejection is logged to `ai_reliability.log`.

**3. Winning guess**
- Secret: 42. Player guesses `42` on attempt 6 of 8 (Normal difficulty, attempt limit 8).
- Outcome: `"Win"`.
- Hint shown: *"🎉 Correct!"*
- Score update: `update_score(0, "Win", 6, 8)` → `8 - 6 = 2` points added (score reflects attempts *remaining*, not attempts used).

## Design Decisions

- **Guardrail + deterministic fallback instead of trusting the LLM directly.** An LLM can hallucinate, leak the secret number, or contradict the actual game outcome. `validate_ai_hint` rejects empty/`None` responses, overly long text, any hint containing a digit (which could leak the secret), and hints whose wording contradicts the true direction (e.g., saying "go higher" when the outcome was "Too High"). Anything that fails is replaced with the same static hint the original game used — so the AI feature can never make the game *less* correct than it was before.
- **`gpt-4o-mini` with a short `max_tokens` and timeout.** Keeps latency and cost low for what is a one-sentence hint, and bounds worst-case wait time in a synchronous UI.
- **Everything is logged.** Every AI call and every guardrail decision (pass/fail/reason) is written to `ai_reliability.log`, so reliability can be audited after the fact rather than only observed live.
- **Trade-off:** when the guardrail rejects a hint, the player sees a generic, less personalized message instead of AI-flavored text. This is an intentional trade — correctness and safety are prioritized over hint variety.
- **Streamlit over a custom frontend.** Chosen for speed of development given the scope of the project; it also makes exposing a "Developer Debug Info" panel (useful for observing AI reliability) trivial.
- **Unpinned dependencies (`streamlit`, `pytest`, `openai`).** Simpler for a small course project, at the cost of reproducibility across environments — a production app would pin exact versions.

## Testing Summary

All **26 tests pass** (`pytest`):
- `tests/test_game_logic.py` (12 tests) — covers `check_guess` outcomes, `update_score` across wins/losses and difficulty levels, and a regression test that guards against reintroducing the old (buggy) scoring formula.
- `tests/test_ai_reliability.py` (14 tests) — covers `validate_ai_hint` rejecting contradictory-direction hints, leaked digits, and empty/overlong text; `get_hint_with_fallback` correctly falling back on API exceptions and on invalid AI responses, and using the AI hint when it's valid; and `score_hint_confidence` producing bounded, meaningfully graded scores for clean vs. risky hints. The OpenAI client is mocked throughout, so tests run offline with no API key and no cost.

26 of 26 tests passed; the guardrail's negative cases (leaked numbers, contradictory direction, empty/overlong text) were the ones most worth testing, since those are exactly where an ungated LLM would fail silently.

**Confidence scoring.** Beyond the pass/fail guardrail, `score_hint_confidence(hint_text, outcome)` grades every hint 0.0–1.0 using the same risk signals as the guardrail (leaked digits, contradictory direction, length), so even a hint that *passes* validation carries a trust signal instead of a bare boolean. Fallback hints are deterministic and always score `1.0`. Sample hints scored:

| Hint text | Outcome | Guardrail | Confidence |
|---|---|---|---|
| "Great try — aim a bit lower on your next guess!" | Too High | Pass | 1.00 |
| "Aim higher, you're getting closer!" | Too Low | Pass | 1.00 |
| "Try something closer to 50 next time!" | Too Low | Fail (leaked digit) | 0.30 |
| "Try going a bit lower next time!" | Too Low | Fail (contradicts outcome) | 0.40 |

Confidence averaged **1.0** across the two guardrail-passing samples and **0.35** across the two rejected samples — the score consistently tracks the same failure modes as the guardrail (digit leaks and contradictory direction), confirming the two signals agree rather than measuring unrelated things.

**What worked:** separating pure game logic (`logic_utils.py`) from the AI layer (`ai_hints.py`) made both sides independently and thoroughly testable — the guardrail's negative cases (the ways an AI hint *shouldn't* be trusted) turned out to be just as important to test as the happy path.

**What didn't at first:** earlier versions of the game logic had a tuple-return bug that silently broke hint directions, and a scoring formula that used attempts *used* instead of attempts *remaining* — both were only caught once dedicated unit tests were written (see `# FIX:` comments in `logic_utils.py`), which reinforced how easy it is for logic bugs to hide behind a UI that "looks" like it's working.

**What didn't get tested:** live behavior against the real OpenAI API (network failures, rate limits, non-deterministic phrasing) is only exercised manually via the running app, not by the automated suite. Confidence scoring is a heuristic (not a calibrated probability), so it should be read as a relative trust signal, not an accuracy guarantee.

## Reproducible Execution Evidence

This section contains real, captured command output — not hand-typed examples — so the system can be verified without running anything or watching a video.

**1. Test suite run**

```
$ python -m pytest -v

============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\AI110\applied-ai-system-project
plugins: anyio-4.13.0
collecting ... collected 26 items

tests/test_ai_reliability.py::test_validate_hint_rejects_contradictory_direction PASSED [  3%]
tests/test_ai_reliability.py::test_validate_hint_rejects_leaked_number PASSED [  7%]
tests/test_ai_reliability.py::test_validate_hint_rejects_empty PASSED    [ 11%]
tests/test_ai_reliability.py::test_validate_hint_rejects_overlong PASSED [ 15%]
tests/test_ai_reliability.py::test_validate_hint_accepts_consistent_hint PASSED [ 19%]
tests/test_ai_reliability.py::test_fallback_used_when_ai_raises PASSED   [ 23%]
tests/test_ai_reliability.py::test_fallback_used_when_ai_response_invalid PASSED [ 26%]
tests/test_ai_reliability.py::test_ai_hint_used_when_response_valid PASSED [ 30%]
tests/test_ai_reliability.py::test_consistency_across_repeated_calls PASSED [ 34%]
tests/test_ai_reliability.py::test_confidence_high_for_clean_encouraging_hint PASSED [ 38%]
tests/test_ai_reliability.py::test_confidence_low_for_leaked_digit PASSED [ 42%]
tests/test_ai_reliability.py::test_confidence_low_for_contradictory_direction PASSED [ 46%]
tests/test_ai_reliability.py::test_confidence_zero_for_empty_hint PASSED [ 50%]
tests/test_ai_reliability.py::test_confidence_always_within_bounds PASSED [ 53%]
tests/test_game_logic.py::test_winning_guess PASSED                      [ 57%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 61%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 65%]
tests/test_game_logic.py::test_score_equals_attempts_remaining PASSED    [ 69%]
tests/test_game_logic.py::test_score_wins_on_first_attempt PASSED        [ 73%]
tests/test_game_logic.py::test_score_wins_on_last_attempt PASSED         [ 76%]
tests/test_game_logic.py::test_score_uses_attempts_remaining_not_attempts_used PASSED [ 80%]
tests/test_game_logic.py::test_score_unchanged_on_too_high PASSED        [ 84%]
tests/test_game_logic.py::test_score_unchanged_on_too_low PASSED         [ 88%]
tests/test_game_logic.py::test_score_unchanged_on_loss_nonzero_starting_score PASSED [ 92%]
tests/test_game_logic.py::test_score_easy_difficulty PASSED              [ 96%]
tests/test_game_logic.py::test_score_hard_difficulty PASSED              [100%]

============================= 26 passed in 0.06s ==============================
```

**2. End-to-end demo run** — `demo_run.py` (new, committed script) drives the real game logic (`check_guess`, `update_score`) and the real hint pipeline (`get_hint_with_fallback`) through 3 scripted guesses, using a mocked OpenAI client so it's deterministic, free, and needs no API key:

```
$ python demo_run.py

Glitchy Guesser — AI hint reliability demo

=== Case 1: Guardrail passes ===
Input:  secret=42, guess=70, range=(1,100), attempt=3/8
Outcome: Too High
Hint shown: "Great try — aim a bit lower on your next guess!" (source=ai, confidence=1.00)
Score: 0 -> 0

=== Case 2: Guardrail fails (leaked digit) -> fallback ===
Input:  secret=42, guess=10, range=(1,100), attempt=4/8
Outcome: Too Low
Hint shown: "📈 Go HIGHER!" (source=fallback, confidence=1.00)
Score: 2 -> 2

=== Case 3: AI call raises exception -> fallback ===
Input:  secret=42, guess=42, range=(1,100), attempt=6/8
Outcome: Win
Hint shown: "🎉 Correct!" (source=fallback, confidence=1.00)
Score: 2 -> 4

See ai_reliability.log for the corresponding logged guardrail decisions.
```

**3. Matching entries from `ai_reliability.log`** (produced by the run above — every AI call and guardrail decision is logged):

```
2026-07-11 20:07:02,741 INFO AI call ok | prompt=...guessed 70 and the outcome was 'Too High'... | response=Great try — aim a bit lower on your next guess!
2026-07-11 20:07:02,741 INFO Guardrail passed | outcome=Too High | confidence=1.00
2026-07-11 20:07:02,742 INFO AI call ok | prompt=...guessed 10 and the outcome was 'Too Low'... | response=Try something closer to 50 next time!
2026-07-11 20:07:02,742 INFO Guardrail failed or AI unavailable, using fallback | outcome=Too Low | confidence=1.00
2026-07-11 20:07:02,742 WARNING AI call failed | prompt=...guessed 42 and the outcome was 'Win'... | error=API down
2026-07-11 20:07:02,742 INFO Guardrail failed or AI unavailable, using fallback | outcome=Win | confidence=1.00
```

**What this shows:** the guardrail correctly passes a clean AI hint (Case 1), correctly rejects one that leaks the secret number and substitutes the deterministic fallback (Case 2), and the same fallback path fires cleanly when the AI call itself raises an exception (Case 3) — all three decisions are logged in real time, and the confidence score agrees with the guardrail's pass/fail verdict in every case (1.00 for the accepted hint, 1.00 for both deterministic fallbacks, which are always maximally trusted by design).

## Portfolio

- **GitHub repo:** [https://github.com/junjhon12/applied-ai-system-project](https://github.com/junjhon12/applied-ai-system-project)

**Reflection — what this project says about me as an AI engineer:** I don't treat an LLM's output as a trusted service response — I treat it the same way I'd treat unvalidated user input: something that has to pass an explicit check before it reaches anyone. That's why `validate_ai_hint` is a hard gate (reject leaked digits, contradictions, empty/overlong text) backed by a graded `score_hint_confidence` signal and a deterministic fallback that can never make the system less correct than before the AI feature existed, with every decision logged so reliability is auditable after the fact, not just observed live. I also lean on tests to catch what manual play won't — the tuple-return and attempts-used-vs-remaining bugs in `logic_utils.py` were only caught once dedicated unit tests existed, which reinforces that "it looks like it's working" and "it's correct" are different claims. At the same time, I'm upfront in `model_card.md` about where this system is weak — the guardrail is regex/keyword-based and would miss synonyms or non-English phrasing, and the confidence score is a heuristic, not a calibrated probability — because shipping something safe also means being honest about its limits.

## Reflection

Building the guardrail and fallback layer was a useful exercise in treating LLM output as untrusted input rather than a trusted service response — the same mindset as validating user input, just applied to a model's output instead. It reinforced that a small amount of deterministic scaffolding (a validator plus a known-safe fallback) can make an otherwise unpredictable AI feature safe to ship, even in a small project. The graded responsible-AI reflection — covering AI collaboration, a helpful and a flawed AI suggestion, and system limitations — is documented separately in [`model_card.md`](model_card.md).
