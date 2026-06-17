# app.py
# ─────────────────────────────────────────────────────────────────────────────
# CSTR Fault Detection — Flask API
# Purpose : Serve the trained Isolation Forest model as a REST API
# Endpoints: GET  /                  → service info
#            POST /predict           → anomaly detection
#            GET  /health            → server health check
#            GET  /sensors/example   → example input reference
# ─────────────────────────────────────────────────────────────────────────────

from flask_cors import CORS
import os
import joblib
import numpy as np
from flask import Flask, request, jsonify
# Flask  → web framework that turns Python functions into API endpoints
# request → reads incoming JSON data from the client
# jsonify → converts Python dicts into JSON responses

# ─── Initialize Flask App ────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
# __name__ tells Flask this is the main application file

# ─── Load Trained Model ──────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
# __file__ = absolute path of app.py itself
# dirname  = strips the filename, gives us the backend/ folder path
# This ensures the model loads correctly regardless of where you run the script from

MODEL_PATH = os.path.join(BASE_DIR, '..', 'model', 'model.pkl')
# '..' moves one level up from backend/ to cstr-fault-detection/
# then into model/model.pkl — the saved Isolation Forest

model = joblib.load(MODEL_PATH)
# joblib.load deserializes model.pkl back into a live sklearn IsolationForest object
# This happens ONCE at startup — not on every request (efficient)

# ── Load Fault Classifier ─────────────────────────────────────────────────────
CLASSIFIER_PATH = os.path.join(BASE_DIR, '..', 'model', 'fault_classifier.pkl')
classifier      = joblib.load(CLASSIFIER_PATH)

# ─── Feature Definition ──────────────────────────────────────────────────────
FEATURES = ['Ca1', 'Cb1', 'T1', 'Ca2', 'Cb2', 'T2', 'Ca3', 'Cb3', 'T3']
# The 9 sensor readings from our 3-tank CSTR series
# Ca = concentration of reactant A, Cb = concentration of B, T = temperature
# Order matters — must match the order used during training in 02_Model.ipynb

# ─── Route 1: Home ───────────────────────────────────────────────────────────
@app.route('/')
def home():
    # GET / → confirms the API is alive and shows available endpoint
    return jsonify({
        "service" : "CSTR Fault Detection API",
        "status"  : "running",
        "endpoint": "POST /predict"
    })

# ─── Route 2: Predict ────────────────────────────────────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    # POST /predict → core endpoint
    # Accepts 9 sensor readings as JSON, returns anomaly status

    data = request.get_json()
    # Parses the incoming HTTP request body as JSON
    # Example input: {"Ca1": 1.25, "T1": 341.5, ...}

    # ── Step 1: Validate — check all 9 sensors are present ───────────────
    missing = [f for f in FEATURES if f not in data]
    # List comprehension: collect any feature names absent from the request
    if missing:
        # Return HTTP 400 Bad Request if any sensor is missing
        # This prevents the model from crashing on incomplete data
        return jsonify({
            "error"  : "Missing sensor readings",
            "missing": missing,
            "message": "Please provide all 9 sensor values"
        }), 400

    # ── Step 2: Build feature array in correct order ──────────────────────
    try:
        X = np.array([[data[f] for f in FEATURES]])
        # Shape: (1, 9) — one sample, nine features
        # FEATURES order enforced here to match training data column order
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # ── Step 3: Run Isolation Forest prediction ───────────────────────────
    prediction    = model.predict(X)[0]
    # Returns -1 (anomaly) or +1 (normal)
    # Isolation Forest flags points that are easy to isolate as anomalies

    anomaly_score = model.decision_function(X)[0]
    # Continuous score: negative = anomalous, positive = normal
    # The further below 0, the more severe the anomaly
    # Example: -0.23 = clear fault, +0.0004 = clearly normal

    # ── Step 4: Format human-readable response ────────────────────────────
    status  = "ANOMALY" if prediction == -1 else "NORMAL"
    message = "⚠️ Fault detected — check reactor immediately!" \
              if prediction == -1 else \
              "✅ Reactor operating normally"

    return jsonify({
        "status"       : status,
        "anomaly_score": round(float(anomaly_score), 4),
        # float() converts numpy float to Python float (JSON serializable)
        # round(4) keeps 4 decimal places for precision
        "message"      : message,
        "sensors"      : data
        # Echo back the input sensors so the client can confirm what was received
    })

# ─── Route 3: Health Check ───────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    # GET /health → lightweight check that server and model are both loaded
    # Used by monitoring tools to verify the service is alive
    return jsonify({
        "status": "running",
        "model" : "loaded"
    })

