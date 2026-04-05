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

print("Dataset size:", df.shape)

# -------------------------------
# Features & Labels
# -------------------------------
X = df[["struct_score", "text_score", "image_score"]]
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
model = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42)
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
joblib.dump(model, "tamper_model_v1.pkl")

# --------------------------------
# Rule-based Accuracy
# --------------------------------
def rule_based(row):
    if row["final_score"] >= 0.5:
        return 1
    return 0

df["rule_pred"] = df.apply(rule_based, axis=1)

rule_acc = accuracy_score(df["label"], df["rule_pred"])

print("\nRule-Based Accuracy:", round(rule_acc * 100, 2), "%")

# -------------------------------
# Feature Importance Plot
# -------------------------------
importances = model.feature_importances_
features = X.columns

plt.bar(features, importances)
plt.title("Feature Importance")
plt.show()
