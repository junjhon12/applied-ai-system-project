# System Diagram — Glitchy Guesser

```mermaid
flowchart TD
    Player([Player])

    subgraph Runtime["Runtime: Streamlit App"]
        UI["app.py<br/>Streamlit UI / Controller"]
        Logic["logic_utils.py<br/>Game Logic (check_guess, score, fallback hint)"]
        AIGen["ai_hints.py<br/>generate_ai_hint()<br/>(OpenAI gpt-4o-mini call)"]
        Guardrail{"validate_ai_hint()<br/>Guardrail"}
        Fallback["get_hint_message()<br/>Deterministic Fallback Hint"]
        Logger[("ai_reliability.log")]
        Debug["Developer Debug Panel<br/>(human-visible hint source)"]
    end

    subgraph Verify["Offline Verification (pytest)"]
        Tests["tests/test_ai_reliability.py<br/>tests/test_game_logic.py<br/>(mocked OpenAI client)"]
    end

    Human([Human Reviewer])

    Player -- "guess input" --> UI
    UI -- "raw_guess" --> Logic
    Logic -- "outcome (Too High/Low/Win)" --> AIGen
    AIGen -- "AI hint text" --> Guardrail
    Guardrail -- "passes" --> UI
    Guardrail -- "fails / AI unavailable" --> Fallback
    Fallback --> UI
    Guardrail -. "logs result" .-> Logger
    AIGen -. "logs call" .-> Logger
    UI -- "hint + score + status" --> Player
    UI --> Debug
    Debug -- "shows AI vs fallback source" --> Human

    Tests -. "exercises offline, no live API" .-> Guardrail
    Tests -. "exercises offline" .-> Fallback
    Human -. "reviews test results" .-> Tests

    style Guardrail fill:#f9e79f,stroke:#b7950b
    style Tests fill:#d5f5e3,stroke:#1e8449
    style Debug fill:#d6eaf8,stroke:#2874a6
```

## Notes

- **Data flow (solid arrows):** Player guess → `app.py` → `logic_utils.check_guess` → `ai_hints.generate_ai_hint` (calls OpenAI) → `validate_ai_hint` guardrail → either the AI hint or the deterministic fallback is shown back to the player.
- **Logging (dotted arrows into `ai_reliability.log`):** every AI call and guardrail decision is logged, whether the AI hint passed, failed, or the API call errored.
- **Human check-in:** the Streamlit "Developer Debug Info" panel exposes which source (`ai` or `fallback`) produced the last hint, letting a human observe AI reliability during a live session.
- **Automated testing (green subgraph):** `tests/test_ai_reliability.py` mocks the OpenAI client and asserts the guardrail rejects bad hints (contradictory direction, leaked numbers, empty/overlong text) and that the fallback path works — this is the safety net that runs before any code change reaches a real player.
