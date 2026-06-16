let anomalyCount = 0;
let normalCount  = 0;
const CONFIRM_THRESHOLD = 3;// must see 3 consecutive readings before switching

let anomalyStartTime  = null;  // when did anomaly begin
let anomalyDuration   = 0;     // how long in seconds
let alarmLevel        = 'NONE'; // NONE → WATCH → WARNING → CRITICAL

// ── Chart Setup ──────────────────────────────────────────────────────────────
const MAX_POINTS = 40;
const labels     = [];

function makeChart(id, datasets, yLabel) {
  return new Chart(document.getElementById(id), {
    type: 'line',
    data: { labels, datasets },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#78909c', font: { size: 10 } } } },
      scales: {
        x: { ticks: { color: '#546e7a', maxTicksLimit: 6, font: { size: 9 } },
             grid:  { color: '#0f2440' } },
        y: { ticks: { color: '#546e7a', font: { size: 9 } },
             grid:  { color: '#0f2440' },
             title: { display: true, text: yLabel, color: '#546e7a', font: { size: 9 } } }
      }
    }
  });
}

const tempData = [
  { label: 'T1', data: [], borderColor: '#ef5350', borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
  { label: 'T2', data: [], borderColor: '#ffa726', borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
  { label: 'T3', data: [], borderColor: '#4fc3f7', borderWidth: 1.5, pointRadius: 0, tension: 0.3 }
];
const scoreData = [
  { label: 'Anomaly Score', data: [], borderColor: '#ab47bc',
    borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: true,
    backgroundColor: 'rgba(171,71,188,0.08)' }
];

const tempChart  = makeChart('tempChart',  tempData,  'Temperature [K]');
const scoreChart = makeChart('scoreChart', scoreData, 'Score');

// ── Helpers ──────────────────────────────────────────────────────────────────
function push(arr, val) {
  arr.push(val);
  if (arr.length > MAX_POINTS) arr.shift();
}

function updateSensor(id, val, isAlert=false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = typeof val === 'number' ? val.toFixed(4) : val;
  el.className   = 'sensor-value' + (isAlert ? ' alert' : '');
}

// ── Clock ─────────────────────────────────────────────────────────────────────
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}, 1000);

// ── API Call ─────────────────────────────────────────────────────────────────
async function predict(sensors) {
  try {
    const res  = await fetch('http://127.0.0.1:5000/predict', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(sensors)
    });
    const data = await res.json();
    updateDashboard(sensors, data);
  } catch (e) {
    document.getElementById('statusLabel').textContent = 'API OFFLINE';
    document.getElementById('statusMsg').textContent   = 'Make sure Flask is running on port 5000';
  }
}

// ── Update Dashboard ─────────────────────────────────────────────────────────
// ── Confirmation Window ───────────────────────────────────────────────────
function updateDashboard(sensors, result) {
  const isAnomaly = result.status === 'ANOMALY';

  // Count consecutive readings
  if (isAnomaly) {
    anomalyCount++;
    normalCount = 0;
  } else {
    normalCount++;
    anomalyCount = 0;
  }

  // Only switch state after 3 consecutive same readings
  let confirmedState = null;
  if (anomalyCount >= CONFIRM_THRESHOLD) confirmedState = 'ANOMALY';
  if (normalCount  >= CONFIRM_THRESHOLD) confirmedState = 'NORMAL';
  if (!confirmedState) return;

  // ── replaced old banner lines with Time-In-Alarm ──
  updateAlarmLevel(confirmedState);

  document.getElementById('anomalyScore').textContent =
    (result.anomaly_score >= 0 ? '+' : '') + result.anomaly_score.toFixed(4);

  // Sensor cards
  ['Ca1','Cb1','Ca2','Cb2','Ca3','Cb3'].forEach(k => updateSensor(k, sensors[k]));
  ['T1','T2','T3'].forEach(k => updateSensor(k, sensors[k], confirmedState === 'ANOMALY'));

  // Charts
  const t = new Date().toLocaleTimeString();
  push(labels, t);
  push(tempData[0].data, sensors.T1);
  push(tempData[1].data, sensors.T2);
  push(tempData[2].data, sensors.T3);
  push(scoreData[0].data, result.anomaly_score);

  tempChart.update();
  scoreChart.update();
}

// ── Simulation ───────────────────────────────────────────────────────────────
let simInterval = null;

