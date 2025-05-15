// Load Pyodide and initialize Python environment + simulation
let pyodide = null;
let sim = null; // Python simulator object

// Globals for plots and UI elements
const rpytPlots = {
  roll: null,
  pitch: null,
  yaw: null,
  thrust: null,
};

const motorCmdColors = ["red", "green", "blue", "orange"];

let map, droneMarker, pathLine;
let dronePathLatLngs = [];

let threeScene, threeCamera, threeRenderer, droneMesh, controls;

async function loadPyodideAndPackages() {
  pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
  });
  await pyodide.loadPackage(["numpy", "micropip"]);

  // You can load custom python files here from /src/ or embed them inline
  // For now, we will inline minimal python for simulation

  const pyCode = `
import math
import numpy as np

class Simulator:
    def __init__(self, start_pos, waypoints, kp, ki, kd, los_gain, rtl):
        self.lat, self.lon, self.alt = start_pos
        self.waypoints = waypoints
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.los_gain = los_gain
        self.rtl = rtl
        self.time = 0.0
        self.dt = 0.1  # 10 Hz sim

        self.current_wp_index = 0
        self.max_steps = 500

        # State: [roll, pitch, yaw, thrust]
        self.state = np.array([0., 0., 0., 0.])
        self.motor_commands = [0, 0, 0, 0]

        self.position = np.array([self.lat, self.lon, self.alt])
        self.position_history = [self.position.copy()]
        self.rpyt_history = [self.state.copy()]
        self.motor_history = [self.motor_commands.copy()]

        # Simple PID state
        self.integral = np.zeros(4)
        self.prev_error = np.zeros(4)

    def step(self):
        # Guidance block: move toward current waypoint or RTL
        target = None
        if self.rtl:
            target = np.array([self.lat, self.lon, self.alt])  # RTL start pos
        else:
            if self.current_wp_index < len(self.waypoints):
                target = self.waypoints[self.current_wp_index]
            else:
                # End of mission
                target = self.position

        # Simple guidance: error in lat, lon, alt to target
        pos_error = target - self.position

        # If close to wp, increment index
        if np.linalg.norm(pos_error) < 0.00005:  # ~5m threshold approx
            if not self.rtl:
                self.current_wp_index += 1

        # Desired roll, pitch, yaw, thrust based on error and LOS gain
        desired_roll = self.los_gain * pos_error[1] * 100  # simplified approx
        desired_pitch = self.los_gain * pos_error[0] * 100
        desired_yaw = 0  # for simplicity fixed yaw
        desired_thrust = min(max(0.5 + pos_error[2], 0), 1)

        desired = np.array([desired_roll, desired_pitch, desired_yaw, desired_thrust])

        # PID control to follow desired from current state
        error = desired - self.state
        self.integral += error * self.dt
        derivative = (error - self.prev_error) / self.dt
        self.prev_error = error

        control = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.state += control * self.dt

        # Simple motor mixer for quadrotor (4 motors)
        # Motor commands between 1000-2000 PWM based on RPYT
        base_pwm = 1500 + self.state[3]*500  # thrust part

        roll_pwm = self.state[0]*100
        pitch_pwm = self.state[1]*100
        yaw_pwm = self.state[2]*50

        m1 = base_pwm + roll_pwm + pitch_pwm - yaw_pwm
        m2 = base_pwm - roll_pwm + pitch_pwm + yaw_pwm
        m3 = base_pwm - roll_pwm - pitch_pwm - yaw_pwm
        m4 = base_pwm + roll_pwm - pitch_pwm + yaw_pwm

        self.motor_commands = [int(np.clip(m, 1000, 2000)) for m in [m1,m2,m3,m4]]

        # Simulate position change (very rough, just for visualization)
        # Add noise for IMU/GPS simulation could be here
        self.position += 0.00001 * pos_error  # moves slowly toward target

        # Save history
        self.position_history.append(self.position.copy())
        self.rpyt_history.append(self.state.copy())
        self.motor_history.append(self.motor_commands.copy())

        self.time += self.dt

        return {
            "time": self.time,
            "position": self.position.tolist(),
            "state": self.state.tolist(),
            "motor_commands": self.motor_commands
        }
  `;

  await pyodide.runPythonAsync(pyCode);

  sim = pyodide.globals.get("Simulator");
}

async function init() {
  await loadPyodideAndPackages();
  initMap();
  init3D();
  initPlots();

  document.getElementById("controlForm").addEventListener("submit", (e) => {
    e.preventDefault();
    startSimulation();
  });
}

function initMap() {
  map = L.map("map").setView([12.9716, 77.5946], 15);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  droneMarker = L.marker([12.9716, 77.5946]).addTo(map);
  dronePathLatLngs = [];
  pathLine = L.polyline(dronePathLatLngs, {color: "blue"}).addTo(map);
}

