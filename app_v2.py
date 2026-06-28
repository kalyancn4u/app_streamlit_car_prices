"""
Car Price Estimator - Simple Edition (v2)
=========================================

A deliberately minimal version of the app for demos to complete beginners.

What makes it simple AND mistake-proof:
  * Only the questions a non-expert can answer: brand, model, age, kilometres.
  * Everything else is decided FOR the user, from the car they picked:
      - engine / power / mileage  -> the chosen model's typical values
      - fuel / gearbox / seats     -> the configurations that model actually
        came in (a "SWIFT VDI" is Diesel/Manual; you can't pick "Electric").
    Because these are shown but never editable, an impossible combination
    simply cannot be entered.
  * Plain Streamlit widgets only - no custom HTML, CSS, cards or gauges.
  * No "Predict" button: the estimate updates live as you change any input.

It reuses the exact same trained models as the full app (app.py). Run with:

    streamlit run app_v2.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

MODELS = Path("models")


# --- Load the trained models + UI metadata (once) --------------------------
@st.cache_resource(show_spinner="Loading…")
def load():
    price_model = joblib.load(MODELS / "price_model.pkl")
    range_model = joblib.load(MODELS / "range_model.pkl")
    feature_columns = json.loads((MODELS / "feature_columns.json").read_text())
    range_config = json.loads((MODELS / "range_config.json").read_text())
    metadata = json.loads((MODELS / "metadata.json").read_text(encoding="utf-8"))
    return price_model, range_model, feature_columns, range_config, metadata


def rupees(lakhs: float) -> str:
    """Format a price (in Lakhs) the Indian way: Crore / Lakh / Rupees."""
    if lakhs >= 100:
        return f"₹{lakhs / 100:.2f} Crore"
    if lakhs >= 1:
        return f"₹{lakhs:.2f} Lakhs"
    return f"₹{lakhs * 100_000:,.0f}"


# --- Page ------------------------------------------------------------------
st.set_page_config(page_title="Car Price Estimator", page_icon="🚗")

st.title("🚗 Used Car Price Estimator")
st.caption("Tell us about the car and we'll estimate what it's worth.")

try:
    price_model, range_model, feature_columns, range_config, meta = load()
except FileNotFoundError:
    st.warning("Models not found. Run `python train_model.py` first, then reload.")
    st.stop()

makes_models = meta["makes_models"]
num = meta["numeric_features"]


# --- Helpers: everything we decide FROM the chosen model -------------------
def auto_specs(make, model):
    """Typical engine / power / mileage for this model (then make, then global)."""
    return (meta["model_specs"].get(make, {}).get(model)
            or meta["make_specs"].get(make)
            or {k: num[k]["default"] for k in ("mileage", "engine", "max_power")})


def auto_options(make, model):
    """Fuel / gearbox / seats this model actually came in (most common first)."""
    cat = meta["categorical_features"]
    return (meta["model_options"].get(make, {}).get(model)
            or meta["make_options"].get(make)
            or {k: cat[k]["options"] for k in ("fuel", "transmission", "seats")})


# --- The few questions a beginner can answer -------------------------------
brands = list(makes_models.keys())
brand_index = brands.index("MARUTI") if "MARUTI" in brands else 0

left, right = st.columns(2)
with left:
    brand = st.selectbox("Brand", brands, index=brand_index)
with right:
    model = st.selectbox("Model", makes_models[brand])

# Decided automatically from the model — shown, but not editable, so they can
# never disagree with the chosen car. This line updates the instant you change
# the model above.
opts = auto_options(brand, model)
fuel, transmission, seats = opts["fuel"][0], opts["transmission"][0], opts["seats"][0]
st.caption(f"⛽ {fuel}  ·  ⚙️ {transmission}  ·  💺 {seats} seats  "
           f"— set automatically from this model.")

# Each slider gets its own full-width row: a wider track means finer control
# (more pixels per step) and is easier to drag precisely.
age = st.slider("Age (years)", num["age"]["min"], num["age"]["max"],
                num["age"]["default"])
km = st.slider("Kilometres driven", num["km_driven"]["min"],
               num["km_driven"]["max"], num["km_driven"]["default"], step=1000)


# --- Build the model input and predict (live) ------------------------------
specs = auto_specs(brand, model)

row = {col: 0 for col in feature_columns}
row["age"] = age
row["km_driven"] = km
row["mileage"] = specs["mileage"]
row["engine"] = specs["engine"]
row["max_power"] = specs["max_power"]
row["make"] = brand
row["model"] = model
if transmission == "Manual":
    row["Manual"] = 1                    # "Automatic" is the baseline (no flag)
if seats == "5":
    row["Seats_5"] = 1
elif seats == "More than 5":
    row["Seats_Above_5"] = 1             # "Fewer than 5" is the baseline (no flag)
fuel_flag = {"Petrol": "Petrol", "Diesel": "Diesel",
             "LPG": "LPG", "Electric": "Electric"}.get(fuel)  # "CNG" = baseline
if fuel_flag:
    row[fuel_flag] = 1

X = pd.DataFrame([row])[feature_columns]
price = max(float(price_model.predict(X)[0]), 0.0)
band = str(range_model.predict(X)[0])

labels, edges = range_config["labels"], range_config["bin_edges"]
low, high = edges[labels.index(band)], edges[labels.index(band) + 1]

# --- Show the result -------------------------------------------------------
st.divider()
st.metric("Estimated price", rupees(price))
st.write(f"This looks like a **{band.lower()}-budget** car "
         f"— similar ones sell for **{rupees(low)} – {rupees(high)}**.")

st.caption("Estimate only, based on past Cars24 listings — not a guaranteed price.")
