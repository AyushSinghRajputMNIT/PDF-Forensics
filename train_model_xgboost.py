import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

import joblib

# -------------------------------
# Load Data
# -------------------------------
df = pd.read_csv("features.csv")

print("Dataset size:", df.shape)

# -------------------------------
# Create GROUPS
# -------------------------------
df["group"] = df["pdf_name"].apply(
    lambda x: x.replace("_tampered", "").replace(".pdf", "")
)

# -------------------------------
# 🔥 FULL FEATURE SET (IMPORTANT)
# -------------------------------
FEATURES = [
    "struct_score",
    "image_score",

    "ocr_similarity",
    "ocr_error_ratio",
    "font_anomaly_ratio",
    "overlap_density",
    "max_local_overlap",

    "overlap_severity",
    "ocr_layout_mismatch",
    "font_ocr_mix",
    "normalized_overlap",
    "relative_ocr_drop",

    # 🔥 strong features (previously missing)
    "struct_text_conflict",
    "image_text_conflict",
    "ocr_noise_weighted",
    "extreme_overlap_flag",
    "cleanliness_score",

    "tamper_signal",
    "tamper_ratio",
]

X = df[FEATURES].fillna(0)
y = df["label"]
groups = df["group"]

# -------------------------------
# GroupKFold Split (FIXED)
# -------------------------------
gkf = GroupKFold(n_splits=5)
splits = list(gkf.split(X, y, groups))

# Fold assignment
test_idx = splits[0][1]
val_idx  = splits[1][1]

train_idx = np.setdiff1d(
    np.arange(len(X)),
    np.concatenate([test_idx, val_idx])
)

X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
X_val, y_val     = X.iloc[val_idx], y.iloc[val_idx]
X_test, y_test   = X.iloc[test_idx], y.iloc[test_idx]

print("\nSplit sizes:")
print("Train:", len(X_train))
print("Validation:", len(X_val))
print("Test:", len(X_test))

print("\nLabel distribution:")
print(df["label"].value_counts())

# -------------------------------
# Models
# -------------------------------
rf_model = RandomForestClassifier(
    n_estimators=400,
    max_depth=10,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

xgb_model = XGBClassifier(
    n_estimators=600,
    max_depth=5,
    learning_rate=0.03,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_alpha=1.0,
    reg_lambda=2.0,
    early_stopping_rounds=40
)

# -------------------------------
# Train
# -------------------------------
print("\n=== Training Random Forest ===")
rf_model.fit(X_train, y_train)

print("\n=== Training XGBoost ===")
xgb_model.fit(
    X_train,
    y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

# -------------------------------
# Evaluation
# -------------------------------
def evaluate(model, X, y, name):
    pred = model.predict(X)

    print(f"\n===== {name} =====")
    print("Accuracy:", round(accuracy_score(y, pred) * 100, 2), "%")
    print("\nClassification Report:")
    print(classification_report(y, pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y, pred))


# -------------------------------
# Validation
# -------------------------------
print("\n\n🔍 VALIDATION PERFORMANCE")
evaluate(rf_model, X_val, y_val, "RF Validation")
evaluate(xgb_model, X_val, y_val, "XGB Validation")

# -------------------------------
# Test
# -------------------------------
print("\n\n🚀 FINAL TEST PERFORMANCE")
evaluate(rf_model, X_test, y_test, "RF Test")
evaluate(xgb_model, X_test, y_test, "XGB Test")

# -------------------------------
# Select Best Model
# -------------------------------
rf_acc  = accuracy_score(y_val, rf_model.predict(X_val))
xgb_acc = accuracy_score(y_val, xgb_model.predict(X_val))

if xgb_acc >= rf_acc:
    best_model = xgb_model
    model_name = "xgboost"
else:
    best_model = rf_model
    model_name = "random_forest"

joblib.dump(best_model, "tamper_model_v4.pkl")

print(f"\n✔ Saved best model: {model_name}")

# -------------------------------
# Feature Importance
# -------------------------------
print("\n=== FEATURE IMPORTANCE ===")

importances = best_model.feature_importances_

for name, score in sorted(zip(FEATURES, importances), key=lambda x: -x[1]):
    print(f"{name}: {round(score, 4)}")