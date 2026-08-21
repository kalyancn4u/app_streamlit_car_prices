"""Working reference tests — a green baseline + patterns to copy in test_stubs.py.

Run:  pytest -v      (from the repo root)

These import `train_model.py` (no Streamlit needed) and load the saved model.
"""

import json
from pathlib import Path

import pandas as pd

import train_model

MODELS = Path(__file__).resolve().parent.parent / "models"
_has_model = (MODELS / "price_model.pkl").exists()

import pytest
needs_model = pytest.mark.skipif(not _has_model, reason="run `python train_model.py` first")


def test_config_price_unit_is_lakhs():
    # The single most important fact about this dataset: prices are in Lakhs.
    """Guards the core dataset fact: prices are in Lakhs and bands are Low/Medium/High."""
    assert train_model.CONFIG["price_unit"] == "Lakhs"
    assert train_model.CONFIG["range_labels"] == ["Low", "Medium", "High"]


def test_clean_drops_nonpositive_and_uppercases():
    """clean_dataset drops non-positive prices and trims + uppercases make/model."""
    df = pd.DataFrame({"selling_price": [5.0, -1.0, 0.0],
                       "make": [" maruti ", "x", "y"],
                       "model": ["swift vxi", "a", "b"]})
    out = train_model.clean_dataset(df)
    assert out["selling_price"].tolist() == [5.0]        # bad prices dropped
    assert out["make"].tolist() == ["MARUTI"]            # trimmed + uppercased
    assert out["model"].tolist() == ["SWIFT VXI"]


@needs_model
def test_saved_model_predicts_a_swift_in_lakhs():
    """Regression guard for the old 'shows ₹5 instead of ₹4.75 Lakhs' unit bug:
    the model's output is in *Lakhs*, so a Swift must land in a few-Lakhs range
    (~1–50), NOT hundreds of thousands."""
    import joblib
    model = joblib.load(MODELS / "price_model.pkl")
    cols = json.loads((MODELS / "feature_columns.json").read_text())
    row = {c: 0 for c in cols}
    row.update({"km_driven": 40000, "mileage": 20.0, "engine": 1200,
                "max_power": 82.0, "age": 5, "make": "MARUTI", "model": "SWIFT VXI",
                "Petrol": 1, "Manual": 1, "Seats_5": 1})
    price = float(model.predict(pd.DataFrame([row])[cols])[0])
    assert 1 < price < 50, f"price {price} is not in a sane Lakhs range"