function init3D() {
  const width = 400;
  const height = 300;

  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  threeRenderer = new THREE.WebGLRenderer({ antialias: true });
  threeRenderer.setSize(width, height);
  document.getElementById("threeDcanvas").appendChild(threeRenderer.domElement);

  controls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
  controls.enablePan = false;
  controls.minDistance = 2;
  controls.maxDistance = 10;
  controls.target.set(0, 0, 0);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xcccccc, 0.5);
  threeScene.add(ambientLight);
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(5, 10, 7);
  threeScene.add(directionalLight);

  // Drone model - simple box for now
  const geometry = new THREE.BoxGeometry(1, 0.2, 1);
  const material = new THREE.MeshStandardMaterial({ color: 0x0077ff });
  droneMesh = new THREE.Mesh(geometry, material);
  threeScene.add(droneMesh);

  threeCamera.position.set(5, 5, 5);
  controls.update();

  animate3D();
}

function animate3D() {
  requestAnimationFrame(animate3D);
  controls.update();
  threeRenderer.render(threeScene, threeCamera);
}

function initPlots() {
  const time = [];
  const emptyData = [];

  function initPlot(divId, name, color) {
    Plotly.newPlot(divId, [{
      x: time,
      y: emptyData,
      type: 'scatter',
      mode: 'lines',
      line: {color: color}
    }],
    {
      margin: {t:30, b:30, l:40, r:20},
      yaxis: {title: name}
    });
  }

  initPlot("plotRoll", "Roll (deg)", "red");
  initPlot("plotPitch", "Pitch (deg)", "green");
  initPlot("plotYaw", "Yaw (deg)", "blue");
  initPlot("plotThrust", "Thrust (0-1)", "orange");
}

let simInstance = null;
let simInterval = null;
let simData = {
  time: [],
  roll: [],
  pitch: [],
  yaw: [],
  thrust: [],
  lat: [],
  lon: [],
  alt: [],
  motors: [[],[],[],[]]
};

async function startSimulation() {
  if (simInterval) {
    clearInterval(simInterval);
    simInterval = null;
  }

  // Reset data
  simData = {
    time: [],
    roll: [],
    pitch: [],
    yaw: [],
    thrust: [],
    lat: [],
    lon: [],
    alt: [],
    motors: [[],[],[],[]]
  };

  // Get inputs
  const startLat = parseFloat(document.getElementById("startLat").value);
  const startLon = parseFloat(document.getElementById("startLon").value);
  const startAlt = parseFloat(document.getElementById("startAlt").value);

  const wpText = document.getElementById("waypoints").value.trim();
  let waypoints = [];
  if (wpText) {
    const lines = wpText.split("\n");
    for (const line of lines) {
      const parts = line.split(",");
      if (parts.length === 3) {
        waypoints.push([
          parseFloat(parts[0]),
          parseFloat(parts[1]),
          parseFloat(parts[2]),
        ]);
      }
    }
  }

  const rtl = document.getElementById("rtlCheck").checked;
  const kp = parseFloat(document.getElementById("kp").value);
  const ki = parseFloat(document.getElementById("ki").value);
  const kd = parseFloat(document.getElementById("kd").value);
  const losGain = parseFloat(document.getElementById("losGain").value);
  const simClass = pyodide.globals.get("Simulator");
  simInstance = simClass(
    [startLat, startLon, startAlt],
    waypoints,
    kp,
    ki,
    kd,
    losGain,
    rtl
  );
  
  simInterval = setInterval(() => {
    const result = simInstance.step().toJs();
    updateSimData(result);
  }, 100);
  
  function updateSimData(data) {
    const t = data.time;
    const pos = data.position;
    const state = data.state;
    const motors = data.motor_commands;
  
    simData.time.push(t);
    simData.roll.push(state[0]);
    simData.pitch.push(state[1]);
    simData.yaw.push(state[2]);
    simData.thrust.push(state[3]);
    simData.lat.push(pos[0]);
    simData.lon.push(pos[1]);
    simData.alt.push(pos[2]);
  
    for (let i = 0; i < 4; i++) {
      simData.motors[i].push(motors[i]);
    }
  
    // Update plots
    Plotly.update("plotRoll", { x: [simData.time], y: [simData.roll] });
    Plotly.update("plotPitch", { x: [simData.time], y: [simData.pitch] });
    Plotly.update("plotYaw", { x: [simData.time], y: [simData.yaw] });
    Plotly.update("plotThrust", { x: [simData.time], y: [simData.thrust] });
  
    // Update map
    const latlng = [pos[0], pos[1]];
    droneMarker.setLatLng(latlng);
    dronePathLatLngs.push(latlng);
    pathLine.setLatLngs(dronePathLatLngs);
  
    // Update 3D drone orientation (very simple)
    droneMesh.rotation.x = state[0];
    droneMesh.rotation.y = state[2];
    droneMesh.rotation.z = state[1];
  
    document.getElementById("rpyValues").innerText =
      `Roll: ${state[0].toFixed(2)}\nPitch: ${state[1].toFixed(2)}\nYaw: ${state[2].toFixed(2)}\nThrust: ${state[3].toFixed(2)}`;
    document.getElementById("positionValues").innerText =
      `Lat: ${pos[0].toFixed(6)}\nLon: ${pos[1].toFixed(6)}\nAlt: ${pos[2].toFixed(1)}`;
    document.getElementById("motorCommands").innerText =
      `Motors: ${motors.join(", ")}`;
  }
  
  init();
