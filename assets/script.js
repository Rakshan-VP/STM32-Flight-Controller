// === GLOBALS === //
let simulationRunning = false;
let simTime = 0; // seconds
const simStep = 0.05; // 20 Hz update rate

// Data buffers for plotting
const timeData = [];
const rpyData = {roll: [], pitch: [], yaw: [], thrust: []};
const motorData = [[], [], [], []]; // M1, M2, M3, M4

// Drone state (dummy simulation)
let droneState = {
  position: {lat: 12.9716, lon: 77.5946, alt: 0},
  roll: 0, pitch: 0, yaw: 0, thrust: 0,
  motorCommands: [1500, 1500, 1500, 1500]
};

let waypoints = [];
let rtlEnabled = false;
let pidGains = {kp:1, ki:0, kd:0.1};
let losGain = 0.5;

// --- Three.js Setup ---
let scene, camera, renderer, droneModel;
const RADIANS_TO_DEG = 180/Math.PI;

function initThreeJS() {
  const container = document.getElementById('threejs-container');
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
  camera.position.set(0, -15, 10);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  // Add light
  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(10,10,10);
  scene.add(light);

  const ambient = new THREE.AmbientLight(0x404040);
  scene.add(ambient);

  // Ground Plane
  const planeGeo = new THREE.PlaneGeometry(50,50);
  const planeMat = new THREE.MeshStandardMaterial({color: 0x88cc88});
  const plane = new THREE.Mesh(planeGeo, planeMat);
  plane.rotation.x = - Math.PI / 2;
  scene.add(plane);

  // Drone (simple box as placeholder)
  const droneGeo = new THREE.BoxGeometry(1, 1, 0.3);
  const droneMat = new THREE.MeshStandardMaterial({color: 0x0033ff});
  droneModel = new THREE.Mesh(droneGeo, droneMat);
  scene.add(droneModel);
}

function updateDroneModel() {
  // Convert RPY (degrees) to radians for rotation
  droneModel.rotation.x = THREE.MathUtils.degToRad(droneState.roll);
  droneModel.rotation.y = THREE.MathUtils.degToRad(droneState.pitch);
  droneModel.rotation.z = THREE.MathUtils.degToRad(droneState.yaw);

  // Position update (simple flat coords, ignoring lat/lon scaling)
  // For demo, convert lat/lon differences roughly to meters:
  const lat0 = droneState.position.lat;
  const lon0 = droneState.position.lon;
  // For visualization, keep position near origin, move on X-Y plane:
  droneModel.position.x = (lat0 - 12.9716) * 111139; // approx meters per deg latitude
  droneModel.position.y = (lon0 - 77.5946) * 111139 * Math.cos(lat0 * Math.PI/180);
  droneModel.position.z = droneState.position.alt;
}

function animateThreeJS() {
  requestAnimationFrame(animateThreeJS);
  renderer.render(scene, camera);
}

// --- Plotly Setup ---
function initPlots() {
  const rpytLayout = {
    margin: {t: 20, b: 40, l: 40, r: 20},
    yaxis: {range: [-180, 180]},
    xaxis: {title: 'Time (s)'},
    legend: {orientation: "h"},
    height: '100%'
  };
  Plotly.newPlot('rpyt-plotly', [
    {y:[], x:[], name:'Roll (°)', mode:'lines', line:{color:'red'}},
    {y:[], x:[], name:'Pitch (°)', mode:'lines', line:{color:'green'}},
    {y:[], x:[], name:'Yaw (°)', mode:'lines', line:{color:'blue'}},
    {y:[], x:[], name:'Thrust', mode:'lines', line:{color:'orange'}}
  ], rpytLayout, {responsive:true});

  const motorLayout = {
    margin: {t: 20, b: 40, l: 40, r: 20},
    yaxis: {range: [1000, 2000], title: 'PWM Signal'},
    xaxis: {title: 'Time (s)'},
    legend: {orientation: "h"},
    height: '100%'
  };
  Plotly.newPlot('motor-plotly', [
    {y:[], x:[], name:'Motor 1', mode:'lines', line:{color:'purple'}},
    {y:[], x:[], name:'Motor 2', mode:'lines', line:{color:'cyan'}},
    {y:[], x:[], name:'Motor 3', mode:'lines', line:{color:'magenta'}},
    {y:[], x:[], name:'Motor 4', mode:'lines', line:{color:'lime'}}
  ], motorLayout, {responsive:true});
}

function updatePlots() {
  const maxPoints = 300;
  // RPYT
  Plotly.extendTraces('rpyt-plotly', {
    x: [[simTime],[simTime],[simTime],[simTime]],
    y: [[droneState.roll],[droneState.pitch],[droneState.yaw],[droneState.thrust]]
  }, [0,1,2,3], maxPoints);

  // Motor Commands
  Plotly.extendTraces('motor-plotly', {
    x: [[simTime],[simTime],[simTime],[simTime]],
    y: [droneState.motorCommands.map(v => v)]
  }, [0,1,2,3], maxPoints);
}

// --- Update RPYT HUD ---
function updateRPYTHUD() {
  document.getElementById('roll-val').textContent = droneState.roll.toFixed(1);
  document.getElementById('pitch-val').textContent = droneState.pitch.toFixed(1);
  document.getElementById('yaw-val').textContent = droneState.yaw.toFixed(1);
  document.getElementById('thrust-val').textContent = droneState.thrust.toFixed(2);
}

// --- Dummy Simulation Step ---
function simulateStep() {
  if (!simulationRunning) return;

  simTime += simStep;

  // Dummy: increment position lat by small delta, and cycle yaw between -180 to 180
  droneState.position.lat += 0.00001; 
  droneState.position.lon += 0.00001;
  droneState.position.alt = 5 + 2 * Math.sin(simTime/5);

  droneState.roll = 10 * Math.sin(simTime);
  droneState.pitch = 8 * Math.sin(simTime/2);
  droneState.yaw = (simTime * 20) % 360 - 180;
  droneState.thrust = 0.6 + 0.4 * Math.abs(Math.sin(simTime/3));

  // Dummy motor commands (just oscillate around 1500)
  for (let i = 0; i < 4; i++) {
    droneState.motorCommands[i] = 1500 + 200 * Math.sin(simTime + i);
  }

  updateDroneModel();
  updateRPYTHUD();
  updatePlots();
}

// --- Handle Form Submission ---
document.getElementById('input-form').addEventListener('submit', (e) => {
  e.preventDefault();

  // Parse inputs
  droneState.position.lat = parseFloat(document.getElementById('start-lat').value);
  droneState.position.lon = parseFloat(document.getElementById('start-lon').value);
  droneState.position.alt = parseFloat(document.getElementById('start-alt').value);

  // Parse waypoints
  const wpText = document.getElementById('waypoints').value.trim();
  waypoints = wpText.split('\n').map(line => {
    const parts = line.split(',').map(s => parseFloat(s.trim()));
    return {lat: parts[0], lon: parts[1], alt: parts[2]};
  });

  rtlEnabled = document.getElementById('rtl-toggle').checked;

  pidGains.kp = parseFloat(document.getElementById('kp').value);
  pidGains.ki = parseFloat(document.getElementById('ki').value);
  pidGains.kd = parseFloat(document.getElementById('kd').value);

  losGain = parseFloat(document.getElementById('los-gain').value);

  // Reset simulation state variables if needed
  simTime = 0;

  // Start simulation
  simulationRunning = true;
});

// --- Initialization ---
window.onload = () => {
  initThreeJS();
  initPlots();
  animateThreeJS();

  // Run simulation step every simStep seconds
  setInterval(simulateStep, simStep * 1000);
};
