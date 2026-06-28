# 🤖 Automating the Project with GitHub Actions (CI / CD / CDD)

A beginner-friendly, copy-paste guide to making GitHub **do the boring work for
you** — testing your code, deploying the app, and retraining the model — every
time you push a change.

No prior DevOps knowledge needed. If you can edit a text file, you can do this.

---

## 1. The jargon, in one table

These three letters scare people. They shouldn't.

| Term          | Stands for                                                               | In plain words                                                          | For*this* project                                                                      |
| :------------ | :----------------------------------------------------------------------- | :---------------------------------------------------------------------- | :--------------------------------------------------------------------------------------- |
| **CI**  | Continuous**Integration**                                          | "Every time I save code, automatically check it isn't broken."          | Install deps, compile the code,**train the model**, and sanity-check a prediction. |
| **CD**  | Continuous**Delivery / Deployment**                                | "If the checks pass, automatically publish the running app."            | Auto-deploy the Streamlit app (or build a Docker image).                                 |
| **CDD** | Continuous**Data/Model Delivery** *(a.k.a. Continuous Training)* | "When the data changes, automatically retrain and republish the model." | Re-run `train_model.py` on a schedule or when `data/` changes.                       |

> 🧠 **CDD** is the machine-learning twist on CD: normal apps redeploy when
> *code* changes; ML apps must also refresh when *data* changes. That's the
> third pillar.

---

## 2. What is GitHub Actions, really?

Think of it as a **free robot assistant** living inside your GitHub repository. 🦾

You leave it a to-do list (a "**workflow**" file). Whenever something happens —
you push code, open a pull request, or a timer fires — the robot:

1. rents a fresh, clean computer in the cloud (called a **runner**),
2. downloads your code onto it,
3. runs the exact commands you listed,
4. shows you a green ✅ or red ❌.

The to-do lists are plain text files that live in a special folder:

```
.github/
└── workflows/
    ├── ci.yml          # the "test my code" robot
    ├── cdd-retrain.yml # the "retrain the model" robot
    └── cd-docker.yml   # the "publish the app" robot   (optional)
```

That folder name and location are **mandatory** — GitHub only looks there.

---

## 3. Before you start: get the project onto GitHub

Actions only runs on GitHub, so the code must live there first. One-time setup:

```bash
# from the project folder
git init
git add .
git commit -m "Initial commit"

# create the repo on GitHub and push (needs the free GitHub CLI 'gh')
gh repo create car-price-predictor --public --source=. --push
```

No `gh`? Create an empty repo on github.com, then:

```bash
git remote add origin https://github.com/<your-username>/car-price-predictor.git
git branch -M main
git push -u origin main
```

> ✅ **Good news about this repo's setup:** the dataset (`data/*.csv`) and the
> small config files (`models/*.json`) are committed, but the **big model files
> (`models/*.pkl`) are git-ignored**. That's exactly right — the robot will
> *rebuild* the `.pkl` files itself by running `train_model.py`. You never store
> large binaries in git.

---

## 4. Anatomy of a workflow file (read this once)

