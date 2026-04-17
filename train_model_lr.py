import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import joblib

# -------------------------------
# Load Data
# -------------------------------
df = pd.read_csv("features.csv")
print("Dataset size:", df.shape)

# -------------------------------
# Create GROUPS (IMPORTANT)
# -------------------------------
# Groups = base PDF name (remove "_tampered")
df["group"] = df["pdf_name"].str.replace("_tampered", "", regex=False)

# -------------------------------
# Features & Labels
# -------------------------------
FEATURES = [
    "struct_score",
    "ocr_similarity",
    "ocr_error_ratio",
    "font_anomaly_ratio",
    "overlap_density",
    "max_local_overlap",
    "tamper_signal",
    "is_suspicious"
]

X = df[FEATURES]
y = df["label"]
groups = df["group"]

# -------------------------------
# Train / Val / Test Split (GROUP-AWARE)
# -------------------------------
gss = GroupShuffleSplit(n_splits=1, test_size=0.4, random_state=42)
train_idx, temp_idx = next(gss.split(X, y, groups))

X_train, X_temp = X.iloc[train_idx], X.iloc[temp_idx]
y_train, y_temp = y.iloc[train_idx], y.iloc[temp_idx]
groups_train, groups_temp = groups.iloc[train_idx], groups.iloc[temp_idx]

# Split temp into val + test
gss2 = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
val_idx, test_idx = next(gss2.split(X_temp, y_temp, groups_temp))

X_val, X_test = X_temp.iloc[val_idx], X_temp.iloc[test_idx]
y_val, y_test = y_temp.iloc[val_idx], y_temp.iloc[test_idx]

print("\nSplit sizes:")
print("Train:", X_train.shape[0])
print("Validation:", X_val.shape[0])
print("Test:", X_test.shape[0])

# -------------------------------
# Cross Validation (GROUP K-FOLD)
# -------------------------------
print("\n=== GROUP K-FOLD CV (5-Fold) ===")

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        C=0.3
    ))
])

gkf = GroupKFold(n_splits=5)

cv_scores = []

for fold, (train_idx, val_idx) in enumerate(gkf.split(X_train, y_train, groups_train)):
    X_tr, X_va = X_train.iloc[train_idx], X_train.iloc[val_idx]
    y_tr, y_va = y_train.iloc[train_idx], y_train.iloc[val_idx]

    pipeline.fit(X_tr, y_tr)
    preds = pipeline.predict(X_va)

    acc = accuracy_score(y_va, preds)
    cv_scores.append(acc)

    print(f"Fold {fold+1}: {round(acc, 4)}")

print("Mean CV Accuracy:", round(np.mean(cv_scores) * 100, 2), "%")

# -------------------------------
# Final Training (on TRAIN)
# -------------------------------
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression(
    class_weight="balanced",
    max_iter=2000,
    C=0.3
)

model.fit(X_train_scaled, y_train)

# -------------------------------
# Validation Evaluation
# -------------------------------
val_pred = model.predict(X_val_scaled)

print("\n===== VALIDATION RESULTS =====")
print("Accuracy:", round(accuracy_score(y_val, val_pred) * 100, 2), "%")
print("\nClassification Report:")
print(classification_report(y_val, val_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_val, val_pred))

# -------------------------------
# Final Test Evaluation
# -------------------------------
test_pred = model.predict(X_test_scaled)

print("\n===== FINAL TEST RESULTS =====")
print("Accuracy:", round(accuracy_score(y_test, test_pred) * 100, 2), "%")
print("\nClassification Report:")
print(classification_report(y_test, test_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, test_pred))

# -------------------------------
# Save Model + Scaler
# -------------------------------
joblib.dump(model, "tamper_model_final.pkl")
joblib.dump(scaler, "scaler.pkl")

print("\n✔ Model and scaler saved.")

# -------------------------------
# Feature Importance
# -------------------------------
print("\n=== FEATURE IMPORTANCE ===")
for name, coef in zip(FEATURES, model.coef_[0]):
    print(f"{name}: {round(coef, 3)}")