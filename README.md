## CSTR Fault Detection — AI System

### Installation
1. Clone the repo
2. Create venv and install packages
3. Run train.py

### How to Run
1. Start API → python backend/app.py (python c:\First_project\cstr-fault-detection\backend\app.py)
2. Open dashboard → frontend/index.html
3. Test API → http://127.0.0.1:5000/sensors/example
and with localhost we use 
http://127.0.0.1:5000
http://127.0.0.1:5000/health
http://127.0.0.1:5000/sensors/example

### Project Structure

cstr-fault-detection/
  data/
    normal_operation.csv  ← simulated sensor readings
    fault_scenarios.csv  ← labeled fault injections
  simulator/
    cstr_ode.py  ← Arrhenius + mass/energy balance
    fault_injector.py  ← injects faults into simulation
  model/
    train.py  ← Isolation Forest training
    evaluate.py  ← precision, recall, F1
    model.pkl  ← saved trained model
  backend/
    app.py  ← Flask API (predict endpoint)
  frontend/
    index.html  ← live reactor dashboard
    dashboard.js
  report/
    report.md  ← scientific write-up
  README.md

### Results
- Accuracy: 90%
- Anomaly Recall: 1.00
- Contamination: 0.222