Every workflow is a [YAML](https://en.wikipedia.org/wiki/YAML) file. YAML is just
"settings written with indentation." Here's the skeleton, annotated:

```yaml
name: CI                       # 1. a friendly name (shown in the Actions tab)

on:                            # 2. WHEN should the robot wake up?
  push:
    branches: [ main ]         #    - on every push to main
  pull_request:                #    - and on every pull request

jobs:                          # 3. WHAT should it do? (one or more "jobs")
  build:
    runs-on: ubuntu-latest     #    - rent a fresh Linux computer
    steps:                     #    - run these steps in order
      - uses: actions/checkout@v4   # a ready-made action (downloads your code)
      - run: echo "Hello!"          # or any shell command you like
```

The only four words you must remember:

| Word                | Meaning                                                                     |
| :------------------ | :-------------------------------------------------------------------------- |
| `on`              | the**trigger** — what wakes the robot up (push, schedule, manual).   |
| `jobs`            | the**tasks** — independent units of work.                            |
| `steps`           | the**commands** inside a job, run top to bottom.                      |
| `uses` vs `run` | `uses:` borrows a pre-built action; `run:` runs your own shell command. |

> ⚠️ **YAML rule #1:** indent with **spaces, never Tabs**, and keep it consistent
> (2 spaces). 90% of "my workflow won't run" problems are a stray indent.

---

## 5. Step 1 — CI: automatically test every change

This is the most important one and works for free immediately.

**Create `tests/smoke_test.py`** (a quick "does it actually work?" check):

```python
# tests/smoke_test.py — a fast sanity check the CI robot runs.
import json, joblib, pandas as pd

model = joblib.load("models/price_model.pkl")
cols = json.load(open("models/feature_columns.json"))

row = {c: 0 for c in cols}
row.update({"km_driven": 30000, "mileage": 18.0, "engine": 1200,
            "max_power": 80.0, "age": 5, "make": "MARUTI",
            "model": "SWIFT VXI", "Petrol": 1, "Manual": 1, "Seats_5": 1})

estimate = float(model.predict(pd.DataFrame([row])[cols])[0])
print(f"Swift estimate: Rs {estimate:.2f} Lakhs")
assert 1 < estimate < 50, "Price is outside a sane range — something broke!"
print("Smoke test passed.")
```

**Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Get the code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip                 # speeds up repeat runs

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Check the code compiles
        run: python -m py_compile app.py app_v2.py train_model.py

      - name: Train the model (smoke-tests the whole pipeline)
        run: python train_model.py

      - name: Sanity-check a prediction
        run: python tests/smoke_test.py
```

**What it does, in order:** rents a Linux box → installs Python 3.11 → installs
your libraries → confirms the code has no syntax errors → **runs the real
training pipeline** on the committed CSV → checks a Swift comes out at a sensible
price. If anything breaks, you get a red ❌ and an email — *before* it reaches
users.

> 💡 Training takes ~1–2 minutes here, which is fine. If your data ever grows
> huge, move the training step into the CDD workflow (Step 3) and keep CI to just
> the compile + a cached-model test.

---

## 6. Step 2 — CD: automatically publish the app

You have two routes. Pick one.

### Route A (recommended, zero config): Streamlit Community Cloud

Streamlit's own hosting is **already** continuous deployment — it watches your
GitHub repo and redeploys on every push. No workflow file needed.

1. Push your repo to GitHub (Section 3).
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → sign in with GitHub.
3. **New app** → choose your **repo**, **branch** (`main`), and **main file**
   (`app.py` or `app_v2.py`).
4. Click **Deploy**. Done — you get a public URL.
5. From now on, **every `git push` redeploys automatically.** ✨

> ⚠️ **Important for this project:** the trained `models/*.pkl` files are
> git-ignored, so a fresh deploy won't have them and the app will show
> *"Model artifacts not found."* Two clean fixes — pick **one**:
>
> 1. **Train on the host (recommended).** Add this at the very top of `app.py`
>    (right after the imports) so the app builds the models if they're missing:
>    ```python
>    import os
>    if not os.path.exists("models/price_model.pkl"):
>        import train_model
>        train_model.main()
>    ```
>    The first boot trains for ~1–2 min; later boots are instant.
> 2. **Or commit the models.** Remove the `models/*.pkl` line from `.gitignore`
>    and commit them — simplest, but adds ~15 MB to the repo.

### Route B (advanced, Actions-driven): build a Docker image

Use this if you want to deploy to your own server, Render, Fly.io, etc.

**Create a `Dockerfile`:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python train_model.py            # bake the trained models into the image
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Create `.github/workflows/cd-docker.yml`:**

```yaml
name: CD - Build & publish Docker image

on:
  push:
    branches: [ main ]
    tags: [ "v*" ]              # also on version tags like v1.0

permissions:
  contents: read
  packages: write              # allow pushing to GitHub's image registry

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}   # provided automatically

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

This produces a ready-to-run image at `ghcr.io/<you>/<repo>:latest`. Anyone (or
any server) can then run the app with one command:

```bash
docker run -p 8501:8501 ghcr.io/<you>/<repo>:latest
```

---

## 7. Step 3 — CDD: automatically retrain when data changes

The ML pillar. This robot retrains the model **on a schedule** and **whenever you
update the dataset**, so predictions never go stale.

**Create `.github/workflows/cdd-retrain.yml`:**

```yaml
name: CDD - Retrain model

on:
  push:
    paths:
      - "data/**"            # whenever the dataset changes
  schedule:
    - cron: "0 3 * * 1"      # every Monday at 03:00 UTC (see note below)
  workflow_dispatch:          # adds a manual "Run workflow" button

permissions:
  contents: write             # needed so the robot can commit refreshed files

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - run: pip install -r requirements.txt

      - name: Retrain
        run: python train_model.py

      # Small text configs CAN live in git — commit them back.
      - name: Commit refreshed metadata
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add models/*.json
          git commit -m "CDD: refresh model metadata [skip ci]" || echo "Nothing changed"
          git push

      # Big binaries should NOT live in git — publish them as a download instead.
      - name: Upload trained models as an artifact
        uses: actions/upload-artifact@v4
        with:
          name: trained-models
          path: models/*.pkl
          retention-days: 14
```

**Two important ideas here:**

- **`cron: "0 3 * * 1"`** is a timer. The five fields are
  `minute hour day-of-month month day-of-week`. `0 3 * * 1` = "minute 0, hour 3,
  any day, any month, on Mondays" → **every Monday 03:00 UTC**. (Try
  [crontab.guru](https://crontab.guru) to design your own.)
- **Where do the outputs go?** The tiny `*.json` files are committed straight
  back to the repo. The large `*.pkl` files are uploaded as a downloadable
  **artifact** (find it on the run's summary page) — this avoids bloating git
  with big binaries. `[skip ci]` in the commit message stops it from waking the
  CI robot in an endless loop.

---

## 8. Turning Actions ON and giving it permissions

Actions is **enabled by default**. You usually just add the files above and push.
Two settings matter for the CDD robot that commits back:

1. On GitHub, open your repo → **Settings** → **Actions** → **General**.
2. Under **Workflow permissions**, select **"Read and write permissions"**
   (this lets the `git push` step in Step 3 succeed). Save.

That's it. The special password the robots use — `${{ secrets.GITHUB_TOKEN }}` —
is created **automatically** for every run. You don't make it yourself.

### Adding your own secrets (only if a step needs an external key)

If you deploy to a service that needs an API key (Render, AWS, etc.):

1. Repo → **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**.
2. Name it (e.g. `RENDER_API_KEY`) and paste the value.
3. Use it in a workflow as `${{ secrets.RENDER_API_KEY }}`.

> 🔐 **Never** paste a password or key directly into a `.yml` file or your code.
> Secrets are encrypted and hidden from logs. Workflow files are plain text that
> anyone with repo access can read.

---

## 9. Watching it work (and showing it off)

- **See runs:** click the **Actions** tab in your repo. Each run shows every
  step with live logs; click a red ❌ to read exactly what failed.
- **Run manually:** any workflow with `workflow_dispatch:` gets a **"Run
  workflow"** button in that tab.
- **Add a status badge** to your `README.md` so visitors see it's healthy:

  ```markdown
  ![CI](https://github.com/<your-username>/<your-repo>/actions/workflows/ci.yml/badge.svg)
  ```

  It renders a little green **CI ✓ passing** badge.

---

## 10. Troubleshooting (the usual suspects)

| Symptom                               | Most likely cause & fix                                                                                                             |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| Workflow never runs                   | File isn't under `.github/workflows/`, or the `on:` branch name doesn't match (`main` vs `master`), or a YAML indent error. |
| "Workflow file is invalid"            | A Tab instead of spaces, or misaligned indentation. Re-check spacing.                                                               |
| `ModuleNotFoundError` in a run      | A library is missing from `requirements.txt`. Add it and push.                                                                    |
| Push step fails:*permission denied* | Set**Workflow permissions → Read and write** (Section 8).                                                                    |
| Deploy can't find `model.pkl`       | The host didn't retrain. Ensure `python train_model.py` runs at build/startup (the `.pkl` files aren't in git).                 |
| Job is slow / times out               | Add `cache: pip` (already included), and keep heavy training in the CDD workflow rather than on every CI push.                    |

---

## 11. One-page recap

```
                       ┌─────────────────────────────────────────┐
   you: git push  ───► │              GitHub Actions             │
                       ├─────────────────────────────────────────┤
                       │ CI   (ci.yml)         every push/PR      │
                       │   install → compile → train → predict ✅ │
                       │                                          │
                       │ CDD  (cdd-retrain.yml) data change/weekly│
                       │   retrain → commit JSON → upload .pkl    │
                       │                                          │
                       │ CD   (Streamlit Cloud or cd-docker.yml)  │
                       │   publish the running app 🚀             │
                       └─────────────────────────────────────────┘
```

**Checklist to go live:**

- [ ] Push the project to GitHub (Section 3).
- [ ] Add `tests/smoke_test.py` and `.github/workflows/ci.yml` → green CI.
- [ ] Deploy via Streamlit Cloud (Route A) — auto-redeploys on every push.
- [ ] (Optional) Add `cdd-retrain.yml` and set **Read and write** permissions.
- [ ] (Optional) Add a CI badge to the README.

That's the whole loop: **write code → push → robots test, retrain, and deploy —
automatically.**
