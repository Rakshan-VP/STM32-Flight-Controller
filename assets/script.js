let pyodide;

async function initPyodide() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage("matplotlib");
  const simCode = await (await fetch("src/sim_logic.py")).text();
  pyodide.runPython(simCode);
}

function initMapPlot() {
  Plotly.newPlot('map2d', [{
    x: [],
    y: [],
    mode: 'lines+markers',
    line: { color: 'green' },
    name: 'Path'
  }], {
    title: 'Drone Path (Lat vs Lon)',
    xaxis: { title: 'Longitude' },
    yaxis: { title: 'Latitude' },
    margin: { t: 30 }
  });
}

function updateMapPosition(lat, lon) {
  Plotly.extendTraces('map2d', { x: [[lon]], y: [[lat]] }, [0]);
}

// Initialize Three.js 3D drone model (simple cube as placeholder)
let scene, camera, renderer, cube;
function init3DModel() {
  const container = document.getElementById('3d');
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  const geometry = new THREE.BoxGeometry(1, 0.3, 0.5);
  const material = new THREE.MeshNormalMaterial();
  cube = new THREE.Mesh(geometry, material);
  scene.add(cube);

  camera.position.z = 3;

  animate3D();
}

// Animate the 3D model continuously
function animate3D() {
  requestAnimationFrame(animate3D);
  renderer.render(scene, camera);
}

// Update 3D drone orientation from roll, pitch, yaw (in degrees)
function update3DOrientation(roll, pitch, yaw) {
  // Convert degrees to radians
  const r = roll * Math.PI / 180;
  const p = pitch * Math.PI / 180;
  const y = yaw * Math.PI / 180;

  // Apply rotation in ZYX order (yaw, pitch, roll)
  cube.rotation.x = p;
  cube.rotation.y = y;
  cube.rotation.z = r;
}

function getInputs() {
  return {
    start: {
      lat: parseFloat(document.getElementById("start-lat").value),
      lon: parseFloat(document.getElementById("start-lon").value),
      alt: parseFloat(document.getElementById("start-alt").value),
    },
    waypoint: {
      lat: parseFloat(document.getElementById("wp-lat").value),
      lon: parseFloat(document.getElementById("wp-lon").value),
      alt: parseFloat(document.getElementById("wp-alt").value),
    },
    kp: parseFloat(document.getElementById("kp").value),
    ki: parseFloat(document.getElementById("ki").value),
    kd: parseFloat(document.getElementById("kd").value),
    los: parseFloat(document.getElementById("los").value),
  };
}

function updateDisplay(data) {
  const { roll, pitch, yaw, thrust, motors, pos } = data;

  document.getElementById("rpy-values").innerText = `RPY: ${roll.toFixed(2)}, ${pitch.toFixed(2)}, ${yaw.toFixed(2)}`;
  document.getElementById("pos-values").innerText = `Position: ${pos.lat.toFixed(5)}, ${pos.lon.toFixed(5)}, ${pos.alt.toFixed(2)}`;
  document.getElementById("motor-values").innerText = `Motors: ${motors.map(m => m.toFixed(0)).join(", ")}`;

  Plotly.extendTraces('plot-roll', { y: [[roll]] }, [0]);
  Plotly.extendTraces('plot-pitch', { y: [[pitch]] }, [0]);
  Plotly.extendTraces('plot-yaw', { y: [[yaw]] }, [0]);
  Plotly.extendTraces('plot-thrust', { y: [[thrust]] }, [0]);

  // Update map and 3D orientation
  updateMapPosition(pos.lat, pos.lon);
  update3DOrientation(roll, pitch, yaw);
}

function initPlots() {
  const configs = ['roll', 'pitch', 'yaw', 'thrust'];
  configs.forEach(type => {
    Plotly.newPlot(`plot-${type}`, [{
      y: [],
      mode: 'lines',
      line: { color: 'blue' }
    }], {
      title: `${type.toUpperCase()} vs Time`,
      margin: { t: 30 }
    });
  });
}

document.getElementById("start-sim").addEventListener("click", async () => {
  const inputs = getInputs();
  const pyInput = `run_simulation(${JSON.stringify(inputs)})`;
  let count = 0;
  const interval = setInterval(() => {
    if (count > 100) {
      clearInterval(interval);
      return;
    }
    const result = pyodide.runPython(pyInput);
    updateDisplay(JSON.parse(result));
    count++;
  }, 200);
});

// Initialize everything
window.addEventListener('DOMContentLoaded', () => {
  initPyodide().then(() => {
    initPlots();
    initMapPlot();
    init3DModel();
    console.log("Pyodide, plots, map, and 3D model initialized.");
  });
});

