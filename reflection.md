# Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

1. On even-numbered attempts, the secret was cast to a string and compared alphabetically instead of numerically, so guesses like 98 and 100 were told "Go Higher" even when the answer was 47.
2. The "Go Higher" and "Go Lower" hint messages were swapped, so every hint sent the player in the wrong direction.
3. The secret number never reset when difficulty changed, and the New Game button always generated a secret from 1-100 regardless of the selected difficulty.
4. After clicking New Game, the attempts counter started at 0 instead of 1, showing one extra attempt than was actually available.
5. The game accepted out-of-bounds numbers like -1 or 999 as valid guesses, processing them as real attempts.
6. Decimal inputs like "1.5" were silently converted to integers instead of being rejected with an error.
7. Invalid guesses counted as real attempts and were saved to history, so spamming "1.5" drained all attempts and filled history with junk.
8. The Hard and Normal difficulty ranges and attempt limits were swapped -- Hard had the smaller range (1-50) with fewer attempts, making it objectively easier than Normal.

---

## 2. How did you use AI as a teammate?

I used Claude Code to trace bugs and apply fixes throughout the project. It correctly identified that `secret = str(st.session_state.secret)` on even attempts caused alphabetical comparison, which I verified by checking that `"98" > "47"` is `True` in Python because `"9" > "4"`. The misleading part was the `try/except TypeError` block in `check_guess` -- it looked like a safety net but was actually what made the string comparison bug produce wrong answers quietly.

---

## 3. Debugging and testing your fixes

I wrote 25 pytest tests covering all the logic functions -- one that stood out was `test_bug1_string_comparison_would_fail`, which checks that `check_guess(100, 47)` returns `"Too High"` instead of `"Too Low"` (what string comparison would return since `"1" < "4"`). Claude helped me think through what the wrong answer would have been, not just what the right answer should be.

---

## 4. What did you learn about Streamlit and state?

Streamlit reruns the entire script on every user interaction, so a bare `random.randint()` at the top level gets a new value every time the user clicks anything. The fix was wrapping the secret in `if "secret" not in st.session_state` so it only generates once, and also checking the difficulty so it resets when the player switches modes.

---

## 5. Looking ahead: your developer habits

Writing a bug report while debugging made it much easier to write tests later, because I already had the exact failure case written down. Next time I work with AI on code, I want to run it and break it manually first -- bugs like the off-by-one on attempts only showed up by clicking around, not by reading the code.
