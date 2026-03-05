# Game Glitch Investigator — Debug Report

## Game Purpose

A Streamlit-based number guessing game where the player tries to guess a secret number within a limited number of attempts. The game gives "Go Higher" or "Go Lower" hints after each guess. Difficulty settings (Easy, Normal, Hard) change the number range and attempt limit.

---

## Bug Found — Wrong Hints (Logic Bug)

**Location:** `app.py`, lines 158–161 (before fix)

**What it looked like:**

```python
if st.session_state.attempts % 2 == 0:
    secret = str(st.session_state.secret)   # ← converts to string on even attempts
else:
    secret = st.session_state.secret
```

**What went wrong:**
On every even-numbered attempt (2nd, 4th, 6th…), the secret number was cast to a string before being passed to `check_guess`. Inside `check_guess`, comparing an `int` to a `str` raises a `TypeError`, which falls into the `except` block that converts the guess to a string too and then does **string (alphabetical) comparison** instead of numeric comparison.

String comparison goes character by character. For example:

- `"98" > "47"` → `True` (because `"9" > "4"`) — says "Go Higher" even when you're way above
- `"50" > "47"` → `True` (correct by coincidence)
- `"100" > "47"` → `False` (because `"1" < "4"`) — would say "Go Lower" when you're above

This is why guessing 50 → 75 → 87 → 94 → 98 → 99 → 100 all returned "Go Higher" even though the secret was 47. The even-attempt string comparison kept giving incorrect feedback.

**Fix applied:**

```python
# Removed the even/odd branch entirely
secret = st.session_state.secret

outcome, message = check_guess(guess_int, secret)
```

Always pass the secret as an integer so `check_guess` always uses numeric comparison.

---

## Bug 2 — Hints Are Backwards (Logic Bug)

**Location:** `app.py`, `check_guess` function (before fix)

**What it looked like:**

```python
if guess > secret:
    return "Too High", "📈 Go HIGHER!"   # ← wrong: guess is too high, should say Go LOWER
else:
    return "Too Low", "📉 Go LOWER!"     # ← wrong: guess is too low, should say Go HIGHER
```

**What went wrong:**
The hint messages were completely swapped. When your guess is higher than the secret ("Too High"), the game told you to go even higher. When your guess was lower ("Too Low"), it told you to go lower. No matter what direction you guessed, the hint pushed you further away from the answer.

**Fix applied:**

```python
if guess > secret:
    return "Too High", "📉 Go LOWER!"
else:
    return "Too Low", "📈 Go HIGHER!"
```

Swapped the messages so the hint correctly tells the player which direction to adjust their next guess.

---

## Bug 3 — Difficulty Range Not Applied to Secret Number (State Bug)

**Location:** `app.py`, secret initialization and New Game button (before fix)

**What it looked like:**

```pythonh
# Secret only generated once, never updates when difficulty changes
if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# New Game always uses 1–100 regardless of difficulty
if new_game:
    st.session_state.secret = random.randint(1, 100)

# Info text hardcoded instead of using low/high
st.info(f"Guess a number between 1 and 100. ...")
```

**What went wrong:**
Three related problems caused the same symptom — the difficulty setting had no real effect on gameplay:

1. The secret is guarded by `if "secret" not in st.session_state`, so once set it never changes. Switching difficulty updates the sidebar display but the existing secret stays, potentially outside the new range entirely.
2. The New Game button hardcoded `random.randint(1, 100)` instead of using `low, high` from the current difficulty. So even starting a fresh game on Easy (1–20) or Hard (1–50) would generate a secret anywhere from 1–100.
3. The info text shown to the player was hardcoded as `"between 1 and 100"`, so even after fixing the secret generation, the displayed range never reflected the actual difficulty.

**Fix applied:**

```python
# Reset secret whenever difficulty changes
if "secret" not in st.session_state or st.session_state.get("difficulty") != difficulty:
    st.session_state.secret = random.randint(low, high)
    st.session_state.difficulty = difficulty

# New Game uses the correct range
if new_game:
    st.session_state.secret = random.randint(low, high)

# Info text now uses dynamic low/high
st.info(f"Guess a number between {low} and {high}. ...")
```

Stored the current difficulty in session state so any change is detected and triggers a new secret within the correct range. New Game also now uses `low, high` instead of hardcoded values. The info text was updated to display the actual range.

---

## Bug 4 — Attempts Left Off By One After New Game (State Bug)

**Location:** `app.py`, New Game button handler (before fix)

**What it looked like:**

