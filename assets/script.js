let pyodide;

async function initPyodide() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage("matplotlib");
  const simCode = await (await fetch("src/sim_logic.py")).text();
  pyodide.runPython(simCode);
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

  document.getElementById("rpy-values").innerText = `RPY: ${roll}, ${pitch}, ${yaw}`;
  document.getElementById("pos-values").innerText = `Position: ${pos.lat}, ${pos.lon}, ${pos.alt}`;
  document.getElementById("motor-values").innerText = `Motors: ${motors.join(", ")}`;

  Plotly.extendTraces('plot-roll', { y: [[roll]] }, [0]);
  Plotly.extendTraces('plot-pitch', { y: [[pitch]] }, [0]);
  Plotly.extendTraces('plot-yaw', { y: [[yaw]] }, [0]);
  Plotly.extendTraces('plot-thrust', { y: [[thrust]] }, [0]);
}

function initPlots() {
  const configs = ['roll', 'pitch', 'yaw', 'thrust'];
  configs.forEach(type => {
    Plotly.newPlot(`plot-${type}`, [{
      y: [],
      mode: 'lines',
      line: { color: 'blue' }
    }], {
      title: `${type.toUpperCase()} vs Time`
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

initPyodide().then(() => {
  initPlots();
  console.log("Pyodide and plots initialized.");
});
