import json
import joblib
import pandas as pd

pm = joblib.load("models/price_model.pkl")
rm = joblib.load("models/range_model.pkl")
cols = json.load(open("models/feature_columns.json"))
rc = json.load(open("models/range_config.json"))

LAKH = 100_000
CR = 100


def fmt(v):
    if v >= CR:
        return f"Rs {v / CR:.2f} Cr"
    if v >= 1:
        return f"Rs {v:.2f} Lakhs"
    return f"Rs {v * LAKH:,.0f}"


print("format check: 4.75 ->", fmt(4.75), "| 0.45 ->", fmt(0.45), "| 145 ->", fmt(145))
print("range_config edges (Lakhs):", rc["bin_edges"])

SELLER = {"Dealer": [], "Individual": ["Individual"], "Trustmark Dealer": ["Trustmark Dealer"]}
FUEL = {"Petrol": ["Petrol"], "Diesel": ["Diesel"], "Electric": ["Electric"], "LPG": ["LPG"], "CNG": []}
TRANS = {"Manual": ["Manual"], "Automatic": []}
SEATS = {"5": ["Seats_5"], "More than 5": ["Seats_Above_5"], "Fewer than 5": []}


def make_row(make, model, nums, seller, fuel, trans, seats):
    r = {c: 0 for c in cols}
    r.update(nums)
    r["make"] = make.upper()
    r["model"] = model.upper()
    for f in SELLER[seller] + FUEL[fuel] + TRANS[trans] + SEATS[seats]:
        if f in r:
            r[f] = 1
    return pd.DataFrame([r])[cols]


tests = [
    ("MARUTI", "SWIFT VXI", dict(km_driven=30000, mileage=18.0, engine=1200, max_power=80.0, age=5), "Individual", "Petrol", "Manual", "5"),
    ("HYUNDAI", "CRETA", dict(km_driven=40000, mileage=17.0, engine=1500, max_power=113.0, age=4), "Dealer", "Diesel", "Automatic", "5"),
    ("BMW", "X5", dict(km_driven=50000, mileage=12.0, engine=3000, max_power=265.0, age=6), "Dealer", "Diesel", "Automatic", "5"),
    ("MARUTI", "WAGON R LXI CNG", dict(km_driven=60000, mileage=26.0, engine=1000, max_power=58.0, age=8), "Individual", "CNG", "Manual", "5"),
]

print()
for mk, mo, nums, se, fu, tr, sa in tests:
    X = make_row(mk, mo, nums, se, fu, tr, sa)
    p = float(pm.predict(X)[0])
    b = str(rm.predict(X)[0])
    print(f"{mk} {mo:18s} {se:16s} {fu:8s} -> {fmt(p):>14s}  | band={b}")

print()
print("All predictions ran without error.")
