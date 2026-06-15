# evaluate.py
import pandas as pd
import joblib
import os
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Always find paths relative to this file's location
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
DATA_PATH  = os.path.join(BASE_DIR, '..', 'data', 'fault_scenarios.csv')
PLOT_PATH  = os.path.join(BASE_DIR, '..', 'data', 'confusion_matrix_eval.png')

# Load model and test data
model    = joblib.load(MODEL_PATH)
fault_df = pd.read_csv(DATA_PATH)

features    = ['Ca1', 'Cb1', 'T1', 'Ca2', 'Cb2', 'T2', 'Ca3', 'Cb3', 'T3']
X_test      = fault_df[features].values
y_test      = fault_df['fault'].values

# Predict
predictions = model.predict(X_test)
pred_labels = ['anomaly' if p == -1 else 'normal' for p in predictions]
true_labels = ['anomaly' if f != 'none' else 'normal' for f in y_test]

# Report
print("=== Model Evaluation ===")
print(classification_report(true_labels, pred_labels))

# Confusion matrix
cm = confusion_matrix(true_labels, pred_labels, labels=['normal', 'anomaly'])
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['normal', 'anomaly'])
disp.plot(cmap='Blues')
plt.title('Evaluation — contamination=0.222')
plt.savefig(PLOT_PATH, dpi=150)
plt.show()