# ─── Route 4: Example Sensor Input ───────────────────────────────────────────
@app.route('/sensors/example', methods=['GET'])
def example():
    # GET /sensors/example → reference guide for API users
    # Shows exactly what JSON to send to /predict
    # Removes the need to memorize sensor names and value ranges
    return jsonify({
        "description": "Example input for /predict",
        "normal_example": {
            # Values near steady-state from normal_operation.csv
            "Ca1": 1.25, "Cb1": 0.45, "T1": 339.8,
            "Ca2": 0.81, "Cb2": 0.62, "T2": 339.6,
            "Ca3": 0.50, "Cb3": 0.68, "T3": 339.4
        },
        
        "fault_example": {
            # Elevated temperatures simulating coolant failure
            "Ca1": 1.25, "Cb1": 0.45, "T1": 341.5,
            "Ca2": 0.81, "Cb2": 0.62, "T2": 341.2,
            "Ca3": 0.50, "Cb3": 0.68, "T3": 340.8
        }
    })

# ─── Route 5: Diagnose ───────────────────────────────────────────────────────
@app.route('/diagnose', methods=['POST'])
def diagnose():
    """
    Two-stage pipeline:
    Stage 1 — Isolation Forest: is this normal or anomaly?
    Stage 2 — Decision Tree:    if anomaly, which fault type?
    """
    data = request.get_json()

    # ── Validate ──────────────────────────────────────────────────────────
    missing = [f for f in FEATURES if f not in data]
    if missing:
        return jsonify({
            "error"  : "Missing sensor readings",
            "missing": missing
        }), 400

    # ── Build feature array ───────────────────────────────────────────────
    X = np.array([[data[f] for f in FEATURES]])

    # ── Stage 1: Isolation Forest ─────────────────────────────────────────
    prediction    = model.predict(X)[0]
    anomaly_score = model.decision_function(X)[0]
    is_anomaly    = prediction == -1

    # ── Stage 2: Decision Tree (only if anomaly detected) ─────────────────
    if is_anomaly:
        fault_type  = classifier.predict(X)[0]
        fault_proba = classifier.predict_proba(X)[0]
        confidence  = round(float(max(fault_proba) * 100), 1)

        # Map fault type to human readable description
        fault_descriptions = {
            'coolant_failure': 'Cooling jacket failure — heat removal compromised',
            'feed_spike'     : 'Feed concentration surge — excess reactant entering tank 1',
            'flow_drop'      : 'Flow rate reduction — residence time increasing',
            'none'           : 'No specific fault pattern identified'
        }

        return jsonify({
            "status"          : "ANOMALY",
            "anomaly_score"   : round(float(anomaly_score), 4),
            "fault_type"      : fault_type,
            "fault_confidence": confidence,
            "description"     : fault_descriptions.get(fault_type, "Unknown fault"),
            "affected_sensors": get_affected_sensors(fault_type, data),
            "recommended_action": get_action(fault_type),
            "sensors"         : data
        })

    # ── Normal operation ──────────────────────────────────────────────────
    return jsonify({
        "status"      : "NORMAL",
        "anomaly_score": round(float(anomaly_score), 4),
        "fault_type"  : "none",
        "description" : "All reactor parameters within normal operating range",
        "sensors"     : data
    })


def get_affected_sensors(fault_type, data):
    """Returns which sensors are showing abnormal readings."""
    affected = {}
    normal   = {
        'T1': 339.8, 'T2': 339.6, 'T3': 339.4,
        'Ca1': 1.25, 'Ca2': 0.81, 'Ca3': 0.50
    }
    for sensor, baseline in normal.items():
        deviation = abs(data[sensor] - baseline)
        if deviation > 0.1:
            affected[sensor] = {
                "current" : round(data[sensor], 4),
                "baseline": baseline,
                "deviation": round(deviation, 4)
            }
    return affected


def get_action(fault_type):
    """Returns recommended operator action for each fault type."""
    actions = {
        'coolant_failure': [
            "Check cooling water supply valve",
            "Inspect heat exchanger for fouling",
            "Monitor T1 — if exceeding 341K initiate emergency cooling",
            "Consider feed reduction to lower heat generation"
        ],
        'feed_spike'     : [
            "Check feed control valve position",
            "Inspect feed concentration analyzer",
            "Reduce feed flow rate by 20% immediately",
            "Monitor Ca1 and T1 for thermal runaway signs"
        ],
        'flow_drop'      : [
            "Check pump operation and flow meters",
            "Inspect feed line for blockage or valve failure",
            "Monitor residence time — increasing τ raises conversion",
            "Verify cooling capacity matches increased reaction time"
        ],
        'none'           : ["Continue monitoring — unclassified anomaly detected"]
    }
    return actions.get(fault_type, ["Contact process engineer immediately"])

# ─── Start Server ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
    # debug=True  → auto-restarts when you save changes to app.py
    # port=5000   → accessible at http://127.0.0.1:5000
    # if __name__ == '__main__' → only runs when executed directly,
    # not when imported by another script