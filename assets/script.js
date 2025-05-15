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
    line: { color: 'red' },
    name: 'Path'
  }], {
    title: 'Drone Path (Lat vs Lon)',
    xaxis: { title: 'Longitude' },
    yaxis: { title: 'Latitude' },
    margin: { t: 30 }
  });
}

function updateMapPosition(lat, lon) {
  Plotly.react('map2d', [{
    x: [lon],
    y: [lat],
    mode: 'markers+lines',
    line: { color: 'red' },
    name: 'Path'
  }], {
    title: 'Drone Path',
    xaxis: { title: 'Longitude' },
    yaxis: { title: 'Latitude' }
  });
}

function init3DModel() {
  Plotly.newPlot('3d', [{
    type: 'scatter3d',
    mode: 'lines+markers',
    x: [0, 0],
    y: [0, 0],
    z: [0, 1],
    line: { color: 'green', width: 6 },
    marker: { size: 4 }
  }], {
    scene: {
      xaxis: { range: [-1, 1], title: 'X' },
      yaxis: { range: [-1, 1], title: 'Y' },
      zaxis: { range: [-1, 1], title: 'Z' },
      aspectratio: { x: 1, y: 1, z: 1 }
    },
    margin: { t: 0 }
  });
}

// Update 3D drone orientation from roll, pitch, yaw (in degrees)
function update3DOrientation(roll, pitch, yaw) {
   // Convert degrees to radians
  const r = roll * Math.PI / 180;
  const p = pitch * Math.PI / 180;
  const y = yaw * Math.PI / 180;

  // Rotation matrix ZYX
  const cx = Math.cos(r), sx = Math.sin(r);
  const cy = Math.cos(p), sy = Math.sin(p);
  const cz = Math.cos(y), sz = Math.sin(y);

  // ZYX rotation (yaw, pitch, roll) → direction vector
  const vx = cy * cz;
  const vy = cy * sz;
  const vz = -sy;

  Plotly.react('3d', [{
    type: 'scatter3d',
    mode: 'lines+markers',
    x: [0, vx],
    y: [0, vy],
    z: [0, vz],
    line: { color: 'green', width: 6 },
    marker: { size: 4 }
  }], {
    scene: {
      xaxis: { range: [-1, 1], title: 'X' },
      yaxis: { range: [-1, 1], title: 'Y' },
      zaxis: { range: [-1, 1], title: 'Z' },
      aspectratio: { x: 1, y: 1, z: 1 }
    },
    margin: { t: 0 }
  });

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
  console.log("Incoming data:", data);
  if (!data.pos || typeof data.pos.lat !== 'number' || typeof data.pos.lon !== 'number') {
    console.error("Invalid or missing position data:", data.pos);
    return; // skip updating to avoid errors
  }
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
    console.log("Pyodide initialized.");
  });
});

