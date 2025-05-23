let pyodide;
let history = {
  txRPYT: [], // transmitter commands history
  rxRPYT: [], // vehicle dynamics output history
  motors: [],
  path: [],   // 2D path points
};

async function initPyodide() {
  pyodide = await loadPyodide();

  // Load flight_controller.py code
  const flightControllerCode = await fetch("flight_controller.py").then(r => r.text());
  pyodide.runPython(flightControllerCode);

  // Load drone_dynamics.py code
  const droneDynamicsCode = await fetch("drone_dynamics.py").then(r => r.text());
  pyodide.runPython(droneDynamicsCode);

  // Initialize empty history in Python if needed (optional)
  pyodide.runPython(`
time_step = 0.05  # 50 ms simulation step
x_pos = 0.0
y_pos = 0.0

def update_path(vx, vy):
    global x_pos, y_pos
    x_pos += vx * time_step
    y_pos += vy * time_step
    return [x_pos, y_pos]
`);
}

function updateLabel(id, val) {
  document.getElementById(id).innerText = val;
}

function plotRPYT() {
  // Plot transmitter RPYT vs vehicle RPYT (roll, pitch, yaw, thrust)
  const tx = history.txRPYT;
  const rx = history.rxRPYT;

  let traces = [];
  ["Roll", "Pitch", "Yaw", "Thrust"].forEach((name, i) => {
    traces.push({
      y: tx.map(t => t[i]),
      mode: 'lines',
      name: `${name} Tx`,
      line: { dash: 'dash' }
    });
    traces.push({
      y: rx.map(t => t[i]),
      mode: 'lines',
      name: `${name} Rx`
    });
  });

  Plotly.newPlot("plot-rpyt", traces, { title: "RPYT Transmitter (Tx) vs Vehicle (Rx)" });
}

function plotMotors() {
  const motors = history.motors;
  if (motors.length === 0) return;

  let traces = [];
  for (let i = 0; i < 4; i++) {
    traces.push({
      y: motors.map(m => m[i]),
      mode: 'lines',
      name: `Motor ${i+1}`
    });
  }

  Plotly.newPlot("plot-motors", traces, { title: "Motor Commands" });
}

function plotPath() {
  if (history.path.length === 0) return;
  let x = history.path.map(p => p[0]);
  let y = history.path.map(p => p[1]);

  Plotly.newPlot("plot-path", [{
    x, y,
    mode: 'lines+markers',
    name: '2D Path',
    line: { shape: 'spline' }
  }], { title: "2D Path Simulation", xaxis: { title: "X" }, yaxis: { title: "Y" } });
}

async function runStep() {
  // Get transmitter input values
  const roll = parseInt(document.getElementById("roll").value);
  const pitch = parseInt(document.getElementById("pitch").value);
  const yaw = parseInt(document.getElementById("yaw").value);
  const thrust = parseInt(document.getElementById("thrust").value);

  updateLabel("roll-val", roll);
  updateLabel("pitch-val", pitch);
  updateLabel("yaw-val", yaw);
  updateLabel("thrust-val", thrust);

  // Save Tx RPYT normalized (1000-2000 to -1 to 1)
  const norm = v => (v - 1500) / 500;
  let txRPYT = [norm(roll), norm(pitch), norm(yaw), (thrust - 1000) / 1000];
  history.txRPYT.push(txRPYT);

  // Run flight controller and drone dynamics in pyodide
  // Passing data as JSON string
  let cmdStr = JSON.stringify(txRPYT);
  let pythonCode = `
from flight_controller import flight_controller
from drone_dynamics import motor_to_rpyt, simulate_path_step, update_path

cmd = ${cmdStr}
motors = flight_controller(cmd)
rpyt = motor_to_rpyt(motors)

# Simulate 2D path velocity based on thrust and yaw for demonstration
# vx = thrust * cos(yaw), vy = thrust * sin(yaw)
import math
vx = thrust = rpyt[3]
yaw_angle = rpyt[2]
vx_path = vx * math.cos(yaw_angle)
vy_path = vx * math.sin(yaw_angle)

pos = update_path(vx_path, vy_path)
  `;

  await pyodide.runPythonAsync(pythonCode);

  // Retrieve output arrays
  const motors = pyodide.globals.get("motors").toJs();
  const rpyt = pyodide.globals.get("rpyt").toJs();
  const pos = pyodide.globals.get("pos").toJs();

  history.motors.push(motors);
  history.rxRPYT.push(rpyt);
  history.path.push(pos);

  plotRPYT();
  plotMotors();
  plotPath();

  // Keep history size manageable
  if (history.txRPYT.length > 100) {
    history.txRPYT.shift();
    history.rxRPYT.shift();
    history.motors.shift();
    history.path.shift();
  }
}

// Set up slider event listeners to run simulation live
function setupControls() {
  ["roll", "pitch", "yaw", "thrust"].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", () => {
      runStep();
    });
  });
}

async function main() {
  await initPyodide();
  setupControls();

  // Initial run to plot default values
  runStep();
}

main();
