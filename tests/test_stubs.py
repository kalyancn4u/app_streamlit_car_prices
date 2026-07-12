"""Guided test stubs — a ladder from complete novice to mastery. 🧗

HOW TO USE
    1. Pick a stub (start at Level 1).
    2. Delete its `@pytest.mark.skip(...)` line.
    3. Replace `pytest.fail(...)` with real `assert` statements (the docstring says what).
    4. Run `pytest -v` until it's green, then climb to the next level.

    pytest -v          # test_smoke.py passes; these stubs show as SKIPPED

Reference patterns are in tests/test_smoke.py. See docs/TESTING_GUIDE.md for the "why".
Difficulty: 🟢 novice · 🟡 pure functions · 🟠 edge cases · 🔴 integration · 🟣 mastery.

NOTE: the Streamlit apps (app.py / app_v1.py) can't be imported in a test (importing
them tries to draw the UI), so we test `train_model.py` and the saved model. A couple of
the mastery stubs ask you to *refactor* a helper out of the app so it becomes testable —
that skill (making code testable) is half of real-world testing.
"""

import pytest

import train_model

TODO = "stub — delete this @skip, then implement (see docstring)"


# ── Level 1 · 🟢 First steps ────────────────────────────────────────────────
@pytest.mark.skip(reason=TODO)
def test_flag_features_include_the_baselines_siblings():
    """`train_model.CONFIG['flag_features']` lists the one-hot flags. Assert it contains
    'Petrol', 'Manual' and 'Seats_5' (the non-baseline levels the app can set)."""
    pytest.fail("TODO")


# ── Level 2 · 🟡 Pure functions ─────────────────────────────────────────────
@pytest.mark.skip(reason=TODO)
def test_make_price_ranges_returns_three_bands_and_four_edges():
    """`train_model.make_price_ranges(df)` returns `(df_with_band, range_config)`.
    Build a small df with a `selling_price` column, call it, and assert `range_config`
    has labels ['Low','Medium','High'] and 4 `bin_edges`, with `price_unit == 'Lakhs'`."""
    pytest.fail("TODO")


@pytest.mark.skip(reason=TODO)
def test_numeric_input_specs_min_below_max():
    """`train_model.numeric_input_specs(df)` gives slider bounds per numeric feature.
    Assert every feature's `min` is <= its `default` <= its `max`."""
    pytest.fail("TODO")


# ── Level 3 · 🟠 Edge cases ─────────────────────────────────────────────────
@pytest.mark.skip(reason=TODO)
def test_clean_renames_the_seat_columns():
    """The raw CSV has columns literally named '5' and '>5'. `clean_dataset` renames them
    to 'Seats_5' / 'Seats_Above_5'. Build a tiny df with those columns and assert the
    rename happened (and no row was dropped for a valid price)."""
    pytest.fail("TODO")


# ── Level 4 · 🔴 Integration (the saved model) ──────────────────────────────
@pytest.mark.skip(reason=TODO)
def test_two_models_agree_on_band_direction():
    """Load BOTH saved models (price_model.pkl + range_model.pkl) and feature_columns.json.
    For a cheap car (e.g. a Maruti Alto) assert the classifier's band is not 'High' and the
    regressor's price is small — i.e. the two models tell a consistent story.
    (Copy the row-building pattern from tests/test_smoke.py.)"""
    pytest.fail("TODO")


# ── Level 5 · 🟣 Mastery ────────────────────────────────────────────────────
@pytest.mark.parametrize("make,model,floor", [
    ("MARUTI", "SWIFT VXI", 1.0),
    ("BMW", "X5", 8.0),
])
@pytest.mark.skip(reason=TODO)
def test_saved_model_prices_exceed_floor(make, model, floor):
    """Parametrized: build a feature row for each car (as in test_smoke.py) and assert the
    predicted price exceeds `floor`. One test body, many cases."""
    pytest.fail("TODO")


@pytest.mark.skip(reason=TODO)
def test_refactor_make_format_lakhs_testable():
    """MASTERY / refactor exercise. `format_lakhs()` lives inside app_v1.py, which can't be
    imported in a test. Move it (and `rupees()` from app.py) into a new importable module,
    e.g. `formatting.py`, have the apps import it, then here assert:
        format_lakhs(4.75)  -> '₹4.75 Lakhs'   (NOT '₹5')
        format_lakhs(145)   -> '₹1.45 Cr'
        format_lakhs(0.45)  -> '₹45,000'
    Making code testable *is* the exercise."""
    pytest.fail("TODO")


# ── 🐞 Debugging drill — regression for a REAL past bug ─────────────────────
@pytest.mark.skip(reason=TODO)
def test_regression_price_is_treated_as_lakhs_not_raw_rupees():
    """History (docs/DESIGN_NOTES.md): the original app treated a model output of 4.75
    (= ₹4.75 Lakhs) as raw rupees and printed '₹5'. Turn that bug into a guard: assert the
    dataset's `selling_price` values are small Lakhs-scale numbers (say, median < 100), so
    any code that divides them by 100,000 would obviously be wrong. This is how a fixed bug
    becomes a permanent tripwire."""
    pytest.fail("TODO")
