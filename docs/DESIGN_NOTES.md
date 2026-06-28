# 🛠️ Design Notes & Rationale

This document explains **what was wrong with the original code**, **why it broke**,
and **how the rewrite fixes it**. The user-facing instructions live in
[`README.md`](../README.md); this file is the engineering rationale.

> TL;DR — The models were always correct, but the app **misread their units**
> (it treated prices that were in *Lakhs* as if they were in *raw rupees*),
> **hid 60 % of the dataset's categories** behind a hard-coded form, and shipped
> **187 MB of over-grown model files**. The rewrite makes the whole app
> **data-driven from a single metadata contract**, fixes the units, and shrinks
> the models ~12×.

---

## 1. What the user reported

> "The UI is not as per expectations and the code is not running as expected."

Both symptoms trace back to concrete defects, not vague polish issues. Here they are.

---

## 2. Root-cause analysis (the discrepancies)

### 🔴 Bug 1 — Price unit mismatch (this is *the* "not running as expected" bug)

The dataset's `selling_price` column is expressed in **Lakhs of Rupees**:

```
selling_price = 1.2   ->  ₹1.2 Lakhs  (₹120,000)
selling_price = 5.5   ->  ₹5.5 Lakhs  (₹550,000)
```

…but the original `app.py` treated the predicted number as **raw rupees**:

```python
# Original format_price() thresholds
'price_crore_threshold': 10_000_000,   # 1 crore in rupees
'price_lakh_threshold':     100_000,   # 1 lakh in rupees
```

So a model output of `4.75` (i.e. **₹4.75 Lakhs**) fell below the lakh threshold and
was printed as **`₹5`**. Worse, the range interval divided the *already-in-Lakhs*
bin edges by 100,000:

```python
lower_lakhs = edges[idx] / 100000     # 3.99 / 100000  ->  0.00004
# result: "₹0.0 Lakhs – ₹0.0 Lakhs"   ← always zero
```

**Every prediction was therefore wrong on screen**, even though the underlying
model was fine.

| Model output | Original UI showed | Correct value |
| :----------- | :----------------- | :------------ |
| `4.75`       | `₹5`               | **₹4.75 Lakhs** |
| range `Medium` | `₹0.0 – ₹0.0 Lakhs` | **₹3.99 – ₹6.75 Lakhs** |

**Fix:** prices are treated as Lakhs **end-to-end**. `format_lakhs()` converts to
Crore / Lakh / rupee notation, and the bin edges (already in Lakhs) are used
directly. `range_config.json` now also carries an explicit `"price_unit": "Lakhs"`
so the contract is self-documenting.

### 🔴 Bug 2 — Missing categorical options (the encoding baselines)

The categorical columns in the CSV are one-hot encoded **with a dropped baseline**
(standard practice to avoid the dummy-variable trap). Counting the data:

| Group | Columns present | Dropped baseline | Baseline share |
| :---- | :-------------- | :--------------- | :------------- |
| Seller | `Individual`, `Trustmark Dealer` | **Dealer** | **60 %** |
| Fuel | `Petrol`, `Diesel`, `Electric`, `LPG` | **CNG / Other** | ~1.6 % |
| Transmission | `Manual` | **Automatic** | ~20 % |
| Seats | `5`, `>5` | **Fewer than 5** | ~1.2 % |

The original form only offered `['Individual', 'Trustmark Dealer']` for seller —
so the **single most common category (Dealer, 60 % of cars) was impossible to
select**, and there was no way to represent a CNG car. Picking "Individual" when
the car is actually dealer-sold silently biased every prediction.

**Fix:** the app now exposes **all** options, with the baseline rendered as an
ordinary choice that simply sets *no* flag (e.g. `Dealer → []`, `CNG → []`). The
mapping lives in one place (`SELLER_FLAGS`, `FUEL_FLAGS`, …) and is documented.

### 🔴 Bug 3 — 187 MB of model files

The original Random Forests had **unbounded depth** over **~3,200 one-hot `model`
columns**, producing:

```
price_model.pkl   122 MB
range_model.pkl    65 MB
```

That makes the app slow to start (joblib has to deserialize 122 MB on first load,
which can look like a hang) and bloats the repo.

**Fix:** bound the trees (`max_depth=18`, `min_samples_leaf=4`) and compress the
pickles. This regularisation *also improves generalisation*:

| File | Before | After | Change |
| :--- | -----: | ----: | :----- |
| `price_model.pkl` | 122 MB | **13.5 MB** | −89 % |
| `range_model.pkl` | 65 MB | **1.0 MB** | −98 % |

