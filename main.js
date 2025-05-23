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

  const plotConfigs = [
    {id: 'roll_plot', name1: 'Roll_cmd', name2: 'Roll_pid'},
    {id: 'pitch_plot', name1: 'Pitch_cmd', name2: 'Pitch_pid'},
    {id: 'yaw_plot', name1: 'Yaw_cmd', name2: 'Yaw_pid'},
    {id: 'thrust_plot', name1: 'Thrust_cmd', name2: 'Thrust_pid'},
  ];

  plotConfigs.forEach(cfg =>
    Plotly.newPlot(cfg.id, [
      {x: [], y: [], name: cfg.name1},
      {x: [], y: [], name: cfg.name2}
    ])
  );

  ['m1_plot', 'm2_plot', 'm3_plot', 'm4_plot'].forEach(id =>
    Plotly.newPlot(id, [{x: [], y: [], name: id.toUpperCase()}])
  );

  Plotly.newPlot('path', [{
    x: [], y: [], mode: 'lines+markers', name: 'Drone Path'
  }]);

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
    const pid = pyodide.globals.get("rpy_pid").toJs();
    const m = pyodide.globals.get("motors").toJs();
    const cmd = [r, p, y, T];
  
    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces(plotConfigs[i].id, {x: [[t]], y: [[cmd[i]]]}, [0], 100);
      Plotly.extendTraces(plotConfigs[i].id, {x: [[t]], y: [[pid[i]]]}, [1], 100);
    }
  
    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces(`m${i+1}_plot`, {x: [[t]], y: [[m[i]]]}, [0], 100);
    }
  
    pathX.push(t);
    pathY.push(pid[3]);
    Plotly.update('path', {x: [pathX], y: [pathY]});
  
    t += 0.1;
    setTimeout(loop, 100);
  }
  loop();
}

function stopSim() {
  running = false;
}

document.getElementById("startBtn").addEventListener("click", startSim);
document.getElementById("stopBtn").addEventListener("click", stopSim);