```python
if "attempts" not in st.session_state:
    st.session_state.attempts = 1   # initialized to 1 on first load

if new_game:
    st.session_state.attempts = 0   # ← reset to 0, inconsistent with initialization
```

**What went wrong:**
On first load, `attempts` is initialized to `1`. The display uses `attempt_limit - st.session_state.attempts` to show attempts remaining. So on a fresh load with Normal difficulty (limit 8), it correctly shows 7 attempts left. But New Game reset `attempts` to `0`, making the display show 8 — one more than it should. The two code paths started from different values.

**Fix applied:**

```python
if new_game:
    st.session_state.attempts = 1   # matches initialization value
```

Reset to `1` so New Game is consistent with the initial state on first load.

---

## Bug 5 — No Bounds Validation on Guess Input (Logic Bug)

**Location:** `app.py`, submit handler (before fix)

**What it looked like:**

```python
ok, guess_int, err = parse_guess(raw_guess)
# no check whether guess_int is within [low, high]
outcome, message = check_guess(guess_int, secret)
```

**What went wrong:**
`parse_guess` only checks that the input is a valid integer. It never validates whether the guess is within the difficulty's allowed range. A player could enter `-1`, `0`, or `999` and the game would process it normally, giving hints based on an out-of-bounds value.

**Fix applied:**

```python
if guess_int < low or guess_int > high:
    st.error(f"Please enter a number between {low} and {high}.")
else:
    # proceed with check_guess, update_score, win/lose logic
```

Added a bounds check after parsing. Out-of-range guesses show an error and skip all game logic so they don't affect the score or attempt count.

---

## Bug 6 — Decimal Inputs Silently Accepted (Logic Bug)

**Location:** `app.py`, `parse_guess` function (before fix)

**What it looked like:**
```python
try:
    if "." in raw:
        value = int(float(raw))   # ← 1.5 becomes 1 silently
    else:
        value = int(raw)
```

**What went wrong:**
The function intentionally handled decimal inputs by converting them to integers — `"1.5"` became `1`, `"9.9"` became `9`. This silently accepted invalid input without any feedback to the player, and could produce misleading results (e.g. typing `47.9` and having it count as a guess of `47`).

**Fix applied:**
```python
if "." in raw:
    return False, None, "Please enter a whole number, not a decimal."

try:
    value = int(raw)
```

Decimal inputs now return an error immediately instead of being silently rounded.

---

## Bug 7 — Invalid Guesses Count as Attempts and Pollute History (Logic Bug)

**Location:** `app.py`, submit handler (before fix)

**What it looked like:**
```python
if submit:
    st.session_state.attempts += 1  # ← increments before any validation

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)  # ← saves invalid input to history
        st.error(err)
```

**What went wrong:**
The attempt counter incremented unconditionally on every submit click, even for invalid inputs like decimals or out-of-bounds numbers. Invalid inputs (e.g. `"1.5"`) were also appended to history. This meant spamming an invalid guess would drain all attempts and fill history with junk, as seen with `Attempts: 33` and history full of `"1.5"` entries.

**Fix applied:**
```python
if submit:
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.error(err)  # no attempt increment, no history append
    else:
        if guess_int < low or guess_int > high:
            st.error(...)  # no attempt increment, no history append
        else:
            st.session_state.attempts += 1      # only valid, in-bounds guesses count
            st.session_state.history.append(guess_int)
```

Moved both `attempts += 1` and `history.append` inside the valid, in-bounds branch so only real guesses are counted.

---

## Bug 8 — Hard and Normal Difficulty Ranges Swapped (Logic Bug)

**Location:** `app.py`, `get_range_for_difficulty` function (before fix)

**What it looked like:**
```python
if difficulty == "Normal":
    return 1, 100   # ← 100-number range on Normal
if difficulty == "Hard":
    return 1, 50    # ← 50-number range on Hard (easier!)
```

**What went wrong:**
Both the number ranges and the attempt limits for Normal and Hard were swapped — Hard had a smaller range (1–50) with fewer attempts (5), while Normal had a larger range (1–100) with more attempts (8). This made Hard objectively easier than Normal.

**Fix applied:**
```python
# Ranges
if difficulty == "Normal":
    return 1, 50
if difficulty == "Hard":
    return 1, 100

# Attempt limits
attempt_limit_map = {
    "Easy": 6,
    "Normal": 5,
    "Hard": 8,
}
```

Swapped both ranges and attempt limits so Normal (1–50, 5 attempts) and Hard (1–100, 8 attempts) correctly reflect their intended difficulty.
