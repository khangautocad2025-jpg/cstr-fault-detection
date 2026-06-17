# train.py
import pandas as pd
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
NORMAL_PATH     = os.path.join(BASE_DIR, '..', 'data', 'normal_operation.csv')
FAULT_PATH      = os.path.join(BASE_DIR, '..', 'data', 'fault_scenarios.csv')
MODEL_PATH      = os.path.join(BASE_DIR, 'model.pkl')
CLASSIFIER_PATH = os.path.join(BASE_DIR, 'fault_classifier.pkl')

features = ['Ca1', 'Cb1', 'T1', 'Ca2', 'Cb2', 'T2', 'Ca3', 'Cb3', 'T3']

# ── Train Isolation Forest ────────────────────────────────────────────────────
normal_df = pd.read_csv(NORMAL_PATH)
X_train   = normal_df[features].values

model = IsolationForest(
    n_estimators=100,
    contamination=0.222,
    random_state=42
)
model.fit(X_train)
joblib.dump(model, MODEL_PATH)
print("Isolation Forest saved → model.pkl")
print(f"Contamination: {model.contamination}")

# ── Train Decision Tree Classifier ────────────────────────────────────────────
fault_df = pd.read_csv(FAULT_PATH)
X        = fault_df[features].values
y        = fault_df['fault'].values

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

classifier = DecisionTreeClassifier(
    max_depth=5,
    min_samples_leaf=10,
    class_weight='balanced',
    random_state=42
)
classifier.fit(X_tr, y_tr)
joblib.dump(classifier, CLASSIFIER_PATH)
print("Decision Tree saved → fault_classifier.pkl")
print(f"Tree depth:  {classifier.get_depth()}")
print(f"Leaves:      {classifier.get_n_leaves()}")
print(f"Classes:     {list(classifier.classes_)}")