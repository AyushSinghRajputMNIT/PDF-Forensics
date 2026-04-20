import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


# -------------------------------
# Load Data
# -------------------------------
df = pd.read_csv("features.csv")
print("Dataset size:", df.shape)


# -------------------------------
# Grouping (VERY IMPORTANT)
# -------------------------------
df["group"] = df["pdf_name"].apply(
    lambda x: x.replace("_tampered", "").replace(".pdf", "")
)


# -------------------------------
# Feature Selection
# -------------------------------
FEATURES = [
    # Structural
    "struct_score",

    # 🔥 Granular image features (important fix)
    "image_score_signature",
    "image_score_stamp",
    "image_score_logo",
    "image_score_internal",
    "avg_ela_variance",

    # Textual
    "ocr_similarity",
    "ocr_error_ratio",
    "font_anomaly_ratio",
    "overlap_density",
    "max_local_overlap",
    "overlap_severity",
    "ocr_layout_mismatch",
    "font_ocr_mix",

    # Derived
    "normalized_overlap",
    "relative_ocr_drop",
    "struct_text_conflict",
    "image_text_conflict",
    "ocr_noise_weighted",
    # "extreme_overlap_flag",
    "cleanliness_score",

    # Structural deep
    "num_startxref",
    # "objects_with_multiple_revisions",
    "stream_length_mismatch_count",
    "metadata_mismatch",
    "time_gap_seconds"
]


# -------------------------------
# Prepare Data
# -------------------------------
X = df[FEATURES].copy()
y = df["label"]
groups = df["group"]

# Fill missing
X = X.fillna(0)


# -------------------------------
# 🔥 Feature Normalization
# -------------------------------
# Log scale heavy-tailed features
log_features = [
    "overlap_severity",
    "max_local_overlap",
    "time_gap_seconds",
    "stream_length_mismatch_count"
]

for col in log_features:
    if col in X.columns:
        X[col] = np.log1p(X[col])

# Optional clipping (extra safety)
X = X.clip(-10, 10)


# -------------------------------
# Split (GroupKFold)
# -------------------------------
gkf = GroupKFold(n_splits=5)
splits = list(gkf.split(X, y, groups))

train_idx = np.concatenate([splits[i][1] for i in range(2, 5)])
val_idx   = splits[1][1]
test_idx  = splits[0][1]

X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
X_val, y_val     = X.iloc[val_idx], y.iloc[val_idx]
X_test, y_test   = X.iloc[test_idx], y.iloc[test_idx]

print("\nSplit sizes:")
print("Train:", len(X_train))
print("Validation:", len(X_val))
print("Test:", len(X_test))


# -------------------------------
# Models
# -------------------------------
rf_model = RandomForestClassifier(
    n_estimators=400,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)

xgb_model = XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42
)


# -------------------------------
# Train
# -------------------------------
print("\n=== Training Random Forest ===")
rf_model.fit(X_train, y_train)

print("\n=== Training XGBoost ===")
xgb_model.fit(X_train, y_train)


# -------------------------------
# Validation Predictions
# -------------------------------
rf_val_prob  = rf_model.predict_proba(X_val)[:, 1]
xgb_val_prob = xgb_model.predict_proba(X_val)[:, 1]


# -------------------------------
# 🔥 Learn best ensemble weight + threshold
# -------------------------------
best_acc = 0
best_w = 0.5
best_thr = 0.5

for w in np.arange(0.0, 1.01, 0.05):
    combined = w * xgb_val_prob + (1 - w) * rf_val_prob

    for t in np.arange(0.3, 0.71, 0.02):
        pred = (combined > t).astype(int)
        acc = accuracy_score(y_val, pred)

        if acc > best_acc:
            best_acc = acc
            best_w = w
            best_thr = t

print(f"\n🔥 Best Ensemble Weight (XGB): {best_w}")
print(f"🔥 Best Threshold: {round(best_thr, 2)}")
print(f"Validation Accuracy (Ensemble): {round(best_acc*100,2)}%")


# -------------------------------
# Evaluation Function
# -------------------------------
def evaluate(name, y_true, prob):
    pred = (prob > best_thr).astype(int)

    print(f"\n===== {name} =====")
    print("Accuracy:", round(accuracy_score(y_true, pred) * 100, 2), "%")
    print("AUC:", round(roc_auc_score(y_true, prob), 4))

    print("\nClassification Report:")
    print(classification_report(y_true, pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, pred))


# -------------------------------
# Test Evaluation
# -------------------------------
rf_test_prob  = rf_model.predict_proba(X_test)[:, 1]
xgb_test_prob = xgb_model.predict_proba(X_test)[:, 1]

ensemble_test_prob = best_w * xgb_test_prob + (1 - best_w) * rf_test_prob

print("\n\n🚀 FINAL TEST PERFORMANCE")

evaluate("RF Test", y_test, rf_test_prob)
evaluate("XGB Test", y_test, xgb_test_prob)
evaluate("ENSEMBLE Test", y_test, ensemble_test_prob)


# -------------------------------
# Save Models
# -------------------------------
joblib.dump(rf_model, "rf_model_with_img.pkl")
joblib.dump(xgb_model, "xgb_model_with_img.pkl")

ensemble_config = {
    "weight_xgb": best_w,
    "threshold": best_thr,
    "features": FEATURES
}

joblib.dump(ensemble_config, "ensemble_config_with_img.pkl")

print("\n✔ Saved:")
print("- rf_model_with_img.pkl")
print("- xgb_model_with_img.pkl")
print("- ensemble_config_with_img.pkl")


# -------------------------------
# Feature Importance (XGB)
# -------------------------------
print("\n=== FEATURE IMPORTANCE (XGB) ===")

importances = xgb_model.feature_importances_

fi = pd.DataFrame({
    "feature": FEATURES,
    "importance": importances
}).sort_values(by="importance", ascending=False)

print(fi)

# Save to CSV (for report)
fi.to_csv("feature_importance.csv", index=False)

print("\n✔ Saved feature_importance.csv")