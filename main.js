let pyodideReadyPromise = loadPyodide();
let running = false;

async function startSim() {
  if (running) return;
  running = true;

  let pyodide = await pyodideReadyPromise;
  await pyodide.loadPackage("numpy");
  const response = await fetch("fc.py");
  await pyodide.runPythonAsync(await response.text());

  const rpyNames = ['Roll', 'Pitch', 'Yaw', 'Thrust'];
  const motorNames = ['M1', 'M2', 'M3', 'M4'];
  let t = 0;

  Plotly.newPlot('rpy_plot', rpyNames.map(n => ({x: [], y: [], name: n})));
  Plotly.newPlot('motor_plot', motorNames.map(n => ({x: [], y: [], name: n})));
  Plotly.newPlot('path', [{x: [], y: [], mode: 'lines+markers'}]);

  function loop() {
    if (!running) return;
    const r = +document.getElementById("roll").value;
    const p = +document.getElementById("pitch").value;
    const y = +document.getElementById("yaw").value;
    const T = +document.getElementById("thrust").value;

    pyodide.globals.set("r", r);
    pyodide.globals.set("p", p);
    pyodide.globals.set("y", y);
    pyodide.globals.set("T", T);

    pyodide.runPython("rpy_pid, motors = fc_step(r, p, y, T)");
    const rpyt = pyodide.globals.get("rpy_pid").toJs();
    const motors = pyodide.globals.get("motors").toJs();

    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces('rpy_plot', {x:[[t]], y:[[rpyt[i]]]}, [i]);
      Plotly.extendTraces('motor_plot', {x:[[t]], y:[[motors[i]]]}, [i]);
    }

    Plotly.update('path', {
      x: [[...Array(t*10+1).keys()].map(x => x/10)],
      y: [[...Array(t*10+1).keys()].map(i => rpyt[3])]]
    });

    t += 0.1;
    setTimeout(loop, 100);
  }

  loop();
}

document.getElementById("startBtn").addEventListener("click", startSim);
