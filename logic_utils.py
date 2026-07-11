def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    # FIX: AI identified that the original function returned a tuple (outcome, message),
    # causing hint tests to always fail and hint directions to be backwards.
    # AI split this into check_guess (plain string) and get_hint_message (UI text),
    # and corrected the arrow directions. Verified by running pytest and manually
    # playing the game to confirm hints matched the actual secret number.
    """
    Compare guess to secret and return the outcome string only.

    Returns: "Win", "Too High", or "Too Low"
    Both guess and secret must be ints.
    """
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def get_hint_message(outcome: str) -> str:
    # FIX: Separated from check_guess so the UI gets emoji text while
    # tests can assert against a plain string. AI suggested this split.
    """Return an emoji hint message for display in the UI."""
    if outcome == "Win":
        return "🎉 Correct!"
    if outcome == "Too High":
        return "📉 Go LOWER!"
    return "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int, attempt_limit: int):
    # FIX: Original formula used attempt_number (attempts used) as the score,
    # so winning on attempt 6 of 8 gave a score of 6 instead of 2.
    # AI suggested the correct formula: attempt_limit - attempt_number (attempts remaining).
    # Also added attempt_limit as a parameter since the function didn't previously
    # receive it. Verified with pytest: update_score(0, "Win", 6, 8) == 2.
    """
    Update score based on outcome and attempts remaining.
    Score only increases on a win: points = attempt_limit - attempt_number.
    Score stays unchanged on a loss.
    """
    if outcome == "Win":
        return current_score + (attempt_limit - attempt_number)
    return current_score