# AI Interactions Log

## AI Feature Setup (Reliability/Testing System)

This project uses the OpenAI API to generate the in-game hint text, wrapped in a validation
guardrail (`ai_hints.py`) that checks each AI response for consistency with the actual guess
outcome before showing it. If the API call fails or the response is invalid, the game falls
back to the deterministic hint automatically — no crash, no misleading hint.

**Setup:**
1. `pip install -r requirements.txt`
2. Set your API key as an environment variable: `setx OPENAI_API_KEY "sk-..."` (Windows) or
   `export OPENAI_API_KEY=sk-...` (macOS/Linux). The app runs fine without a key set — it just
   always uses the fallback hint in that case.
3. Run the app: `streamlit run app.py`
4. Run the tests (no API key required — the OpenAI client is mocked):
   `pytest`

Check `ai_reliability.log` after playing to see logged AI calls, guardrail results, and
fallback triggers.


> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**What did the agent do?**

<!-- List the steps the agent took (files edited, commands run, etc.) -->

**What did you have to verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| | | | | |
| | | | | |
| | | | | |

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
<!-- Paste the prompt you gave the AI -->
```

**Linting output before:**

```
<!-- Paste relevant linter warnings/errors -->
```

**Changes applied:**

<!-- Describe what you changed based on the AI's suggestions -->

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->
