let pyodideReadyPromise = loadPyodide();
let running = false;

async function startSim() {
  if (running) return;
  running = true;

  let pyodide = await pyodideReadyPromise;
  await pyodide.loadPackage("numpy");
  const response = await fetch("fc.py");
  await pyodide.runPythonAsync(await response.text());

  let t = 0;
  let pathX = [], pathY = [];

  Plotly.newPlot('rpy_plot', [
    {x: [], y: [], name: 'Roll_cmd'}, {x: [], y: [], name: 'Pitch_cmd'},
    {x: [], y: [], name: 'Yaw_cmd'}, {x: [], y: [], name: 'Thrust_cmd'},
    {x: [], y: [], name: 'Roll_pid'}, {x: [], y: [], name: 'Pitch_pid'},
    {x: [], y: [], name: 'Yaw_pid'}, {x: [], y: [], name: 'Thrust_pid'},
  ]);

  Plotly.newPlot('motor_plot', [
    {x: [], y: [], name: 'M1'}, {x: [], y: [], name: 'M2'},
    {x: [], y: [], name: 'M3'}, {x: [], y: [], name: 'M4'},
  ]);

  Plotly.newPlot('path', [{
    x: [], y: [], mode: 'lines+markers', name: 'Drone Path'
  }], {
    margin: {t:0}, xaxis: {title: 'Time'}, yaxis: {title: 'Thrust'}
  });

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
    const rpyt_pid = pyodide.globals.get("rpy_pid").toJs();
    const motors = pyodide.globals.get("motors").toJs();

    const rpyt_cmd = [r, p, y, T];

    // Extend RPY plot: 4 command + 4 PID values
    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces('rpy_plot', {x: [[t]], y: [[rpyt_cmd[i]]]}, [i]);
      Plotly.extendTraces('rpy_plot', {x: [[t]], y: [[rpyt_pid[i]]]}, [i + 4]);
    }

    // Extend Motor plot
    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces('motor_plot', {x: [[t]], y: [[motors[i]]]}, [i]);
    }

    // Extend Path plot (use t for X and thrust for Y)
    pathX.push(t);
    pathY.push(rpyt_pid[3]);
    Plotly.update('path', {x: [pathX], y: [pathY]});

    t += 0.1;
    setTimeout(loop, 100);
  }

  loop();
}

document.getElementById("startBtn").addEventListener("click", startSim);
