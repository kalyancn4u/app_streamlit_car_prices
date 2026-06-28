"""
Car Price & Range Predictor - Streamlit front-end
==================================================

Loads the artifacts produced by ``train_model.py`` and turns a handful of car
specifications into:

    * an **exact price** estimate (RandomForestRegressor), and
    * a **price band** - Low / Medium / High - with its rupee interval
      (RandomForestClassifier).

Design choices that fix the original app (see DESIGN_NOTES.md):

  * Prices are handled in **Lakhs** end-to-end - the models were trained on a
    ``selling_price`` column expressed in Lakhs, so ``format_lakhs`` and the
    range gauge interpret every value as Lakhs (1 Lakh = Rs 100,000,
    100 Lakhs = 1 Crore).
  * The UI is **data-driven**: makes, models, slider ranges and the categorical
    options (including the encoding baselines "Dealer" and "CNG") all come from
    ``models/metadata.json`` rather than being hard-coded, so the form can never
    drift out of sync with the trained model.

Run:  streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

MODELS_DIR = Path("models")
PRICE_MODEL_PATH = MODELS_DIR / "price_model.pkl"
RANGE_MODEL_PATH = MODELS_DIR / "range_model.pkl"
FEATURE_COLUMNS_PATH = MODELS_DIR / "feature_columns.json"
RANGE_CONFIG_PATH = MODELS_DIR / "range_config.json"
METADATA_PATH = MODELS_DIR / "metadata.json"

LAKH = 100_000          # 1 Lakh  = Rs 100,000
CRORE_IN_LAKHS = 100    # 1 Crore = 100 Lakhs

# Maps a UI choice -> which pre-encoded flag columns must be set to 1.
# An empty list means "this option is the dropped baseline" (all flags 0),
# which is exactly how the dataset was one-hot encoded during training.
SELLER_FLAGS: Dict[str, List[str]] = {
    "Dealer": [],
    "Individual": ["Individual"],
    "Trustmark Dealer": ["Trustmark Dealer"],
}
FUEL_FLAGS: Dict[str, List[str]] = {
    "Petrol": ["Petrol"],
    "Diesel": ["Diesel"],
    "Electric": ["Electric"],
    "LPG": ["LPG"],
    "CNG": [],  # baseline
}
TRANSMISSION_FLAGS: Dict[str, List[str]] = {
    "Manual": ["Manual"],
    "Automatic": [],  # baseline
}
SEATS_FLAGS: Dict[str, List[str]] = {
    "5": ["Seats_5"],
    "More than 5": ["Seats_Above_5"],
    "Fewer than 5": [],  # baseline
}

# Presentation metadata for the numeric sliders (labels live here, bounds in
# metadata.json). Keyed by the feature name used by the model.
NUMERIC_UI = {
    "age":       {"label": "Age",        "icon": "📅", "unit": "years", "help": "How old the car is."},
    "km_driven": {"label": "Kilometres driven", "icon": "🛣️", "unit": "km", "help": "Total distance on the odometer."},
    "mileage":   {"label": "Mileage",    "icon": "⛽", "unit": "km/l", "help": "Fuel efficiency."},
    "engine":    {"label": "Engine",     "icon": "🔧", "unit": "cc",   "help": "Engine displacement."},
    "max_power": {"label": "Max power",  "icon": "⚡", "unit": "bhp",  "help": "Peak power output."},
}

# Colour per price band (neutral, not good/bad).
BAND_COLORS = {"Low": "#10b981", "Medium": "#6366f1", "High": "#ec4899"}


# ---------------------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Car Price & Range Predictor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 1100px; }

      .hero {
        background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        border-radius: 18px; padding: 26px 32px; color: #fff;
        box-shadow: 0 12px 32px rgba(79,70,229,.28); margin-bottom: 6px;
      }
      .hero h1 { margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing:-.5px; }
      .hero p  { margin: 6px 0 0; opacity: .92; font-size: 1.02rem; }

      .result-card {
        border-radius: 16px; padding: 22px 24px; color: #fff;
        box-shadow: 0 10px 28px rgba(0,0,0,.12); height: 100%;
      }
      .result-card .label { margin:0; font-weight:500; opacity:.92; font-size:1rem; }
      .result-card .value { margin:6px 0 0; font-weight:800; line-height:1.1; }
      .card-price { background: linear-gradient(135deg,#2563eb 0%,#4f46e5 100%); }
      .card-range { background: linear-gradient(135deg,#db2777 0%,#9333ea 100%); }

      .gauge-track {
        position: relative; display: flex; width: 100%; height: 58px;
        border-radius: 12px; overflow: hidden; margin-top: 6px;
        border: 1px solid rgba(0,0,0,.06);
      }
      .gauge-seg {
        flex: 1; display: flex; flex-direction: column; align-items: center;
        justify-content: center; color: #fff; font-weight: 700; font-size: .9rem;
        text-align: center; line-height: 1.15;
      }
      .gauge-seg small { font-weight: 500; opacity: .9; font-size: .72rem; }
      .gauge-marker {
        position: absolute; top: -7px; transform: translateX(-50%);
        font-size: 1.15rem; filter: drop-shadow(0 2px 2px rgba(0,0,0,.35));
        transition: left .4s ease;
      }
      .gauge-caption { color:#6b7280; font-size:.82rem; margin-top:6px; }

      div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading models...")
def load_models() -> Tuple[Any, Any]:
    return joblib.load(PRICE_MODEL_PATH), joblib.load(RANGE_MODEL_PATH)


@st.cache_data(show_spinner=False)
def load_config() -> Tuple[List[str], Dict, Dict]:
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    range_config = json.loads(RANGE_CONFIG_PATH.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return feature_columns, range_config, metadata


def artifacts_exist() -> bool:
    return all(p.exists() for p in (
        PRICE_MODEL_PATH, RANGE_MODEL_PATH, FEATURE_COLUMNS_PATH,
        RANGE_CONFIG_PATH, METADATA_PATH,
    ))


# ---------------------------------------------------------------------------
# Formatting helpers (everything in Lakhs)
# ---------------------------------------------------------------------------

def format_lakhs(value_lakhs: float) -> str:
    """Render a price (given in Lakhs) using Indian Crore/Lakh/Rupee notation."""
    if value_lakhs >= CRORE_IN_LAKHS:
        return f"₹{value_lakhs / CRORE_IN_LAKHS:.2f} Cr"
    if value_lakhs >= 1:
        return f"₹{value_lakhs:.2f} Lakhs"
    return f"₹{value_lakhs * LAKH:,.0f}"


def band_interval_text(label: str, range_config: Dict) -> str:
    """Human-readable rupee interval for a Low/Medium/High band."""
    labels = range_config["labels"]
    edges = range_config["bin_edges"]
    idx = labels.index(label)
    return f"{format_lakhs(edges[idx])} – {format_lakhs(edges[idx + 1])}"


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------

def build_feature_row(
    *,
    feature_columns: List[str],
    make: str,
    model: str,
    numeric_values: Dict[str, float],
    seller: str,
    fuel: str,
    transmission: str,
    seats: str,
) -> pd.DataFrame:
    """Assemble a single-row DataFrame matching the model's training schema."""
    row: Dict[str, Any] = {col: 0 for col in feature_columns}

    # Numeric features
    for name, value in numeric_values.items():
        row[name] = value

    # Free-text features (uppercased to match the cleaned training data)
    row["make"] = make.strip().upper()
    row["model"] = model.strip().upper()

    # Pre-encoded categorical flags (baselines leave everything at 0)
    for flag in (SELLER_FLAGS[seller] + FUEL_FLAGS[fuel]
                 + TRANSMISSION_FLAGS[transmission] + SEATS_FLAGS[seats]):
        if flag in row:
            row[flag] = 1

    return pd.DataFrame([row])[feature_columns]