const NORMAL_SENSORS = {
  Ca1:1.25, Cb1:0.45, T1:339.8,
  Ca2:0.81, Cb2:0.62, T2:339.6,
  Ca3:0.50, Cb3:0.68, T3:339.4
};
const FAULT_SENSORS = {
  Ca1:1.25, Cb1:0.45, T1:341.5,
  Ca2:0.81, Cb2:0.62, T2:341.2,
  Ca3:0.50, Cb3:0.68, T3:340.8
};

function addNoise(sensors, scale=0.02) {
  const out = {};
  Object.keys(sensors).forEach(k => {
    out[k] = +(sensors[k] + (Math.random()-0.5)*scale).toFixed(4);
  });
  return out;
}

function sendNormal() {
  stopSim();
  document.getElementById('updateRate').textContent = 'Interval: 1.5s — Normal mode';
  simInterval = setInterval(() => predict(addNoise(NORMAL_SENSORS,0.005)), 1500);
  predict(addNoise(NORMAL_SENSORS,0.005));
}

function sendFault() {
  stopSim();
  document.getElementById('updateRate').textContent = 'Interval: 1.5s — FAULT mode';
  simInterval = setInterval(() => predict(addNoise(FAULT_SENSORS, 0.05)), 1500);
  predict(addNoise(FAULT_SENSORS, 0.05));
}

function stopSim() {
  if (simInterval) { clearInterval(simInterval); simInterval = null; }
  document.getElementById('updateRate').textContent = 'Interval: stopped';
}

// ── Time-In-Alarm Logic ───────────────────────────────────────────────────
function updateAlarmLevel(confirmedState) {
  const now = Date.now();

  if (confirmedState === 'ANOMALY') {
    // Start timer if not already running
    if (!anomalyStartTime) anomalyStartTime = now;
    anomalyDuration = Math.floor((now - anomalyStartTime) / 1000);

    // Escalate based on duration
    if      (anomalyDuration >= 120) alarmLevel = 'CRITICAL';
    else if (anomalyDuration >= 30)  alarmLevel = 'WARNING';
    else if (anomalyDuration >= 5)   alarmLevel = 'WATCH';
    else                             alarmLevel = 'NONE';

  } else {
    // Reset when normal restored
    anomalyStartTime = null;
    anomalyDuration  = 0;
    alarmLevel       = 'NONE';
  }

  updateAlarmBanner(confirmedState);
}

function updateAlarmBanner(confirmedState) {
  const banner = document.getElementById('statusBanner');
  const label  = document.getElementById('statusLabel');
  const msg    = document.getElementById('statusMsg');

  if (confirmedState === 'NORMAL') {
    banner.style.background   = '#0d2318';
    banner.style.borderColor  = '#1b5e20';
    label.style.color         = '#4caf50';
    label.textContent         = '✅ NORMAL';
    msg.textContent           = 'Reactor operating within safe parameters';
    document.getElementById('alarmTimer').textContent = '';
    return;
  }

  // Anomaly — show escalating alarm
  const configs = {
    'NONE'    : { bg: '#1a1200', border: '#f9a825', color: '#f9a825',
                  text: '👁 WATCH',
                  sub: `Anomaly detected — monitoring (${anomalyDuration}s)` },
    'WATCH'   : { bg: '#1a1200', border: '#ffa726', color: '#ffa726',
                  text: '⚠ WATCH — SUSTAINED',
                  sub: `Anomaly sustained ${anomalyDuration}s — operator awareness required` },
    'WARNING' : { bg: '#2d1500', border: '#ef6c00', color: '#ef6c00',
                  text: '🔶 WARNING',
                  sub: `Anomaly sustained ${anomalyDuration}s — investigate immediately` },
    'CRITICAL': { bg: '#2d0a0a', border: '#b71c1c', color: '#ef5350',
                  text: '🚨 CRITICAL — SHUTDOWN RECOMMENDED',
                  sub: `Anomaly sustained ${anomalyDuration}s — THERMAL RUNAWAY RISK` }
  };

  const cfg = configs[alarmLevel];
  banner.style.background  = cfg.bg;
  banner.style.borderColor = cfg.border;
  label.style.color        = cfg.color;
  label.textContent        = cfg.text;
  msg.textContent          = cfg.sub;
  document.getElementById('alarmTimer').textContent =
    `Time in alarm: ${anomalyDuration}s`;
}