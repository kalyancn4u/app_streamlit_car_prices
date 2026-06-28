# 🛡️ How the App Stops Wrong Inputs — A Beginner's Guide

This guide explains, in plain language, **how the car-price app makes it
impossible to type a wrong or impossible answer in the first place** — and a few
extra things a newcomer will see in the project folder (smoke tests, that mysterious
`__pycache__` folder, and so on).

No prior knowledge needed. If you can read a recipe, you can read this.

---

## 1. The big idea: make mistakes *impossible*, don't just *complain* about them

There are two ways to handle bad input:

| Approach | Example | Problem |
| :------- | :------ | :------ |
| ❌ **Check afterwards** | Let the user type "Petrl", then show *"Error: unknown fuel"* | Annoying, easy to get wrong, errors slip through |
| ✅ **Prevent up front** | Only let the user **pick** from a list: Petrol / Diesel / CNG | A wrong value can't even be entered |

> 🔑 **The golden rule:** *If a door is locked, you don't need a sign that says
> "do not enter."* We lock the doors instead of putting up signs.

The fancy name for this is **"make invalid states unrepresentable."** We do it
because **we already have clean, validated data** — 19,820 real cars. We know
every real brand, model, fuel and gearbox that exists. So the app simply **only
ever offers choices that are real.**

---

## 2. Two kinds of input — and why we treat them differently

Think about a single car. Some facts are **baked into the car itself**; others
are just **about this particular sale**.

| Kind | Examples | How we protect it |
| :--- | :------- | :---------------- |
| 🚗 **Part of the car** (intrinsic) | brand, model, fuel, gearbox, seats, engine, power | Tied to the model — you can only get the values that car really has |
| 🧾 **About the sale** (circumstantial) | who's selling, how old, how many km | Free to choose, but only within sensible limits |

Why the split? A *"Maruti Swift VDI"* is **always** a diesel — that's part of the
car, so we lock it. But **any** car can be 5 years old or sold by a dealer — so
those stay open (within limits).

---

## 3. The five locks that prevent wrong inputs

### 🔒 Lock 1 — You choose, you never type

Every input is a **dropdown, slider, or radio button** — never a free text box.

- **Why it helps:** you can't make a typo ("Marutee"), and you can't enter a
  number that's out of range. A menu, not a blank page.
- **Where:** every field in both `app.py` and `app_v2.py`.

> The *old* version had a free-text "Model" box. With 3,233 real models, people
> mistyped constantly — and the app quietly gave a meaningless answer. That box
> is gone.

### 🔒 Lock 2 — Pick a Brand → the Model list narrows to that brand

When you choose **Maruti**, the **Model** dropdown shows *only Maruti models*.
Choose **BMW**, and it instantly shows *only BMW models*.

- **Why it helps:** you can never pair "Maruti" with a "BMW X5" — the wrong
  models simply aren't on the menu.
- **Like:** pick a country first, and the city list only shows that country's
  cities.

**Step by step, what happens the moment you change the Brand:**

