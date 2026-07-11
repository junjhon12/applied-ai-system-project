import random
import streamlit as st
# FIX: AI refactored all game logic out of app.py into logic_utils.py so
# functions can be imported and tested independently with pytest.
from logic_utils import (
    get_range_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
)
from ai_hints import get_hint_with_fallback

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    # FIX: Was initialised to 1, making the counter show one attempt used
    # before the player did anything. AI corrected it to 0. Verified by
    # checking the "Attempts left" display on first load showed the full limit.
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "last_hint_source" not in st.session_state:
    st.session_state.last_hint_source = None

if "game_id" not in st.session_state:
    # FIX: AI introduced game_id to change the text input widget key on New Game.
    # Without this, Streamlit kept the old typed value and Submit stayed broken
    # after pressing New Game. Verified by pressing New Game mid-game and
    # confirming the input cleared and Submit worked on the fresh game.
    st.session_state.game_id = 0

st.subheader("Make a guess")

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)
    if st.session_state.last_hint_source == "ai":
        st.write("Last hint source: 🤖 AI hint")
    elif st.session_state.last_hint_source == "fallback":
        st.write("Last hint source: ⚙️ fallback hint")

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}_{st.session_state.game_id}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    # FIX: Original only reset attempts and secret, leaving status/score/history
    # stale. Pressing New Game after a win/loss hit st.stop() immediately.
    # AI fixed it to reset all five state keys and use the correct difficulty
    # range instead of hardcoded 1-100. game_id increment clears the input field.
    # Verified by winning a game then pressing New Game — game resumed correctly.
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.game_id += 1
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        # FIX: Original code alternated secret between int and str on even/odd
        # attempts, causing string comparison to flip hint directions every other
        # guess. AI removed the alternation so secret is always compared as int.
        # Verified by playing several rounds — hints were correct every time.
        secret = st.session_state.secret
        outcome = check_guess(guess_int, secret)

        if show_hint:
            hint_text, hint_source = get_hint_with_fallback(
                outcome, guess_int, low, high, st.session_state.history
            )
            st.session_state.last_hint_source = hint_source
            st.warning(hint_text)

        # FIX: attempts is incremented before this point, so passing it directly
        # gave attempt_limit - attempts which is one less than the "Attempts left"
        # the player saw before submitting. We pass attempts - 1 so the score
        # equals exactly the remaining count shown on the winning guess.
        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts - 1,
            attempt_limit=attempt_limit,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")