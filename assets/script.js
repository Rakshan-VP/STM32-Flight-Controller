import { GLTFLoader } from 'https://cdn.skypack.dev/three@0.140.0/examples/jsm/loaders/GLTFLoader.js';

let pyodide = null;
let rpytChart = null;
let motorChart = null;
let scene, camera, renderer, droneModel;

async function loadPyodideAndPackages() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage(["numpy", "micropip"]);
  await pyodide.runPythonAsync(`
    import sys
    sys.path.append("src")
    from main import init_sim, step_sim
  `);
}

function getInputValues() {
  const start = document.getElementById("start").value.split(",").map(Number);
  const waypoints = document.getElementById("waypoints").value.split(";").map(wp =>
    wp.split(",").map(Number)
  );
  const rtl = document.getElementById("rtl").checked;
  const kp = parseFloat(document.getElementById("kp").value);
  const ki = parseFloat(document.getElementById("ki").value);
  const kd = parseFloat(document.getElementById("kd").value);

  return { start, waypoints, rtl, kp, ki, kd };
}

async function startSimulation() {
  if (!pyodide) await loadPyodideAndPackages();
  const { start, waypoints, rtl, kp, ki, kd } = getInputValues();

  await pyodide.runPythonAsync(`
    init_sim(${JSON.stringify(start)},
             ${JSON.stringify(waypoints)},
             ${rtl},
             ${kp}, ${ki}, ${kd})
  `);

  setupCharts();
  await setup3D();

  let time = 0;
  const interval = setInterval(async () => {
    const result = await pyodide.runPythonAsync("step_sim()");
    const { roll, pitch, yaw, thrust, motors, pos } = JSON.parse(result);

    updateCharts(time, roll, pitch, yaw, thrust, motors);
    update3D(pos, roll, pitch, yaw);

    time += 0.1;
    if (time > 20) clearInterval(interval);
  }, 100);
}

function setupCharts() {
  const ctxRPYT = document.getElementById("rpyt-chart").getContext("2d");
  rpytChart = new Chart(ctxRPYT, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "Roll", data: [], borderColor: "red", fill: false },
        { label: "Pitch", data: [], borderColor: "blue", fill: false },
        { label: "Yaw", data: [], borderColor: "green", fill: false },
        { label: "Thrust", data: [], borderColor: "orange", fill: false },
      ],
    },
    options: { animation: false, scales: { x: { title: { display: true, text: "Time (s)" }}}}
  });

  const ctxMotor = document.getElementById("motor-chart").getContext("2d");
  motorChart = new Chart(ctxMotor, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "M1", data: [], borderColor: "purple" },
        { label: "M2", data: [], borderColor: "teal" },
        { label: "M3", data: [], borderColor: "brown" },
        { label: "M4", data: [], borderColor: "gray" },
      ],
    },
    options: { animation: false, scales: { x: { title: { display: true, text: "Time (s)" }}}}
  });
}

async function setup3D() {
  const container = document.getElementById("3d-container");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, container.offsetWidth / 300, 0.1, 1000);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.offsetWidth, 300);
  container.innerHTML = "";
  container.appendChild(renderer.domElement);

  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(5, 10, 7.5);
  scene.add(light);

  const loader = new GLTFLoader();
  await loader.load(
    "assets/models/drone.glb",
    gltf => {
      droneModel = gltf.scene;
      droneModel.scale.set(0.5, 0.5, 0.5);
      scene.add(droneModel);
    },
    undefined,
    error => console.error("Error loading drone.glb:", error)
  );

  const grid = new THREE.GridHelper(20, 20);
  scene.add(grid);

  camera.position.z = 5;
  camera.position.y = 5;
  camera.lookAt(0, 0, 0);
}

function update3D(pos, roll, pitch, yaw) {
  if (!droneModel) return;

  droneModel.position.set(pos[0], pos[2], pos[1]);
  droneModel.rotation.set(roll, yaw, pitch);

  renderer.render(scene, camera);
}
