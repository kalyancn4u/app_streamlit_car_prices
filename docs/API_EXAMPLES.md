# 📗 API Examples — the training pipeline & model by example

The Streamlit apps (`app.py`, `app_v1.py`) are *user interfaces* and aren't imported
directly. The reusable, testable API is in **`train_model.py`** plus the **saved model**
under `models/`. Recipes with expected output below; a runnable version is in
[`notebooks/api_examples.ipynb`](../notebooks/api_examples.ipynb).

Setup once:

```bash
pip install -r requirements.txt
```

---

## The training pipeline (`train_model.py`)

```python
import train_model

train_model.CONFIG["price_unit"]        # 'Lakhs'  (prices are in Lakhs, not raw rupees)
train_model.CONFIG["range_labels"]      # ['Low', 'Medium', 'High']
```

Clean a DataFrame (drops bad rows, uppercases make/model, renames seat columns):

```python
import pandas as pd
df = pd.DataFrame({"selling_price": [5.0, -1.0],
                   "make": [" maruti ", "x"], "model": ["swift vxi", "y"]})
out = train_model.clean_dataset(df)
out["make"].tolist()                    # ['MARUTI']   (the -1 price row is dropped)
```

Derive the price bands and the slider bounds:

```python
full = train_model.clean_dataset(train_model.load_dataset())
binned, range_config = train_model.make_price_ranges(full)
range_config["bin_edges"]               # 4 tercile edges, e.g. [0.3, 3.99, 6.75, 20.9]
specs = train_model.numeric_input_specs(full)
specs["age"]                            # {'min': .., 'max': .., 'default': .., 'step': 1, 'dtype': 'int'}
```

Run the whole training pipeline (writes the five artifacts into `models/`):

```python
train_model.main()                      # load -> clean -> bin -> fit RF x2 -> evaluate -> save
```

## Using the saved model to predict

```python
import json, joblib, pandas as pd
from pathlib import Path

MODELS = Path(train_model.__file__).parent / "models"        # cwd-independent
model = joblib.load(MODELS / "price_model.pkl")
cols = json.loads((MODELS / "feature_columns.json").read_text())

row = {c: 0 for c in cols}
row.update({"km_driven": 40000, "mileage": 20.0, "engine": 1200, "max_power": 82.0,
            "age": 5, "make": "MARUTI", "model": "SWIFT VXI",
            "Petrol": 1, "Manual": 1, "Seats_5": 1})       # baselines = leave flags at 0

price = float(model.predict(pd.DataFrame([row])[cols])[0])
print(f"₹{price:.2f} Lakhs")            # e.g. ₹5.24 Lakhs   (a few Lakhs, NOT ₹500000)
```

> The price is in **Lakhs** — a Swift lands around a few Lakhs. (This is the exact unit that
> the original app got wrong; see `docs/DESIGN_NOTES.md`.)

## Formatting money the Indian way

`format_lakhs()` (in `app_v1.py`) and `rupees()` (in `app.py`) turn a Lakhs value into
₹ / Lakh / Crore text. Because they live inside the Streamlit scripts they can't be imported
directly — extracting them into a small `formatting.py` module is a great exercise (see the
mastery stub in [`tests/test_stubs.py`](../tests/test_stubs.py)). The logic:

```text
4.75  -> '₹4.75 Lakhs'      (>= 1 Lakh)
145   -> '₹1.45 Crore'      (>= 100 Lakhs)
0.45  -> '₹45,000'          (< 1 Lakh -> raw rupees)
```
