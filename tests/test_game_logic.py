from logic_utils import check_guess, update_score


# ---------------------------------------------------------------------------
# check_guess
# ---------------------------------------------------------------------------

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# update_score — core formula: score == attempt_limit - attempt_number
# ---------------------------------------------------------------------------

def test_score_equals_attempts_remaining():
    """
    Score must equal the attempts remaining shown to the player at the moment
    of the winning guess. In app.py, attempts is incremented before update_score
    is called, so the app passes attempt_number - 1. We mirror that here:
    8 allowed, winning on the 6th guess -> player saw 3 left -> score = 3.
    """
    score = update_score(current_score=0, outcome="Win", attempt_number=5, attempt_limit=8)
    assert score == 3, f"Expected 3 (attempts remaining before winning guess), got {score}"

def test_score_wins_on_first_attempt():
    """Winning on the first guess: attempt_number=0 (before increment), score = 8."""
    score = update_score(current_score=0, outcome="Win", attempt_number=0, attempt_limit=8)
    assert score == 8

def test_score_wins_on_last_attempt():
    """Winning on the last guess: attempt_number=7 (before increment), score = 1."""
    score = update_score(current_score=0, outcome="Win", attempt_number=7, attempt_limit=8)
    assert score == 1

def test_score_uses_attempts_remaining_not_attempts_used():
    """
    Regression guard: result must NOT equal attempt_number itself.
    With attempt_number=5 and attempt_limit=8, score should be 3, not 5.
    """
    attempt_number = 5
    attempt_limit = 8
    score = update_score(current_score=0, outcome="Win", attempt_number=attempt_number, attempt_limit=attempt_limit)
    assert score != attempt_number, (
        f"Score ({score}) must not equal attempt_number ({attempt_number}); "
        "that would mean the old broken formula is still in use."
    )


# ---------------------------------------------------------------------------
# update_score — loss cases: score must never change
# ---------------------------------------------------------------------------

def test_score_unchanged_on_too_high():
    score = update_score(current_score=0, outcome="Too High", attempt_number=3, attempt_limit=8)
    assert score == 0

def test_score_unchanged_on_too_low():
    score = update_score(current_score=0, outcome="Too Low", attempt_number=3, attempt_limit=8)
    assert score == 0

def test_score_unchanged_on_loss_nonzero_starting_score():
    """Score should not change on a wrong guess even if score is already above 0."""
    score = update_score(current_score=5, outcome="Too Low", attempt_number=2, attempt_limit=8)
    assert score == 5


# ---------------------------------------------------------------------------
# update_score — difficulty variations
# ---------------------------------------------------------------------------

def test_score_easy_difficulty():
    """Easy: 6 attempts allowed, win on attempt 4 -> 2 remaining."""
    score = update_score(current_score=0, outcome="Win", attempt_number=4, attempt_limit=6)
    assert score == 2

def test_score_hard_difficulty():
    """Hard: 5 attempts allowed, win on attempt 2 -> 3 remaining."""
    score = update_score(current_score=0, outcome="Win", attempt_number=2, attempt_limit=5)
    assert score == 3