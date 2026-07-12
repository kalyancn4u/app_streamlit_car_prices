# 🧪 Testing & Debugging Guide — novice → mastery

Learn to **test, debug, and troubleshoot** using this project as a practice ground.
No prior testing experience needed. The exercises live in
[`tests/test_stubs.py`](../tests/test_stubs.py); a green baseline is in
[`tests/test_smoke.py`](../tests/test_smoke.py).

---

## 1. What is a test?

A tiny piece of code that automatically checks *"does this behave the way I expect?"*.

```python
def test_price_unit():
    assert train_model.CONFIG["price_unit"] == "Lakhs"
```

`assert X` means "I claim X is true." If it isn't, the test fails and points at the
line. Tests let you refactor and retrain *without fear*.

## 2. Running the tests

```bash
pip install -r requirements.txt
pip install pytest
pytest -v            # from the repo root
pytest -k clean      # only tests with "clean" in the name
pytest -x            # stop at first failure
```

`conftest.py` (at the repo root) puts the project on the import path, so
`from train_model import ...` just works. Dots pass, `s` = skipped stubs, `F` = fail.

## 3. Arrange-Act-Assert — the shape of every test

```python
def test_clean_uppercases():
    df = pd.DataFrame({"selling_price":[5.0], "make":[" maruti "], "model":["swift"]})  # Arrange
    out = train_model.clean_dataset(df)                                                # Act
    assert out["make"].tolist() == ["MARUTI"]                                          # Assert
```

## 4. A key real-world skill: making code *testable*

You **cannot** `import app.py` in a test — importing a Streamlit script tries to draw
the whole UI. That's normal. The lesson: keep your *logic* in plain functions
(`train_model.py` already does) and keep only the *drawing* in the app. One mastery stub
asks you to move `format_lakhs()` out of `app_v1.py` into an importable `formatting.py` —
**refactoring for testability is half of professional testing.**

## 5. The difficulty ladder (in `tests/test_stubs.py`)

| Level | Focus | Skill it builds |
| :---- | :---- | :-------------- |
| 🟢 **1 — First steps** | read `CONFIG` | how to run pytest; confidence |
| 🟡 **2 — Pure functions** | `make_price_ranges`, `numeric_input_specs` | Arrange-Act-Assert |
| 🟠 **3 — Edge cases** | the `5`/`>5` rename, dropped rows | reading code carefully |
| 🔴 **4 — Integration** | load the saved models and predict | how the parts connect |
| 🟣 **5 — Mastery** | `@parametrize`, **refactor for testability** | professional testing |
| 🐞 **Debugging drill** | the price-unit (₹5 vs ₹4.75 L) bug as a guard | regression testing |

**To complete a stub:** delete `@pytest.mark.skip(...)`, replace `pytest.fail("TODO")`
with real `assert`s, run `pytest`.

## 6. Debugging when a test goes red

1. **Read the traceback bottom-up** — *what* failed and *where*.
2. **Reproduce small:** `pytest tests/test_stubs.py::test_... -x`.
3. **Print it:** add `print(value)` and run `pytest -s` so prints show.
4. **Question the test, not just the code** — often the expectation is wrong.
5. **Fix, re-run, keep the test** — it now guards that behaviour forever.

## 7. Troubleshooting cheat-sheet

| Symptom | Fix |
| :------ | :-- |
| `ModuleNotFoundError: train_model` | Run pytest from the repo root (so `conftest.py` is picked up). |
| A model test is skipped | Run `python train_model.py` once to create `models/*.pkl`. |
| `ScriptRunContext` warnings when importing an app | Don't import `app.py` in tests — test `train_model.py` and the saved model instead. |
| Stub "passes" but checks nothing | You removed the skip but left `pytest.fail` / no asserts. |

## 8. In THIS repo — the debugging drill

The most instructive stub is the **price-unit regression** (see `docs/DESIGN_NOTES.md`):
the original app treated a model output of `4.75` (= ₹4.75 **Lakhs**) as raw rupees and
printed "₹5". Turn that fixed bug into a permanent tripwire — a test that asserts prices are
Lakhs-scale — so it can never silently come back.

> **The mastery mindset:** make logic testable, and turn every fixed bug into a test. Your
> project then only ever gets *more* reliable.