### 🟠 Bug 4 — Free-text model box (poor UX & silent wrong answers)

There are **3,233 distinct models**. A free-text box meant typos were common, and
because the encoder uses `handle_unknown='ignore'`, an unrecognised model name was
**silently encoded as all-zeros** — the user got a confident-looking prediction
that ignored their (mistyped) model entirely.

**Fix:** a **cascading Make → Model dropdown**. Selecting a brand filters the model
list to that brand's real variants, so every input is valid by construction.

### 🟡 Bug 5 — README inconsistencies

The README's Quick Start said training "generates `model.joblib` and
`encoders.json`", and Troubleshooting referenced a missing `model.joblib` — **none
of which the project ever produced** (it produces `price_model.pkl`,
`range_model.pkl`, and two JSON files). These references were corrected and the
project structure updated to include `metadata.json`.

---

## 3. The redesign

### Architecture: one metadata contract

The biggest structural change is that **`train_model.py` now emits a
`metadata.json`** that fully describes the UI, and **`app.py` is driven entirely
by it**. The form can no longer drift out of sync with the model.

```
            train_model.py                         app.py
  ┌───────────────────────────────┐      ┌──────────────────────────┐
  │ data/cars24-…-cleaned-new.csv │      │  loads 5 artifacts       │
  │            │                  │      │                          │
  │   clean → bin → fit RF×2      │      │  metadata.json ─┐        │
  │            │                  │      │   • makes→models │ builds │
  │   writes:  ▼                  │ ───► │   • slider ranges├─►form  │
  │   price_model.pkl             │      │   • categories   │        │
  │   range_model.pkl             │      │  range_config ──┘        │
  │   feature_columns.json        │      │   • bin edges + UNIT      │
  │   range_config.json (+unit)   │      │  price_model → ₹ exact    │
  │   metadata.json  ◄── NEW      │      │  range_model → Low/Med/Hi │
  └───────────────────────────────┘      └──────────────────────────┘
```

`metadata.json` contains:

* `makes_models` — `{ "MARUTI": ["SWIFT VXI", …], … }` for the cascading dropdown.
* `model_options` / `make_options` — the valid fuel / transmission / seats per
  model (and per make, as a fallback), so the dependent dropdowns can only ever
  offer real combinations. See **§6** and
  [INPUT_VALIDATION_GUIDE.md](INPUT_VALIDATION_GUIDE.md).
* `model_specs` / `make_specs` — median engine / power / mileage per model, for
  the simple app's auto-fill (see §5).
* `numeric_features` — outlier-robust slider bounds (1st–99th percentile),
  sensible step and default (median) per feature, plus dtype.
* `categorical_features` — the option lists **including the baselines** (used as
  the final fallback).
* `metrics` — R², MAE and accuracy, surfaced live in the sidebar.

A welcome side-effect: **the app no longer needs the 1.5 MB CSV at runtime** — it
is only required for (re)training.

### Modelling decisions

* **Two models, as per the README** — a `RandomForestRegressor` for the exact price
  and a `RandomForestClassifier` for the Low/Medium/High band.
* **Tercile bands** (33rd/67th percentile) keep the three classes balanced
  (~33 % each), which is why the classifier uses `class_weight="balanced"`.
* **Bounded trees** for size and generalisation (see Bug 3).
* Reported with **MAE in Lakhs** (≈ ₹0.71 L) alongside R² because "average error
  of ₹71,000" is far more intuitive to a car buyer than an R² value.

### UI/UX decisions

* **Wide, sectioned single-page layout** (`1 · Vehicle`, `2 · Specifications`)
  inside bordered cards instead of cramming everything into the sidebar.
* **Sidebar repurposed** for an "About" blurb and **live model-quality metrics**.
* **Result cards** for the exact price and the band, plus a **three-band gauge**
  with a marker (`🔻`) showing exactly where the estimate sits on the price scale.
  The classifier's band is highlighted; the marker comes from the regressor.
* All money rendered with `format_lakhs()` so ₹, Lakh and Crore are consistent
  everywhere (the sidebar MAE, the cards, the gauge labels).

---

## 4. Verified results

Trained on **19,820 cars / 41 brands** (held-out 20 % test set):

| Metric | Value |
| :----- | :---- |
| Price R² | **0.950** |
| Price MAE | **₹0.71 Lakhs** |
| Band accuracy | **76.9 %** |

