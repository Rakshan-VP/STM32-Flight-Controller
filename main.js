let pyodide;

async function loadPyodideAndPackages() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage("micropip");
  const fcCode = await fetch("flight_controller.py").then(r => r.text());
  pyodide.runPython(fcCode);

  const dynCode = await fetch("drone_dynamics.py").then(r => r.text());
  pyodide.runPython(dynCode);

}

loadPyodideAndPackages();

function updateLabel(id) {
  document.getElementById(id + "Val").innerText = document.getElementById(id).value;
}

async function runSimulation() {
  const cmd = {
    roll: parseInt(document.getElementById("roll").value),
    pitch: parseInt(document.getElementById("pitch").value),
    yaw: parseInt(document.getElementById("yaw").value),
    thrust: parseInt(document.getElementById("thrust").value)
  };

  let pythonCmd = `cmd = ${JSON.stringify(cmd)}\n` +
                  `motors = flight_controller(cmd)\n` +
                  `response = motor_to_rpyt(motors)`;
  await pyodide.runPythonAsync(pythonCmd);

  const motors = pyodide.globals.get("motors").toJs();
  const response = pyodide.globals.get("response").toJs();

  Plotly.newPlot("rpyPlot", [
    { y: [response.roll], name: "Roll" },
    { y: [response.pitch], name: "Pitch" },
    { y: [response.yaw], name: "Yaw" },
    { y: [response.thrust], name: "Thrust" },
  ], { title: "RPYT Response", margin: { t: 30 } });

  Plotly.newPlot("motorPlot", motors.map((m, i) => ({
    y: [m], name: `Motor ${i+1}`
  })), { title: "Motor Outputs", margin: { t: 30 } });
}
