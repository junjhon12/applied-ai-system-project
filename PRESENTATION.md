# Presentation Outline — Glitchy Guesser: AI-Reliable Hint System

Target length: 5-7 minutes. Timings are cues, not hard stops.

## 1. Hook (0:00-0:30)

"This is a number-guessing game where an LLM writes the hints — but the LLM is never trusted directly. Every hint it generates has to pass a guardrail before a player ever sees it, and if it fails, the game silently falls back to the same deterministic hint it always had. That's the whole idea: treat model output like untrusted input."

## 2. System walkthrough (0:30-2:15)

- Walk the flow from `assets/diagrams/system-diagram.md`: Player → `app.py` → `logic_utils.check_guess()` → outcome → `ai_hints.generate_ai_hint()` (calls OpenAI `gpt-4o-mini`) → `ai_hints.validate_ai_hint()` (guardrail) → AI hint shown *or* fallback → Player.
- Name the guardrail rules in `validate_ai_hint`: reject empty/`None`, reject text over 200 chars, reject any digit (could leak the secret number), reject wording that contradicts the actual outcome (e.g., "go higher" when the outcome was "Too High").
- Mention `score_hint_confidence`: a graded 0.0-1.0 trust signal using the same risk signals as the guardrail, so even a *passing* hint carries a confidence number instead of a bare boolean.
- Everything — every AI call, every guardrail decision — is logged to `ai_reliability.log`.

## 3. Live demo (2:15-4:15)

Two options, pick based on time/setup:

- **Scripted, guaranteed to work:** `python demo_run.py` — runs 3 real cases through the actual pipeline with a mocked OpenAI client (no key needed): a guardrail pass, a guardrail fail from a leaked digit, and a fallback triggered by an API exception. Narrate the printed output live.
- **Interactive:** `streamlit run app.py`, play a guess, and point out the "Developer Debug Info" panel showing hint source (`ai`/`fallback`) and confidence.

Either way, show the corresponding lines appearing in `ai_reliability.log` as proof the guardrail decision is actually being recorded, not just displayed.

## 4. Testing & reliability evidence (4:15-5:15)

- `pytest -v` → 26/26 tests pass, offline, no API key or cost (OpenAI client mocked throughout).
- Point out that the negative cases — leaked digits, contradictory direction, empty/overlong text — were the ones most worth testing, since those are exactly where an ungated LLM would fail silently.
- Reference the README's "Reproducible Execution Evidence" section — a grader can verify all of this from text alone, no video required.

## 5. What I learned (5:15-6:15)

- Treating LLM output as untrusted input is the same discipline as validating user input — just applied to a model's response instead of a form field.
- Two real logic bugs (a tuple-return bug and an attempts-used-vs-remaining scoring bug in `logic_utils.py`) were only caught once dedicated unit tests existed — a reminder that "looks like it's working" and "is correct" are different claims.
- The guardrail and confidence score are useful but limited: both are regex/keyword-based and would miss synonyms or non-English phrasing; confidence is a heuristic, not a calibrated probability. Documented honestly in `model_card.md`.

## 6. Close (6:15-7:00)

- GitHub: https://github.com/junjhon12/applied-ai-system-project
- One-line takeaway: "A small amount of deterministic scaffolding — a validator plus a known-safe fallback — is what makes an otherwise unpredictable AI feature safe to ship."