Spot-checks (exact predictions from the saved model):

| Car | Prediction | Band |
| :-- | :--------- | :--- |
| Maruti Swift VXI · Petrol · Individual | ₹5.24 Lakhs | Medium |
| Hyundai Creta · Diesel · Automatic · Dealer | ₹11.35 Lakhs | High |
| BMW X5 · Diesel · Automatic | ₹20.80 Lakhs | High |
| Maruti Wagon R · **CNG** · Individual | ₹3.35 Lakhs | Low |

The CNG and Dealer cases confirm the baseline categories now work.

---

## 5. Simple edition — `app_v2.py`

A second front-end built for **demos to complete beginners**: *simplicity is the
ultimate sophistication*. Same trained models, a radically smaller surface.

**What was removed** (vs `app.py`): the custom CSS, gradient hero, result cards,
the gauge, the sidebar, expanders and the debug table — i.e. everything ornate.
Only plain Streamlit widgets remain (`selectbox`, `slider`, `radio`, `metric`).
There is also **no "Predict" button**: the estimate updates **live** as inputs
change, which is both simpler and more engaging to watch.

**What was hidden** — a novice can't answer "engine cc" or "max power bhp", so the
form asks only six intuitive questions (brand, model, fuel, gearbox, age, km).

**The key decision — auto-filling the hidden specs.** Engine and power are *strong*
price predictors, so they can't just be dropped. Filling them with one **global
median** collapses premium cars toward the average — a measured failure:

| Car | global-median fill | per-model fill | actual |
| :-- | -----------------: | -------------: | -----: |
| BMW X5 | ₹8.2 L ❌ | **₹20.7 L** ✅ | ₹20.8 L |
| Toyota Fortuner | ₹7.7 L ❌ | **₹18.5 L** ✅ | ₹20.0 L |

So `train_model.py` now records **per-model (and per-make) median specs** in
`metadata.json` (`model_specs` / `make_specs`), and `app_v2.py` auto-fills from the
*chosen model's* typical values — "you picked the model, so we know its specs."
Lookup falls back per-model → per-make → global. The form stays trivially simple
while predictions stay accurate across the whole price range.

Run it with: `streamlit run app_v2.py`.

---

## 6. Preventing invalid inputs (the validated-data approach)

The data is clean and finite, so rather than *validating* user input we make
invalid input **unrepresentable** — the form only ever offers values that exist
in the data. The full, beginner-oriented write-up is in
[INPUT_VALIDATION_GUIDE.md](INPUT_VALIDATION_GUIDE.md); the engineering summary:

* **Intrinsic vs circumstantial inputs.** Attributes that belong to the *car*
  (fuel, transmission, seats, engine, power, mileage) are derived from the chosen
  **model**; attributes about the *sale* (seller, age, km) stay free within data
  bounds. A `SWIFT VDI` is always diesel; any car can be 5 years old.
* **Dependent dropdowns.** `model_options[make][model]` lists the fuel /
  transmission / seats actually seen for that model. The full app limits those
  dropdowns to it; the simple app auto-selects `[0]` and shows it read-only.
  Result: combinations like "Electric Alto" cannot be entered. 3,231 / 3,233
  models have a single valid fuel and gearbox anyway (the variant name encodes
  them), so this is mostly *automatic selection*, not a choice.
* **No stale state.** The cascading widgets (`model`, `fuel`, …) are intentionally
  given **no `key=`**, so each rerun rebuilds them from the current parent
  selection. Changing the brand can't leave a mismatched "Maruti X5" behind —
  data only flows downhill (make → model → fuel/gearbox/seats).
* **Single source of truth.** All these lists come from `metadata.json`, written
  by `train_model.py`, so the form can never drift from what the model was
  trained on. Retraining refreshes the form automatically.

## 7. Known limitations / future work

* **Band accuracy (~77 %)** is capped by the arbitrary tercile boundaries — cars
  near a boundary are genuinely ambiguous. One could instead **derive the band
  from the (very accurate) predicted price** to guarantee the band and the rupee
  figure never disagree; this rewrite keeps the separate classifier to honour the
  README's stated design.
* Slider bounds are clipped to the 1st–99th percentile, so extreme inputs (e.g. a
  brand-new car with <3 years age) can't be entered. Widen the percentiles in
  `train_model.py` if needed.
* `model` cardinality is high (~3,200). Target/frequency encoding would shrink the
  artifacts further and likely help the rarer models, at the cost of a more complex
  pipeline.
