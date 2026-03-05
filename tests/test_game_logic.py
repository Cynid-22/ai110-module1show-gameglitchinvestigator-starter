from logic_utils import check_guess, parse_guess, get_range_for_difficulty, update_score


# ---------------------------------------------------------------------------
# Bug 1 & 2 — check_guess: string comparison + swapped hint messages
# ---------------------------------------------------------------------------

def test_winning_guess():
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"

def test_bug1_numeric_comparison_not_string():
    # Bug 1: secret was cast to str on even attempts, causing "9" > "47" = True alphabetically
    # With secret=47, guess=98 should be "Too High" (numeric), not "Too Low" (string)
    outcome, _ = check_guess(98, 47)
    assert outcome == "Too High"

def test_bug1_string_comparison_would_fail():
    # "100" < "47" alphabetically ("1" < "4"), so string compare would say "Too Low"
    # Correct numeric compare: 100 > 47 → "Too High"
    outcome, _ = check_guess(100, 47)
    assert outcome == "Too High"

def test_bug2_too_high_message_says_go_lower():
    # Bug 2: "Go HIGHER!" and "Go LOWER!" were swapped
    _, message = check_guess(60, 50)
    assert "LOWER" in message

def test_bug2_too_low_message_says_go_higher():
    _, message = check_guess(40, 50)
    assert "HIGHER" in message

def test_bug2_win_message_correct():
    _, message = check_guess(50, 50)
    assert "Correct" in message


# ---------------------------------------------------------------------------
# Bug 6 — parse_guess: decimal inputs silently accepted
# ---------------------------------------------------------------------------

def test_bug6_decimal_rejected():
    # Bug 6: "1.5" was silently converted to int(1) instead of returning an error
    ok, value, err = parse_guess("1.5")
    assert ok is False
    assert value is None
    assert err is not None

def test_bug6_decimal_99_rejected():
    ok, value, err = parse_guess("9.9")
    assert ok is False

def test_valid_integer_accepted():
    ok, value, err = parse_guess("47")
    assert ok is True
    assert value == 47
    assert err is None

def test_empty_string_rejected():
    ok, value, err = parse_guess("")
    assert ok is False

def test_none_rejected():
    ok, value, err = parse_guess(None)
    assert ok is False

def test_non_numeric_rejected():
    ok, value, err = parse_guess("abc")
    assert ok is False

def test_negative_integer_accepted():
    # parse_guess only checks format, not bounds
    ok, value, err = parse_guess("-5")
    assert ok is True
    assert value == -5


# ---------------------------------------------------------------------------
# Bug 3 & 8 — get_range_for_difficulty: wrong ranges + Hard/Normal swapped
# ---------------------------------------------------------------------------

def test_easy_range():
    low, high = get_range_for_difficulty("Easy")
    assert low == 1
    assert high == 20

def test_bug8_normal_range_is_50_not_100():
    # Bug 8: Normal had 1-100 (should be 1-50), Hard had 1-50 (should be 1-100)
    low, high = get_range_for_difficulty("Normal")
    assert low == 1
    assert high == 50

def test_bug8_hard_range_is_100_not_50():
    low, high = get_range_for_difficulty("Hard")
    assert low == 1
    assert high == 100

def test_bug8_hard_range_larger_than_normal():
    # Hard must be harder (larger range) than Normal
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")
    assert hard_high > normal_high

def test_unknown_difficulty_defaults():
    low, high = get_range_for_difficulty("Unknown")
    assert low == 1
    assert high == 100


# ---------------------------------------------------------------------------
# Bug 5 — bounds validation (tested at logic level via parse_guess + range)
# ---------------------------------------------------------------------------

def test_bug5_negative_guess_out_of_easy_range():
    # parse_guess passes -1 through, but it should fail bounds check
    ok, value, _ = parse_guess("-1")
    assert ok is True  # parse_guess allows it
    low, high = get_range_for_difficulty("Easy")
    assert value < low  # caller must reject it

def test_bug5_guess_above_easy_range():
    ok, value, _ = parse_guess("21")
    assert ok is True
    low, high = get_range_for_difficulty("Easy")
    assert value > high  # caller must reject it


# ---------------------------------------------------------------------------
# update_score — general correctness
# ---------------------------------------------------------------------------

def test_win_score_increases():
    new_score = update_score(0, "Win", 1)
    assert new_score > 0

def test_too_low_score_decreases():
    new_score = update_score(100, "Too Low", 1)
    assert new_score < 100

def test_win_minimum_points():
    # Even on late attempts, score should not drop below 10 points added
    new_score = update_score(0, "Win", 20)
    assert new_score >= 10
