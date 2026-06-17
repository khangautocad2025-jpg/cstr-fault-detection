# evaluate.py
import pandas as pd
import joblib
import os
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH      = os.path.join(BASE_DIR, 'model.pkl')
CLASSIFIER_PATH = os.path.join(BASE_DIR, 'fault_classifier.pkl')
FAULT_PATH      = os.path.join(BASE_DIR, '..', 'data', 'fault_scenarios.csv')

features = ['Ca1', 'Cb1', 'T1', 'Ca2', 'Cb2', 'T2', 'Ca3', 'Cb3', 'T3']

fault_df    = pd.read_csv(FAULT_PATH)
X_test      = fault_df[features].values
y_test      = fault_df['fault'].values
true_labels = ['anomaly' if f != 'none' else 'normal' for f in y_test]

# ── Evaluate Isolation Forest ─────────────────────────────────────────────────
model       = joblib.load(MODEL_PATH)
predictions = model.predict(X_test)
pred_labels = ['anomaly' if p == -1 else 'normal' for p in predictions]

print("=== Isolation Forest Evaluation ===")
print(classification_report(true_labels, pred_labels))

cm1 = confusion_matrix(true_labels, pred_labels, labels=['normal', 'anomaly'])
ConfusionMatrixDisplay(cm1, display_labels=['normal', 'anomaly']).plot(cmap='Blues')
plt.title('Isolation Forest — contamination=0.222')
plt.savefig(os.path.join(BASE_DIR, '..', 'data', 'eval_isolation_forest.png'), dpi=150)
plt.show()

# ── Evaluate Decision Tree ────────────────────────────────────────────────────
classifier  = joblib.load(CLASSIFIER_PATH)
y_pred      = classifier.predict(X_test)

print("\n=== Decision Tree Fault Classifier Evaluation ===")
print(classification_report(y_test, y_pred))

cm2 = confusion_matrix(y_test, y_pred,
      labels=['none', 'coolant_failure', 'feed_spike', 'flow_drop'])
ConfusionMatrixDisplay(cm2,
      display_labels=['none', 'coolant_failure', 'feed_spike', 'flow_drop']
      ).plot(cmap='Blues', xticks_rotation=45)
plt.title('Decision Tree — Fault Classifier')
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, '..', 'data', 'eval_decision_tree.png'), dpi=150)
plt.show()