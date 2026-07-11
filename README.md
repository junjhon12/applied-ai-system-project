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

All **21 tests pass** (`pytest`):
- `tests/test_game_logic.py` (12 tests) — covers `check_guess` outcomes, `update_score` across wins/losses and difficulty levels, and a regression test that guards against reintroducing the old (buggy) scoring formula.
- `tests/test_ai_reliability.py` (9 tests) — covers `validate_ai_hint` rejecting contradictory-direction hints, leaked digits, and empty/overlong text, plus `get_hint_with_fallback` correctly falling back on API exceptions and on invalid AI responses, and using the AI hint when it's valid. The OpenAI client is mocked throughout, so tests run offline with no API key and no cost.

**What worked:** separating pure game logic (`logic_utils.py`) from the AI layer (`ai_hints.py`) made both sides independently and thoroughly testable — the guardrail's negative cases (the ways an AI hint *shouldn't* be trusted) turned out to be just as important to test as the happy path.

**What didn't at first:** earlier versions of the game logic had a tuple-return bug that silently broke hint directions, and a scoring formula that used attempts *used* instead of attempts *remaining* — both were only caught once dedicated unit tests were written (see `# FIX:` comments in `logic_utils.py`), which reinforced how easy it is for logic bugs to hide behind a UI that "looks" like it's working.

**What didn't get tested:** live behavior against the real OpenAI API (network failures, rate limits, non-deterministic phrasing) is only exercised manually via the running app, not by the automated suite.

## Reflection

Building the guardrail and fallback layer was a useful exercise in treating LLM output as untrusted input rather than a trusted service response — the same mindset as validating user input, just applied to a model's output instead. It reinforced that a small amount of deterministic scaffolding (a validator plus a known-safe fallback) can make an otherwise unpredictable AI feature safe to ship, even in a small project. The graded responsible-AI reflection — covering AI collaboration, a helpful and a flawed AI suggestion, and system limitations — is documented separately in [`model_card.md`](model_card.md).