1. You pick a new Brand.
2. The app re-draws the page (Streamlit calls this a *rerun* — it's automatic).
3. The Model dropdown is rebuilt from `makes_models[brand]` — that brand's list.
4. The old model selection is dropped and it shows the first model of the new
   brand. No stale, mismatched leftover. (More on *why* in Section 5.)

### 🔒 Lock 3 — Pick a Model → Fuel, Gearbox and Seats follow automatically

This is the important new one. The model variant name **already decides** the
fuel and gearbox:

- `SWIFT VXI` → Petrol · Manual
- `SWIFT VDI` → **Diesel** · Manual  (the "D" literally means diesel)
- `X5 XDRIVE 30D` → Diesel · **Automatic**

In fact, **3,231 of the 3,233 models have exactly one fuel and one gearbox** in
the data. So we don't ask the user to guess — we read it off the chosen car.

The two apps show this slightly differently:

| | Full app (`app.py`) | Simple app (`app_v2.py`) |
| :-- | :------------------ | :----------------------- |
| Fuel / Gearbox / Seats | Shown as **dropdowns limited to that model's real options** (usually one option) | **Auto-filled and shown as read-only text** ("⛽ Diesel · ⚙️ Automatic · 💺 5 seats") |
| Can you pick something impossible? | No — only real options are listed | No — you can't edit it at all |

> 🚫 **"Electric Alto" can never happen.** The Maruti Alto was never electric in
> the data, so "Electric" is never offered for it. Try to picture entering it —
> there's no field to do so.

**Watch it work:** change the model from `SWIFT VXI` to `SWIFT VDI` and the fuel
flips from *Petrol* to *Diesel* by itself. You didn't touch a fuel control —
because there isn't one to get wrong.

### 🔒 Lock 4 — Sliders can't go past real-world limits

Age, kilometres, and (in the full app) engine/power/mileage are **sliders** with
a minimum and maximum taken from the actual data.

- **Why it helps:** you can't enter a 500-year-old car or negative kilometres.
  The slider physically stops at sensible ends.
- The limits aren't guessed — they come from the real spread of 19,820 cars
  (we trim the most extreme 1% off each end so one weird listing doesn't stretch
  the slider).

### 🔒 Lock 5 — The technical specs are filled in for you

A beginner can't be expected to know a car's **engine size (cc)** or **power
(bhp)**. So the simple app hides them and **fills them from the chosen model's
typical values**.

- **Why it helps:** you can't enter a *wrong* engine size if you never enter one.
- **Why it must be per-model:** filling every car with one "average" engine makes
  a BMW look like a hatchback and crashes its price estimate. (Full reasoning in
  [DESIGN_NOTES.md](DESIGN_NOTES.md) §5.)

---

## 4. The whole journey of one estimate (start to finish)

Here is everything that happens, in order, with no gaps:

1. **You pick a Brand.** → Model list rebuilds to that brand only. *(Lock 2)*
2. **You pick a Model.** → The app looks up that model and decides:
   - its fuel, gearbox and seats *(Lock 3)*,
   - its typical engine, power and mileage *(Lock 5)*.
3. **You set Age and Kilometres** with sliders that can't exceed real limits. *(Lock 4)*
4. **(Full app only) You pick a Seller type** — the one free, sale-related choice.
5. The app builds a tidy row of numbers in the **exact shape the model expects**
   (it fills every column, sets the right 0/1 flags, and orders them correctly).
6. The trained model reads that row and returns an **exact price** and a
   **budget band** (Low / Medium / High).
7. The price is shown in **₹ Lakhs / Crores**.

At **no point** can a human type a value the model hasn't seen before. Every
field was either chosen from a real list or filled in from real data.

---

## 5. The one tricky bit: "stale" leftovers (and how we avoid them)

A subtle trap in Streamlit: if you *remember* a widget's value too aggressively,
you can end up with a leftover that no longer fits. Imagine:

- You pick **BMW → X5**.
- You switch the brand to **Maruti**.
- If the app *kept* "X5" selected, you'd now have **"Maruti X5"** — nonsense!

**How we prevent it:** we deliberately do **not** pin the Model / Fuel / Gearbox
dropdowns to a saved value (in code terms: we don't give them a fixed `key`).
Each time the page redraws, these dependent dropdowns are rebuilt from scratch
based on what's currently chosen above them. When their list of options changes,
they reset to the first valid option instead of clinging to an old one.

> 🧠 In short: **brand drives model; model drives fuel/gearbox/seats.** Things
> only ever flow downhill, so an upstream change always refreshes everything
> below it. No stale mismatches.

---

## 6. Where the "list of real values" comes from: `metadata.json`

The app doesn't hard-code any of these lists. They all live in one generated
file, **`models/metadata.json`**, which the training script writes. It contains:

| Inside `metadata.json` | What it's for |
| :--------------------- | :------------ |
| `makes_models` | Which models belong to each brand *(Lock 2)* |
| `model_options` / `make_options` | Valid fuel / gearbox / seats per model *(Lock 3)* |
| `model_specs` / `make_specs` | Typical engine / power / mileage per model *(Lock 5)* |
| `numeric_features` | The slider minimums and maximums *(Lock 4)* |

**Why this matters:** there is **one single source of truth**. When you retrain
on new data, this file is rewritten, and the form updates itself automatically.
The dropdowns can never drift out of sync with what the model was trained on,
because they're built from the same file the model came with.

To regenerate everything:

```bash
python train_model.py
```

---

## 7. "Smoke tests" — how we checked it really works

### What is a smoke test?

The name comes from electronics: *plug in the new gadget and see if smoke comes
out.* 💨 A **smoke test** is a quick, throwaway check that the basic thing works
before you trust it — not a thorough exam, just *"does it catch fire?"*

### The smoke tests we ran for this project

While building the app, small temporary scripts were used to confirm behaviour,
for example:

- **Price sanity:** does a Maruti Swift come out around ₹5 Lakhs and a BMW X5
  around ₹20 Lakhs? (Catches the old "shows ₹5 instead of ₹5 Lakhs" bug.)
- **Hidden-spec check:** does auto-filling a model's engine/power keep premium
  cars expensive instead of squashing them to average?
- **Option check:** does `SWIFT VDI` really offer only *Diesel*, and does
  switching models flip the fuel automatically? (This proves Lock 3.)

These scripts were named with a leading underscore (e.g. `_smoke_test.py`) so
they were easy to spot, run once, and **delete afterwards** — they are not part
of the finished app. If you ever see a file like `_something.py`, it's a
scratch/test file and safe to remove.

### How you can run your own smoke test

The app itself *is* the best smoke test: launch it and click around.

```bash
streamlit run app_v2.py     # simple version
streamlit run app.py        # full version
```

If a Maruti shows a few Lakhs and a Mercedes shows ~₹20 Lakhs, the wiring is good.

---

## 8. Things you'll see in the folder — explained for newcomers

Open the project folder and you'll notice some files and folders that aren't
obvious. Here's what each one is and **whether you should care**:

| You see… | What it is | Do you need to touch it? |
| :------- | :--------- | :----------------------- |
| `__pycache__/` | A folder Python **creates by itself**. It stores a pre-chewed (compiled) copy of the code so it starts faster next time. | **No.** Ignore it. It's rebuilt automatically and is set to be ignored by Git. Deleting it is harmless. |
| `*.pkl` files in `models/` | The **trained models**, saved to disk (`price_model.pkl`, `range_model.pkl`). | Don't edit by hand. Recreate with `python train_model.py`. |
| `*.json` files in `models/` | Plain-text settings the app reads (the lists from Section 6). | Don't edit by hand; they're generated. |
| `_*.py` files | **Temporary smoke-test scripts** (Section 7). | Safe to delete; not part of the app. |
| `.claude/launch.json` | A small helper that tells the preview tool how to start the app. | Leave it; harmless. |
| `data/…csv` | The original spreadsheet of 19,820 cars. | Only needed when **re-training**, not when running the app. |
| `venv/` (if present) | A private copy of Python with this project's libraries. | Created once during setup; ignored by Git. |

> 💡 Rule of thumb for a newcomer: if a file or folder is **generated
> automatically** (`__pycache__`, `.pkl`, `.json`, `venv`), you never edit it by
> hand — you regenerate it. The only files humans edit are the `.py` code and
> the `.md` docs.

---

## 9. Quick reference — every input and its safety net

| Input | Type of control | Why it can't be wrong |
| :---- | :-------------- | :-------------------- |
| Brand | Dropdown | Fixed list of 41 real brands |
| Model | Dropdown | Rebuilt to show only the chosen brand's models |
| Fuel | Auto-filled / limited dropdown | Only fuels that model truly came with |
| Gearbox | Auto-filled / limited dropdown | Only gearboxes that model truly came with |
| Seats | Auto-filled / limited dropdown | Only seat counts that model truly came with |
| Engine / Power / Mileage | Auto-filled (simple app) or bounded slider | Taken from the model, or capped at real limits |
| Age / Kilometres | Slider | Stops at sensible minimum and maximum |
| Seller type | Dropdown (full app) | Fixed list; this one is a free choice (it's about the sale, not the car) |

**Bottom line:** because we started from clean, validated data and only ever let
you pick from it, *there is no path to a wrong input.* The mistakes aren't
caught — they're made impossible.
