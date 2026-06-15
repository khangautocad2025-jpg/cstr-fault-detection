# train.py
import pandas as pd
import joblib
import os
from sklearn.ensemble import IsolationForest

# Always find paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'normal_operation.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')

# Load normal operation data
normal_df = pd.read_csv(DATA_PATH)

features = ['Ca1', 'Cb1', 'T1', 'Ca2', 'Cb2', 'T2', 'Ca3', 'Cb3', 'T3']
X_train = normal_df[features].values

# Train final model
model = IsolationForest(
    n_estimators=100,
    contamination=0.222,
    random_state=42
)
model.fit(X_train)

# Save
joblib.dump(model, MODEL_PATH)
print("Model trained and saved!")
print(f"Contamination: {model.contamination}")