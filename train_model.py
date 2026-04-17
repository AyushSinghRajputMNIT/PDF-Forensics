import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import joblib

# -------------------------------
# Load Data
# -------------------------------
df = pd.read_csv("features.csv")

# -------------------------------
# Balance Dataset (IMPORTANT)
# -------------------------------
df_genuine = df[df["label"] == 0]
df_tampered = df[df["label"] == 1]

print(f"Original -> Genuine: {len(df_genuine)}, Tampered: {len(df_tampered)}")

# Downsample tampered to match genuine
df_tampered_sampled = df_tampered.sample(len(df_genuine), random_state=42)

# Combine and shuffle
df_balanced = pd.concat([df_genuine, df_tampered_sampled])
df = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"Balanced -> Genuine: {sum(df['label']==0)}, Tampered: {sum(df['label']==1)}")

print("Dataset size:", df.shape)

print("\n=== STRUCT SCORE ANALYSIS ===")
print(df.groupby("label")["struct_score"].mean())

# -------------------------------
# Features & Labels (UPDATED)
# -------------------------------
X = df[
    [
        "struct_score",
        "ocr_similarity",
        "ocr_error_ratio",
        "font_anomaly_ratio",
        "overlap_density",
        "max_local_overlap",
        # "overlap_severity",
        # "ocr_layout_mismatch",
        # "font_ocr_mix",
        "tamper_signal",
    ]
]

y = df["label"]

# -------------------------------
# Train-Test Split
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------
# Train Model
# -------------------------------
model = RandomForestClassifier(
    n_estimators=200,          # 🔥 increased trees
    class_weight="balanced",   # keep this
    random_state=42,
    min_samples_leaf=3,  
)

model.fit(X_train, y_train)

# -------------------------------
# Predictions
# -------------------------------
y_pred = model.predict(X_test)

# -------------------------------
# Evaluation
# -------------------------------
accuracy = accuracy_score(y_test, y_pred)

print("\n===== RESULTS =====")
print("Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# --------------------------------
# Saving Model
# --------------------------------
joblib.dump(model, "tamper_model_v3.pkl")

# -------------------------------
# Feature Importance Plot
# -------------------------------
importances = model.feature_importances_
features = X.columns

print("\nFeature Importance:")
for f, imp in zip(features, importances):
    print(f"{f}: {round(imp, 3)}")

plt.bar(features, importances)
plt.title("Feature Importance")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()