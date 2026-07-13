# =============================================================================
# Car Prices - clean rebuild & deploy pipeline
#
#   Fresh conda env  ->  train models  ->  auto-pin versions  ->  verify  -> push
#
# The whole point: the env that TRAINS the models also GENERATES requirements.txt
# and .python-version, so Streamlit Cloud installs the exact versions the .pkl
# files were saved with (no version-mismatch AttributeError on load).
#
# Quick start (from a shell where `conda` works, e.g. Anaconda Prompt / Git Bash):
#     make rebuild                 # build 3.12 env, train, pin, verify
#     make rebuild PY=3.14         # ...or pick a different Python version
#     make push                    # commit models + pins and push to GitHub
#
# Requires GNU make. If you don't have it:  conda install -c conda-forge make
# =============================================================================

ENV   ?= car-prices          # conda env name (override: make ENV=foo)
PY    ?= 3.14                 # Python version for the fresh env (override: make PY=3.14)
CONDA ?= conda               # path to conda (override: make CONDA=/d/tools/miniconda3/Scripts/conda.exe)

RUN := $(CONDA) run -n $(ENV) --no-capture-output

.DEFAULT_GOAL := help
.PHONY: help env train freeze verify rebuild push clean

help:  ## Show this help
	@echo "Targets:"
	@echo "  make env       - create conda env '$(ENV)' (Python $(PY)) and install deps"
	@echo "  make train     - run train_model.py -> regenerate models/*.pkl + *.json"
	@echo "  make freeze    - write requirements.txt + .python-version from the env"
	@echo "  make verify    - load the freshly-saved models to confirm they unpickle"
	@echo "  make rebuild   - env + train + freeze + verify (the full clean run)"
	@echo "  make push      - git add models + pins, commit, and push to GitHub"
	@echo "  make clean     - delete the conda env '$(ENV)'"
	@echo ""
	@echo "Override defaults, e.g.:  make rebuild PY=3.14 ENV=cars314"

env:  ## Create the conda env and install the app's dependencies (latest for this Python)
	$(CONDA) create -y -n $(ENV) python=$(PY)
	$(RUN) python -m pip install --upgrade pip
	$(RUN) python -m pip install numpy pandas scikit-learn joblib streamlit

train:  ## Train both models from the dataset (writes models/*.pkl and *.json)
	$(RUN) python train_model.py

freeze:  ## Pin requirements.txt + .python-version to this exact environment
	$(RUN) python scripts/pin_env.py

verify:  ## Sanity-check: the just-saved models must load in this same env
	$(RUN) python -c "import joblib; joblib.load('models/price_model.pkl'); joblib.load('models/range_model.pkl'); print('OK: both models load cleanly')"

rebuild: env train freeze verify  ## Full clean run: build env, train, pin, verify
	@echo ""
	@echo "Rebuild complete. Review the diff, then 'make push' (or push manually)."
	@echo "Reminder: set Streamlit Cloud's Python version to $(PY) to match .python-version."

push:  ## Commit the retrained models + regenerated pins and push to GitHub
	git add requirements.txt .python-version models/
	git commit -m "Rebuild models and re-pin environment (Python $(PY))"
	git push origin main

clean:  ## Remove the conda env (models and pins are left untouched)
	-$(CONDA) env remove -y -n $(ENV)
