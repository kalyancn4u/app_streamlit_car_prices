# 🚗 Car Price & Range Predictor

> A machine-learning web app that estimates what a **used car is worth in Indian
> Rupees (₹)** — both an **exact price** *and* a **budget band** (Low / Medium /
> High) — from a handful of easy questions about the car.

Built with [Streamlit](https://streamlit.io) and
[scikit-learn](https://scikit-learn.org), trained on **19,820 real Cars24
listings** across **41 brands** and **3,233 models**.

```
   You tell it:                          It tells you:
   ┌─────────────────────┐               ┌──────────────────────────────┐
   │ 🏷️  Maruti          │               │ 💰  ₹5.24 Lakhs              │
   │ 🚙  Swift VXI        │   ───────►    │ 🎯  Medium-budget car        │
   │ 📅  5 years old      │   predicts    │      (similar cars sell for  │
   │ 🛣️  45,000 km        │               │       ₹3.99 – ₹6.75 Lakhs)   │
   └─────────────────────┘               └──────────────────────────────┘
```

---

## 📑 Table of Contents

1. [What This Project Does](#-what-this-project-does)
2. [Highlights (What Makes It Good)](#-highlights-what-makes-it-good)
3. [Two Editions: Full vs Simple](#-two-editions-full-vs-simple)
4. [Quick Start](#-quick-start)
5. [Using the App](#-using-the-app)
6. [How It Works (Architecture)](#-how-it-works-architecture)
7. [The Machine Learning](#-the-machine-learning)
   - [The dataset & features](#the-dataset--features)
   - [Two models, two questions](#two-models-two-questions)
   - [Why Random Forest? (DT vs RF vs XGBoost vs LightGBM)](#why-random-forest-dt-vs-rf-vs-xgboost-vs-lightgbm)
   - [Results](#results)
8. [Mistake-Proof Inputs by Design](#-mistake-proof-inputs-by-design)
9. [Project Structure & Every Artifact Explained](#-project-structure--every-artifact-explained)
10. [The Dataset File: CSV, Excel & Storage Formats](#-the-dataset-file-csv-excel--storage-formats)
11. [Companion Flask REST API](#-companion-flask-rest-api)
12. [Automation (CI / CD / CDD)](#-automation-ci--cd--cdd)
13. [Troubleshooting](#-troubleshooting)
14. [Tech Stack & Glossary for Newcomers](#-tech-stack--glossary-for-newcomers)
15. [Further Reading](#-further-reading)

---

## 🎯 What This Project Does

You give the app a few facts about a used car — brand, model, age, kilometres
driven — and it instantly returns **two** predictions:

| Output | What it is | Example |
| :----- | :--------- | :------ |
| **Exact price** | A single rupee figure, shown Indian-style in Lakhs / Crores | `₹5.24 Lakhs` |
| **Price band** | A budget bucket with its actual rupee interval | `Medium` → `₹3.99 – ₹6.75 Lakhs` |

The exact price comes from a **regression** model; the band comes from a
separate **classification** model. Both were trained together on the same
cleaned Cars24 dataset. Everything runs locally in your browser — no internet,
no API keys, no cloud account required.

> 💡 **New to any of these words?** There's a plain-English
> [glossary](#-tech-stack--glossary-for-newcomers) at the bottom. If you can
> read a recipe, you can follow this README.

---

## ✨ Highlights (What Makes It Good)

These are the design decisions that make the app accurate, trustworthy and
pleasant to use.

- **💷 True Indian-currency handling, end-to-end.** Prices live in **Lakhs**
  throughout — the model, the sliders, the result cards and the gauge all speak
  the same unit, and a single `format_lakhs()` helper renders every figure
  consistently as **₹ / Lakh / Crore** (1 Lakh = ₹100,000; 100 Lakhs = 1 Crore).
  A `"price_unit": "Lakhs"` field baked into the config makes the contract
  self-documenting.

- **🗂️ Complete category coverage.** Every real option is selectable —
  including the *most common* ones. The dataset one-hot-encodes categories with
  a **dropped baseline** (standard practice to avoid the "dummy-variable trap"),
  and the app faithfully reconstructs those baselines so that, for example,
  **Dealer** sellers (≈60 % of all cars) and **CNG** fuel are first-class
  choices rather than being hidden:

  | Group | Selectable options | Reconstructed baseline |
  | :---- | :----------------- | :--------------------- |
  | Seller | Individual, Trustmark Dealer | **Dealer** (≈60 %) |
  | Fuel | Petrol, Diesel, Electric, LPG | **CNG / Other** |
  | Transmission | Manual | **Automatic** |
  | Seats | 5, More than 5 | **Fewer than 5** |

- **🔗 Cascading, self-validating dropdowns.** Pick a **brand** → the **model**
  list narrows to that brand; pick a **model** → its **fuel, gearbox and seats**
  follow automatically. Impossible combinations such as "Electric Alto" or
  "Maruti X5" simply cannot be entered. (Full write-up:
  [Mistake-Proof Inputs](#-mistake-proof-inputs-by-design).)

- **📦 Compact, fast-loading models.** The forests are **regularised**
  (`max_depth=18`, `min_samples_leaf=4`) and the pickles are compressed — so the
  app starts quickly instead of stalling on a giant file, and the trees
  generalise better because they can't memorise noise.
  `price_model.pkl` ≈ **13.5 MB**, `range_model.pkl` ≈ **1 MB**.

- **🧭 One source of truth.** A generated `metadata.json` fully describes the UI
  — brand→model lists, slider ranges, valid options, per-model specs and live
  quality metrics. The form is built entirely from it, so **it can never drift
  out of sync with the trained model**, and it means the app doesn't even need
  the raw CSV at runtime.

- **📊 Honest, visible quality.** The full app surfaces the model's real
  accuracy (R², typical error, band accuracy) live in the sidebar, and shows a
  **three-band gauge** with a marker (`🔻`) placing the estimate on the price
  scale.

---

## 🖥️ Two Editions: Full vs Simple

The project ships **two front-ends** that share the *exact same trained models*.
Pick whichever fits your audience.

| | **Full edition** | **Simple edition** |
| :--- | :--- | :--- |
| **File** | `app_v1.py` | `app.py` *(default)* |
| **Run** | `streamlit run app_v1.py` | `streamlit run app.py` |
| **Best for** | Exploring every lever, demos to analysts | First-time users, quick demos, teaching |
| **Inputs** | All specs editable (fuel, gearbox, seats, engine, power, mileage, seller, age, km) | Just brand, model, age, km — the rest auto-filled |
| **Look** | Gradient hero, result cards, live sidebar metrics, band gauge, debug table | Plain Streamlit widgets only |
| **Predict** | Click **Estimate price** | **Live** — updates as you type, no button |
| **Philosophy** | *Power and transparency* | *Simplicity is the ultimate sophistication* |

> ℹ️ If you only remember one command, use **`streamlit run app.py`** (Simple);
> switch to **`streamlit run app_v1.py`** when you want the Full edition.

**How the Simple edition stays accurate with fewer questions:** a beginner
can't be expected to know a car's engine size (cc) or power (bhp), so those are
**auto-filled from the chosen model's own typical values** (its median engine,
power and mileage, recorded during training). Filling them with a single global
average would squash premium cars toward the mean — a measured failure — so the
fill is **per-model**:

| Car | If filled with a global average | Per-model fill (used) | Actual |
| :-- | ------------------------------: | --------------------: | -----: |
| BMW X5 | ₹8.2 L ❌ | **₹20.7 L** ✅ | ₹20.8 L |
| Toyota Fortuner | ₹7.7 L ❌ | **₹18.5 L** ✅ | ₹20.0 L |

---

## ⚡ Quick Start

### 1. Prerequisites

- **Python 3.9 or newer** — [download here](https://www.python.org/downloads/).

### 2. Open the project folder

```bash
cd path/to/app_streamlit_car_prices
```

### 3. Create a virtual environment *(recommended)*

A "virtual environment" is a private, throwaway copy of Python for this project,
so its libraries don't clash with anything else on your machine.

```bash
python -m venv venv
```

Activate it:

- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate.bat`
- **macOS / Linux:** `source venv/bin/activate`

<sub>Prefer Conda? `conda create -n car-price python=3.11 -y && conda activate car-price`</sub>

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

### 5. Train the models *(optional — pre-trained models ship with the repo)*

The trained models are **committed to the repo**, so you can skip straight to
step 6. Run this only if you want to retrain (e.g. on new data):

```bash
python train_model.py
```

This reads the dataset in `data/` and writes **five files** into `models/`:
`price_model.pkl`, `range_model.pkl`, `feature_columns.json`,
`range_config.json` and `metadata.json`. It takes ~1–2 minutes and prints the
accuracy it achieved.

### 6. Launch the app

```bash
streamlit run app.py        # Simple edition (recommended first run)
# or
streamlit run app_v1.py     # Full edition
```

Your browser opens automatically at **http://localhost:8501**. That's it. 🎉

---

## 🧭 Using the App

1. **Pick a Brand.** The **Model** dropdown instantly narrows to that brand.
2. **Pick a Model.** Its fuel, gearbox and seats are set automatically (Simple
   edition) or limited to that model's real options (Full edition).
3. **Set Age and Kilometres** with sliders that stop at sensible real-world
   limits. *(Full edition adds Engine, Power, Mileage and Seller.)*
4. **Read the result:** the **exact price** (₹ Lakhs/Crores) and the **budget
   band** with its rupee interval — plus a gauge showing where the estimate
   lands (Full edition).

In the Simple edition there is **no button** — the estimate updates live as you
change any input.

---

## 🏗️ How It Works (Architecture)

The whole design rests on **one idea**: the training script emits a single
`metadata.json` "contract" that fully describes the user interface, and the apps
are built *entirely* from that contract. The form therefore **can never
disagree** with the model it's paired with.

```
        train_model.py                              app.py / app_v1.py
  ┌──────────────────────────────┐          ┌───────────────────────────────┐
  │ data/cars24-…-cleaned.csv    │          │  loads 5 artifacts at start    │
  │            │                 │          │                                │
  │  clean → bin → fit RF × 2    │          │  metadata.json ──┐  builds the │
  │            │                 │  ──────► │   • brand→model   │  entire     │
  │  writes ▼                    │          │   • slider ranges ├─► form      │
  │   price_model.pkl            │          │   • valid options │             │
  │   range_model.pkl            │          │  range_config ────┘             │
  │   feature_columns.json       │          │   • band edges + UNIT           │
  │   range_config.json          │          │  price_model → ₹ exact price    │
  │   metadata.json              │          │  range_model → Low/Medium/High  │
  └──────────────────────────────┘          └───────────────────────────────┘
```

- **`train_model.py`** does all the heavy lifting once: load → clean → engineer
  features → fit both models → evaluate → save artifacts.
- **The apps** never touch the raw CSV. They load the five small artifacts,
  render the form from `metadata.json`, build a single feature row in the exact
  shape the model expects, and call `.predict()`.

Retrain on new data and the form updates itself automatically — no code changes.

---

## 🤖 The Machine Learning

### The dataset & features

The models learn from **19,820 cleaned Cars24 used-car listings** (41 brands,
3,233 distinct models). Each listing carries:

- **Numeric features:** `age`, `km_driven`, `mileage` (km/l), `engine` (cc),
  `max_power` (bhp).
- **Text features:** `make` and `model` — one-hot encoded inside the pipeline
  (`handle_unknown="ignore"`, so unseen values degrade gracefully).
- **Pre-encoded flags:** fuel, transmission, seller and seat-count, each stored
  with a dropped baseline (see [Highlights](#-highlights-what-makes-it-good)).
- **Target:** `selling_price`, expressed in **Lakhs of Rupees**.

Cleaning drops rows with missing/invalid prices, normalises the text columns to
uppercase, and trims the sliders to the 1st–99th percentile so one freak listing
can't stretch the controls.

### Two models, two questions

The app answers two different questions, so it trains two different models on
the **same features**:

| Model | Type | Answers | scikit-learn class |
| :---- | :--- | :------ | :----------------- |
| **Price model** | Regression | "*How many* Lakhs?" (a continuous number) | `RandomForestRegressor` |
| **Range model** | Classification | "*Which bucket* — Low, Medium or High?" | `RandomForestClassifier` |

The bands are cut at **terciles** (the 33rd and 67th percentiles of price), which
keeps the three classes roughly balanced (~⅓ each); the classifier additionally
uses `class_weight="balanced"` so no band dominates.

### Why Random Forest? (DT vs RF vs XGBoost vs LightGBM)

This is a **tabular** problem with a mix of numeric columns and thousands of
one-hot categorical columns — exactly the regime where **tree-based models**
dominate. But which tree model? Here's the honest comparison a data scientist
weighs.

**First, a 30-second intuition:**

- A **Decision Tree** is a flowchart of yes/no questions ("engine > 1500cc?
  → automatic? → …") ending in a price. Easy to read, but a *single* deep tree
  **memorises the training data** (high variance) and gives unstable predictions.
- A **Random Forest (RF)** grows *hundreds* of different trees on random subsets
  of the data and features, then **averages** them. The randomness de-correlates
  the trees, so their individual errors cancel out — much more accurate and
  stable than one tree, with almost no tuning.
- **Gradient boosting** (XGBoost, LightGBM, HistGradientBoosting) grows trees
  **one after another**, each new tree correcting the previous ones' mistakes.
  Often the most accurate family on tabular data — but more moving parts.

| Algorithm | How it learns | Accuracy on this data | Tuning effort | Model size / speed | Verdict here |
| :-------- | :------------ | :-------------------- | :------------ | :----------------- | :----------- |
| **Linear / Ridge regression** | One weighted sum of features | Poor — can't capture non-linear brand × age × engine interactions | Trivial | Tiny / fastest | ❌ Underfits |
| **Single Decision Tree** | One greedy flowchart | Mediocre — overfits, high variance, unstable | Low | Small / fast | ❌ Too fragile |
| **Random Forest** ⭐ | Bagging: average of many de-correlated trees | **Strong (R² ≈ 0.95)** out of the box | **Very low** | Larger / good | ✅ **Chosen** |
| **XGBoost (XGB)** | Sequential boosting + regularisation | Typically comparable-to-higher | Higher (learning rate, depth, rounds, early stopping) | Compact / fast | 🔜 Upgrade path |
| **LightGBM (LGBM)** | Leaf-wise boosting + histogram binning | Typically comparable-to-higher; shines on large / high-cardinality data | Higher; can overfit small data | Very compact / fastest | 🔜 Upgrade path |

**Why Random Forest was the right default:**

1. **Excellent accuracy with almost no tuning.** RF reaches **R² ≈ 0.95** here
   essentially out of the box. Boosting *can* edge higher, but only after
   careful tuning of the learning rate, tree depth, number of rounds and early
   stopping — RF is far more forgiving, which matters for a maintainable,
   reproducible project.
2. **Robust and hard to break.** Averaging many trees makes RF naturally
   resistant to outliers and noise, and it **won't silently overfit** the way a
   single tree — or an under-regularised booster — can.
3. **No feature scaling, handles mixed types.** Trees split on raw thresholds,
   so numeric and one-hot columns coexist with zero preprocessing beyond the
   encoding. Both models share one `ColumnTransformer` pipeline.
4. **Ships with scikit-learn.** Zero extra dependencies — `pip install
   scikit-learn` and you're done. XGBoost and LightGBM are separate libraries.
5. **Two-in-one.** The same algorithm serves both the regressor *and* the
   classifier, keeping the codebase and the mental model small.

**When you'd reach for boosting instead** — and it's a genuinely good upgrade
path: gradient boosting (especially **LightGBM** or scikit-learn's built-in
`HistGradientBoosting`) usually produces **smaller, faster models** and can
squeeze out a bit more accuracy, because it needs fewer, shallower trees. The
trade-offs are more hyper-parameters to tune, a higher risk of overfitting
without early stopping, and (for XGB/LGBM) an extra dependency. For a project
whose priorities are **robustness, reproducibility and a clean dependency
footprint**, Random Forest is the sweet spot; boosting is the documented next
step if the model artifacts ever need to shrink further or the accuracy frontier
matters more than tuning simplicity.

> 🧠 **Why bounded trees?** The forests are deliberately capped at
> `max_depth=18` and `min_samples_leaf=4`. With ~3,200 one-hot `model` columns,
> unbounded trees would both **overfit** and **balloon the saved files**.
> Bounding them keeps accuracy high *and* keeps the pickles small and
> fast-loading — regularisation that pays off twice.

### Results

Trained on 19,820 cars with a held-out **20 % test set**:

| Metric | Value | In plain words |
| :----- | :---- | :------------- |
| **Price R²** | **0.950** | Explains 95 % of the variation in price |
| **Price MAE** | **₹0.71 Lakhs** | Typical miss is ≈ ₹71,000 — intuitive for a buyer |
| **Band accuracy** | **76.9 %** | Correct Low/Medium/High bucket ~3 times in 4 |

Real predictions from the saved model (spot-checks across the price range):

| Car | Prediction | Band |
| :-- | :--------- | :--- |
| Maruti Swift VXI · Petrol · Individual | ₹5.24 Lakhs | Medium |
| Hyundai Creta · Diesel · Automatic · Dealer | ₹11.35 Lakhs | High |
| BMW X5 · Diesel · Automatic | ₹20.80 Lakhs | High |
| Maruti Wagon R · **CNG** · Individual | ₹3.35 Lakhs | Low |

> The CNG and Dealer examples confirm the reconstructed baseline categories work
> correctly across the whole price range.

**Known limits & future work:** band accuracy (~77 %) is capped by the arbitrary
tercile boundaries — cars near a boundary are genuinely ambiguous. Slider bounds
are clipped to the 1st–99th percentile, so extreme inputs can't be entered. The
high-cardinality `model` column is a natural target for frequency/target
encoding or a switch to boosting, both of which would shrink the artifacts
further.

---

## 🛡️ Mistake-Proof Inputs by Design

Rather than *checking* input after the fact, the app makes invalid input
**impossible to enter in the first place** — the "make invalid states
unrepresentable" principle. Because the training data is clean and finite, the
form only ever offers values that genuinely exist.

- **You choose, you never type.** Every input is a dropdown, slider or radio —
  no free-text box to mistype ("Marutee", "Petrl").
- **Brand → Model → Fuel/Gearbox/Seats cascade.** Data only ever flows downhill,
  so an upstream change refreshes everything below it. There are no stale
  leftovers like "Maruti X5". (In fact **3,231 of 3,233** models have exactly one
  valid fuel and gearbox — the variant name encodes them — so this is mostly
  *automatic selection*, not a question.)
- **Sliders can't exceed real-world limits.** Bounds come from the actual spread
  of 19,820 cars (trimmed to the 1st–99th percentile).
- **Technical specs are auto-filled** (Simple edition) from the chosen model's
  typical values, so you can't enter a *wrong* engine size if you never enter
  one.

📖 The full beginner-friendly walkthrough — with the "five locks" and a
field-by-field safety table — is in
[docs/INPUT_VALIDATION_GUIDE.md](docs/INPUT_VALIDATION_GUIDE.md).

---

## 📁 Project Structure & Every Artifact Explained

```
app_streamlit_car_prices/
├── app.py                     # ▶ Simple edition (default) — live, beginner-friendly
├── app_v1.py                  # ▶ Full edition — rich UI, all inputs editable
├── train_model.py             # ⚙ Training pipeline — builds all model artifacts
├── requirements.txt           # 📦 Python dependencies
├── README.md                  # 📄 This file
├── .gitignore                 # 🚫 Ignored files (caches, virtualenvs, secrets)
│
├── data/
│   └── cars24-car-price-cleaned-new.csv   # 🗃 Dataset (only needed for training)
│
├── models/                    # 🧠 Generated by train_model.py (run it once)
│   ├── price_model.pkl        #   Regression model  → exact price (Lakhs)
│   ├── range_model.pkl        #   Classification model → Low / Medium / High
│   ├── feature_columns.json   #   Model input schema (exact column order)
│   ├── range_config.json      #   Band edges, labels & price unit
│   └── metadata.json          #   Drives the UI: brand→model, ranges, options, metrics
│
├── docs/                      # 📚 Deep-dive guides (see Further Reading)
│   ├── DESIGN_NOTES.md        #   Engineering rationale & design decisions
│   ├── INPUT_VALIDATION_GUIDE.md   # How wrong inputs are made impossible
│   └── CI_CD_GITHUB_ACTIONS.md     # Automating test/deploy/retrain
│
└── .claude/launch.json        # ▶ Preview-tool launch config (ports 8503 / 8504)
```

> 🐳 A companion **Flask REST API** version of this predictor lives in its own
> separate repository (see the [next section](#-companion-flask-rest-api)).

### The code files

| File | What it is | How you use it |
| :--- | :--------- | :------------- |
| **`train_model.py`** | The training pipeline: loads & cleans the CSV, engineers features, fits both Random Forests, evaluates them, and writes the five artifacts. Self-documenting `CONFIG` block at the top. | `python train_model.py` — run once, and again whenever the data changes. |
| **`app.py`** | The **Simple edition** front-end. Six intuitive questions, live-updating estimate, plain widgets. | `streamlit run app.py` |
| **`app_v1.py`** | The **Full edition** front-end. Every input editable, styled cards, sidebar quality metrics, three-band gauge, debug table. | `streamlit run app_v1.py` |
| **`requirements.txt`** | Pins the five libraries the app needs: `joblib`, `numpy`, `pandas`, `scikit-learn`, `streamlit`. | `pip install -r requirements.txt` |

### The generated model artifacts (in `models/`)

You never edit these by hand — `train_model.py` regenerates them. All five
artifacts (including the two `.pkl` models, ~14.5 MB total) are committed to the
repo, so a **fresh clone runs immediately** without a training step. Delete them
and rerun `python train_model.py` anytime to rebuild.

| Artifact | Format | Contains | Consumed by |
| :------- | :----- | :------- | :---------- |
| `price_model.pkl` | joblib pickle (~13.5 MB) | Fitted `RandomForestRegressor` pipeline | Both apps → exact price |
| `range_model.pkl` | joblib pickle (~1 MB) | Fitted `RandomForestClassifier` pipeline | Both apps → Low/Medium/High |
| `feature_columns.json` | JSON | Ordered list of feature names (the input schema) | Both apps → to build the feature row in the right order |
| `range_config.json` | JSON | Band `labels`, `bin_edges`, and `price_unit` | Both apps → to label bands & format money |
| `metadata.json` | JSON (~1 MB) | brand→model lists, slider ranges, valid options, per-model specs, and live metrics | Both apps → to render the entire form |

### Supporting files

| File / folder | Purpose |
| :------------ | :------ |
| `data/…cleaned-new.csv` | The raw dataset. Needed **only** for (re)training — the running app doesn't read it. |
| `docs/` | Three deep-dive guides (see [Further Reading](#-further-reading)). |
| `.claude/launch.json` | Tells the preview tooling how to start each edition (Simple on port 8503, Full on 8504). |
| `__pycache__/` | Auto-generated compiled Python. Ignored by Git; safe to delete anytime. |

---

## 🗃️ The Dataset File: CSV, Excel & Storage Formats

The training data lives at
[`data/cars24-car-price-cleaned-new.csv`](data/cars24-car-price-cleaned-new.csv)
— a **plain, uncompressed CSV** (~1.5 MB). This section explains what that file
is, the "it opens in Excel when I click it" behaviour, how to inspect it
*safely*, and the better formats you could store tabular data in.

### Why it opens in Excel — and why that's a trap

A **CSV** ("comma-separated values") is just a text file: one row per line,
columns separated by commas. On Windows the `.csv` extension is **associated
with Excel**, so double-clicking it launches Excel. Convenient for a peek — but
Excel silently "helpfully" rewrites data:

- strips leading zeros (`007` → `7`),
- turns long numbers/IDs into scientific notation (`9192631770` → `9.19E+09`),
- reinterprets text like `3-4` or `MAR1` as **dates**,
- can change the character encoding when you save.

> ⚠️ **Never double-click a data CSV, edit it, and hit Save** — you can corrupt
> it without any warning. Excel is a *viewer of last resort* for raw data.

**How to look at it safely instead:**

| Goal | Do this |
| :--- | :------ |
| Just read a few rows | Open in a text editor (VS Code, Notepad) or run `head data/…csv` in a terminal |
| Inspect it properly | Load it in pandas: `pd.read_csv("data/…csv").head()` |
| Confirm what the file *really* is | `file data/…csv` (reports the true type from the file's bytes, not its name) |
| See true extensions in Explorer | File Explorer → **View → File name extensions** (Windows hides them by default, so `data.csv` may actually be `data.csv.gz`) |

### Could this file be compressed? Yes — and pandas reads it directly

This project keeps the CSV **uncompressed** for maximum human-readability (you
can open it anywhere). But you don't have to: `pandas.read_csv()` transparently
reads **`.gz`, `.bz2`, `.xz` and `.zip`** by file extension, with **no unzip
step and no code change** — the companion Flask project ships this very dataset
as `cars24-…-new.csv.gz` (≈5× smaller) for exactly this reason. A compressed
CSV like `.csv.gz` won't open in Excel on double-click, though: its extension is
`.gz`, so Windows hands it to an **archive tool** (7-Zip / WinRAR), not Excel.
To peek inside without extracting: `zcat file.csv.gz | head` (Git Bash) or
`pd.read_csv("file.csv.gz", nrows=5)`.

### Storage-format alternatives — measured on *this* dataset

Written from the same 19,820 × 17 table; read time is the fastest of 5 pandas
reads on this machine (your absolute numbers will differ — the **ranking** is
what matters):

| Format | File size | vs CSV | Read speed | Human-readable? | Excel double-click? | Keeps column types? |
| :----- | --------: | -----: | ---------: | :-------------- | :------------------ | :------------------ |
| **CSV (raw)** — what's shipped here | 1,535 KB | 100 % | 25 ms | ✅ plain text | ✅ yes | ❌ everything is text |
| **CSV + gzip** (`.csv.gz`) | 290 KB | 19 % | 28 ms | ⚠️ after unzip | ❌ archive tool | ❌ |
| **CSV + xz / LZMA** (`.csv.xz`) | 163 KB | 11 % | 34 ms | ⚠️ after unzip | ❌ | ❌ |
| **CSV + bzip2** (`.csv.bz2`) | 151 KB | 10 % | 74 ms | ⚠️ after unzip | ❌ | ❌ |
| **Parquet** (snappy) | 274 KB | 18 % | **7 ms** | ❌ binary | ❌ needs tools | ✅ yes |
| **Parquet** (zstd) | 227 KB | 14 % | **7 ms** | ❌ binary | ❌ | ✅ yes |
| **Feather / Arrow** | 867 KB | 57 % | **5 ms** | ❌ binary | ❌ | ✅ yes |

**How to read this table:**

- **Smallest on disk:** `CSV + bzip2` (10 %) — but the **slowest to read** (3× a
  raw CSV). Great for cold archival you rarely open; poor for a file you load
  often.
- **Best size/speed balance for a git repo:** **`CSV + gzip`** — 5× smaller than
  raw CSV, reads just as fast, one command to make (`gzip -9 file.csv`), and
  pandas reads it directly. This is what the Flask project uses.
- **Best for real data pipelines:** **Parquet** — nearly as small as gzip **and
  ~3–4× faster to read** than CSV, because it's *columnar* and stores each
  column's type, so no "is this a number or a string?" guessing on load. Needs
  the `pyarrow` library. This is the industry default for analytics.
- **Fastest read, size no object:** **Feather/Arrow** — near-instant, but ~3×
  larger than Parquet; ideal for short-lived local hand-offs, not for shipping.
- **Most universal & readable:** **raw CSV** — anyone can open it, anywhere, with
  no special library; the price is size and the loss of type information.

> 🧭 **Rules of thumb:** *sharing with humans / tiny files* → **CSV**;
> *shrinking a CSV in a repo with zero friction* → **CSV + gzip**;
> *a real analytics workflow or a large dataset* → **Parquet**;
> *maximum read speed for temporary local files* → **Feather**.
> Avoid **pickle** for datasets — it's fast but executes arbitrary code on load
> (a security risk) and breaks across library versions.

---

## 🐳 Companion Flask REST API

Alongside this Streamlit app, a **containerised REST API** version of the same
predictor was built and now lives in its **own separate repository**. It reuses
the **same two Random Forest models**, wrapping them behind a single
`POST /predict` HTTP endpoint, and ships with a full **Docker + AWS ECS/Fargate**
deployment guide.

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"make": "MARUTI", "model": "SWIFT VDI", "age": 3, "km_driven": 45000}'
```
```json
{ "predicted_price_lakhs": 6.5, "predicted_price_display": "₹6.50 Lakhs",
  "price_range": { "label": "Medium", "display": "₹3.99 Lakhs - ₹6.75 Lakhs" } }
```

That project's own README documents the API, the dev-vs-production Docker split,
model compression benchmarks (it pushes the artifacts smaller still with **LZMA**
compression), and step-by-step AWS deployment.

---

## 🤖 Automation (CI / CD / CDD)

The project is ready to be automated with **GitHub Actions** so that every push
can automatically **test the code, deploy the app, and retrain the model when
the data changes**. A complete, copy-paste, beginner-friendly guide — with ready
workflow files for CI, Streamlit Cloud / Docker deployment, and scheduled
retraining — is in
[docs/CI_CD_GITHUB_ACTIONS.md](docs/CI_CD_GITHUB_ACTIONS.md).

| Term | Means | For this project |
| :--- | :---- | :--------------- |
| **CI** — Continuous Integration | Auto-check code isn't broken on every push | Install → compile → train → sanity-check a prediction |
| **CD** — Continuous Delivery | Auto-publish the running app when checks pass | Streamlit Community Cloud (zero config) or a Docker image |
| **CDD** — Continuous Data/Model Delivery | Auto-retrain when the data changes | Re-run `train_model.py` on a schedule or on `data/` changes |

---

## 🔧 Troubleshooting

| Issue | Fix |
| :---- | :-- |
| `ModuleNotFoundError` | Activate your virtual environment, then re-run `pip install -r requirements.txt`. |
| `Model artifacts not found` / `Models not found` | Run `python train_model.py` once to generate the `models/` files. |
| Port 8501 is busy | Use a different port: `streamlit run app.py --server.port 8502`. |
| App seems slow on first load | It's deserialising the model once and caching it — subsequent interactions are instant. |
| The form looks empty / no brands | The `metadata.json` artifact is missing — retrain with `python train_model.py`. |

---

## 🧰 Tech Stack & Glossary for Newcomers

**Built with:**

- **[Streamlit](https://streamlit.io)** — turns a plain Python script into a web
  UI, no HTML/CSS required.
- **[scikit-learn](https://scikit-learn.org)** — provides the Random Forest
  algorithm and the training pipeline.
- **pandas / numpy** — load and reshape the tabular data.
- **joblib** — saves the trained models to disk and reloads them fast.

**Words you'll see, in plain English:**

| Term | Meaning |
| :--- | :------ |
| **Model** (`.pkl`) | The trained "brain" saved to a file. Load it and ask it to predict. |
| **Regression** | Predicting a *number* (the exact price). |
| **Classification** | Predicting a *category* (Low / Medium / High). |
| **Random Forest** | Many decision trees voting together for a stable, accurate answer. |
| **One-hot encoding** | Turning a category like "Diesel" into 0/1 columns a model can read. |
| **Lakh / Crore** | Indian number units: 1 Lakh = ₹100,000; 1 Crore = 100 Lakhs = ₹10,000,000. |
| **Artifact** | A file produced by training (a `.pkl` model or a `.json` config). |
| **`__pycache__`** | A folder Python creates by itself to start faster. Ignore it. |

---

## 📚 Further Reading

Three companion guides go deeper, each written for a beginner:

- 📐 **[docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md)** — the engineering rationale:
  the data contract, the modelling and UI/UX decisions, and how the pieces fit.
- 🛡️ **[docs/INPUT_VALIDATION_GUIDE.md](docs/INPUT_VALIDATION_GUIDE.md)** — how the
  app makes wrong inputs impossible, plus what `__pycache__`, smoke tests and the
  generated files are.
- 🤖 **[docs/CI_CD_GITHUB_ACTIONS.md](docs/CI_CD_GITHUB_ACTIONS.md)** — automate
  testing, deployment and retraining with GitHub Actions.

---

> ⚠️ **Disclaimer:** Predictions are statistical estimates based on historical
> Cars24 listings. Treat them as guidance, not a guaranteed sale price.

<sub>Built with ❤️ using Streamlit and scikit-learn.</sub>

---

### 🔗 The Car Prices Trio

Three sibling projects built on the same Cars24 dataset:

- 🎛️ **Streamlit web app** — interactive price-predictor UI · _you are here_
- 🐳 **[Flask REST API →](https://github.com/kalyancn4u/app_flask_car_prices)** — containerised API (Docker + AWS ECS/Fargate)
- 🔬 **[MLOps lifecycle →](https://github.com/kalyancn4u/app_mlops_car_prices)** — full SDLC: notebooks → production pipeline