def valid_options(meta: Dict, make: str, model: str) -> Dict[str, List[str]]:
    """Fuel / transmission / seats actually seen for this model.

    Falls back model -> make -> every option, so the dropdowns can only ever
    offer combinations that exist in the data (no "Electric Alto"). Options are
    ordered most-common-first.
    """
    by_model = meta.get("model_options", {}).get(make, {}).get(model)
    if by_model:
        return by_model
    by_make = meta.get("make_options", {}).get(make)
    if by_make:
        return by_make
    cat = meta["categorical_features"]
    return {k: cat[k]["options"] for k in ("fuel", "transmission", "seats")}


# ---------------------------------------------------------------------------
# Range gauge
# ---------------------------------------------------------------------------

def marker_percent(price_lakhs: float, edges: List[float]) -> float:
    """Position of the exact price across three equal-width bands (0-100%)."""
    if price_lakhs <= edges[0]:
        return 0.0
    if price_lakhs >= edges[-1]:
        return 100.0
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if lo <= price_lakhs <= hi:
            frac = (price_lakhs - lo) / (hi - lo) if hi > lo else 0.5
            return (i + frac) / (len(edges) - 1) * 100
    return 50.0


def render_gauge(price_lakhs: float, predicted_label: str, range_config: Dict) -> str:
    """Build the HTML for the Low/Medium/High band gauge with a price marker."""
    labels = range_config["labels"]
    edges = range_config["bin_edges"]

    segments = ""
    for i, label in enumerate(labels):
        active = label == predicted_label
        color = BAND_COLORS[label]
        opacity = "1" if active else ".38"
        interval = f"{format_lakhs(edges[i])} – {format_lakhs(edges[i + 1])}"
        segments += (
            f'<div class="gauge-seg" style="background:{color};opacity:{opacity};">'
            f'{label}<small>{interval}</small></div>'
        )

    pct = marker_percent(price_lakhs, edges)
    marker = f'<div class="gauge-marker" style="left:{pct:.1f}%;">🔻</div>'

    return (
        f'<div class="gauge-track">{segments}{marker}</div>'
        f'<div class="gauge-caption">🔻 marks the exact estimate '
        f'({format_lakhs(price_lakhs)}) on the price scale.</div>'
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
      <h1>🚗 Car Price &amp; Range Predictor</h1>
      <p>Estimate the resale value of a used car in Indian Rupees, plus its
         budget band — powered by a Random Forest trained on Cars24 data.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not artifacts_exist():
    st.error("### ⚠️ Model artifacts not found")
    st.markdown(
        "The trained models are missing. Generate them once with:\n\n"
        "```bash\npython train_model.py\n```\n\n"
        "This creates `price_model.pkl`, `range_model.pkl` and the JSON "
        "configuration files inside the `models/` folder."
    )
    st.stop()

price_model, range_model = load_models()
feature_columns, range_config, metadata = load_config()

makes_models: Dict[str, List[str]] = metadata["makes_models"]
numeric_specs: Dict[str, Dict] = metadata["numeric_features"]
categorical: Dict[str, Dict] = metadata["categorical_features"]
metrics: Dict[str, float] = metadata.get("metrics", {})

# ---- Sidebar: context + model quality -------------------------------------
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown(
        "Pick a car's specifications, then **Estimate price** to see its "
        "predicted resale value and price band.\n\n"
        "Two models work together:\n"
        "- a **regressor** for the exact price\n"
        "- a **classifier** for the Low / Medium / High band"
    )
    st.divider()
    st.subheader("📈 Model quality")
    if metrics:
        st.metric("Price accuracy (R²)", f"{metrics.get('price_r2', 0) * 100:.1f}%")
        st.metric("Typical price error (MAE)",
                  format_lakhs(metrics.get("price_mae_lakhs", 0)))
        st.metric("Band accuracy", f"{metrics.get('range_accuracy', 0) * 100:.1f}%")
    st.caption(
        f"Trained on {metadata.get('n_samples', 0):,} cars · "
        f"{len(makes_models)} brands · prices in Lakhs (₹)."
    )

# ---- Inputs: vehicle ------------------------------------------------------
st.subheader("1 · Vehicle")
with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        make_names = list(makes_models.keys())
        default_make = make_names.index("MARUTI") if "MARUTI" in make_names else 0
        make = st.selectbox("🏷️ Make / Brand", options=make_names,
                            index=default_make, help="Manufacturer of the car.")
    with c2:
        model = st.selectbox(
            "🚙 Model", options=makes_models.get(make, []),
            help="Specific variant. The list updates with the selected brand.",
        )

    # Fuel / transmission / seats are limited to what this model actually came
    # with, so an impossible combination can't be selected. Seller is NOT tied
    # to the model (any car can be sold by a dealer or an individual).
    opts = valid_options(metadata, make, model)
    c3, c4, c5, c6 = st.columns(4)
    with c3:
        fuel = st.selectbox("⛽ Fuel", opts["fuel"])
    with c4:
        transmission = st.selectbox("⚙️ Transmission", opts["transmission"])
    with c5:
        seller = st.selectbox("🤝 Seller type", categorical["seller"]["options"])
    with c6:
        seats = st.selectbox("💺 Seats", opts["seats"])
    st.caption("ⓘ Fuel, transmission and seats are limited to this model's real "
               "configurations — they update when you change the model.")

# ---- Inputs: specifications ----------------------------------------------
st.subheader("2 · Specifications")
numeric_values: Dict[str, float] = {}
with st.container(border=True):
    cols = st.columns(len(NUMERIC_UI))
    for col_box, (name, ui) in zip(cols, NUMERIC_UI.items()):
        spec = numeric_specs[name]
        is_int = spec["dtype"] == "int"
        with col_box:
            numeric_values[name] = st.slider(
                f"{ui['icon']} {ui['label']} ({ui['unit']})",
                min_value=spec["min"], max_value=spec["max"],
                value=spec["default"],
                step=int(spec["step"]) if is_int else float(spec["step"]),
                help=ui["help"],
            )

predict = st.button("🔮 Estimate price", type="primary", use_container_width=True)

# ---- Prediction + results -------------------------------------------------
if predict:
    try:
        X = build_feature_row(
            feature_columns=feature_columns,
            make=make, model=model, numeric_values=numeric_values,
            seller=seller, fuel=fuel, transmission=transmission, seats=seats,
        )
        price_lakhs = float(price_model.predict(X)[0])
        price_lakhs = max(price_lakhs, 0.0)
        band_label = str(range_model.predict(X)[0])

        st.subheader("📊 Estimate")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown(
                f'<div class="result-card card-price">'
                f'<p class="label">💰 Estimated price</p>'
                f'<p class="value" style="font-size:2.6rem;">{format_lakhs(price_lakhs)}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with rc2:
            st.markdown(
                f'<div class="result-card card-range">'
                f'<p class="label">🎯 Price band</p>'
                f'<p class="value" style="font-size:2.6rem;">{band_label}</p>'
                f'<p class="label">{band_interval_text(band_label, range_config)}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(render_gauge(price_lakhs, band_label, range_config),
                    unsafe_allow_html=True)

        with st.expander("🔎 Details & model input"):
            st.write(
                f"**Vehicle:** {make.title()} {model.title()}  ·  "
                f"{fuel} · {transmission} · {seller} · {seats} seats"
            )
            st.write(
                f"**Exact estimate:** {format_lakhs(price_lakhs)}  ·  "
                f"**Band:** {band_label} "
                f"({band_interval_text(band_label, range_config)})"
            )
            st.caption("Feature row sent to the model:")
            st.dataframe(X, use_container_width=True, hide_index=True)

        st.success("✅ Done. Adjust any input and estimate again.")

    except Exception as exc:  # pragma: no cover - surfaced to the user
        st.error(f"🚨 Could not produce an estimate: {exc}")

# ---- Footer ---------------------------------------------------------------
st.divider()
st.caption(
    "💡 Estimates are indicative and based on historical Cars24 listings — "
    "use them as guidance, not a guaranteed sale price."
)
