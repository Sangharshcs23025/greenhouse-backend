"""
Trains a RandomForest classifier to predict growth risk (low/medium/high)
per crop, using synthetic data generated around known optimal ranges.

DESIGNED FOR EXTENSION: to add a new crop, just add an entry to
CROP_PROFILES below and rerun this script — no other code changes needed.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

CROP_PROFILES = {
    "tomato": {
        "temp_range": (18, 27),
        "humidity_range": (60, 80),
        "soil_moisture_range": (60, 80),
        "light_range": (400, 800),
    },
}

SAMPLES_PER_CROP = 3000


def generate_synthetic_data():
    rows = []
    for crop, profile in CROP_PROFILES.items():
        t_lo, t_hi = profile["temp_range"]
        h_lo, h_hi = profile["humidity_range"]
        s_lo, s_hi = profile["soil_moisture_range"]
        l_lo, l_hi = profile["light_range"]

        for _ in range(SAMPLES_PER_CROP):
            in_range = np.random.rand() < 0.6

            if in_range:
                temp = np.random.uniform(t_lo, t_hi)
                hum = np.random.uniform(h_lo, h_hi)
                soil = np.random.uniform(s_lo, s_hi)
                light = np.random.uniform(l_lo, l_hi)
            else:
                temp = np.random.uniform(t_lo - 10, t_hi + 10)
                hum = np.random.uniform(max(0, h_lo - 25), min(100, h_hi + 25))
                soil = np.random.uniform(max(0, s_lo - 30), min(100, s_hi + 30))
                light = np.random.uniform(max(0, l_lo - 200), l_hi + 300)

            out_of_range = sum([
                not (t_lo <= temp <= t_hi),
                not (h_lo <= hum <= h_hi),
                not (s_lo <= soil <= s_hi),
                not (l_lo <= light <= l_hi),
            ])
            if out_of_range == 0:
                risk = "low"
            elif out_of_range == 1:
                risk = "medium"
            else:
                risk = "high"

            rows.append([crop, temp, hum, soil, light, risk])

    return pd.DataFrame(rows, columns=["crop", "temperature", "humidity", "soil_moisture", "light_intensity", "risk"])


def main():
    print("Generating synthetic training data...")
    df = generate_synthetic_data()
    print(f"Generated {len(df)} rows across {len(CROP_PROFILES)} crop(s).")

    crop_encoder = LabelEncoder()
    df["crop_encoded"] = crop_encoder.fit_transform(df["crop"])

    risk_encoder = LabelEncoder()
    df["risk_encoded"] = risk_encoder.fit_transform(df["risk"])

    X = df[["crop_encoded", "temperature", "humidity", "soil_moisture", "light_intensity"]]
    y = df["risk_encoded"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    print("\nModel evaluation:")
    print(classification_report(y_test, model.predict(X_test), target_names=risk_encoder.classes_))

    os.makedirs("app/ml", exist_ok=True)
    joblib.dump(model, "app/ml/greenhouse_model.joblib")
    joblib.dump(crop_encoder, "app/ml/crop_encoder.joblib")
    joblib.dump(risk_encoder, "app/ml/risk_encoder.joblib")
    print("\nSaved model + encoders to app/ml/")


if __name__ == "__main__":
    main()