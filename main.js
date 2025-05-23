let pyodideReadyPromise = loadPyodide();
let running = false;

async function startSim() {
  if (running) return;
  running = true;
  let pyodide = await pyodideReadyPromise;
  await pyodide.loadPackage("numpy");
  let response = await fetch("fc.py");
  await pyodide.runPythonAsync(await response.text());

  let rpyPlot = {x: [], y: [[], [], [], []], name: ['Roll', 'Pitch', 'Yaw', 'Thrust']};
  let motorPlot = {x: [], y: [[], [], [], []], name: ['M1', 'M2', 'M3', 'M4']};
  let path = {x: [], y: []};
  let t = 0;

  Plotly.newPlot('rpy_plot', [0,1,2,3].map(i => ({x:[], y:[], name:rpyPlot.name[i]})));
  Plotly.newPlot('motor_plot', [0,1,2,3].map(i => ({x:[], y:[], name:motorPlot.name[i]})));
  Plotly.newPlot('path', [{x:[], y:[], mode:'lines+markers'}]);

  function loop() {
    if (!running) return;
    let r = +roll.value, p = +pitch.value, y = +yaw.value, T = +thrust.value;
    pyodide.globals.set("r", r);
    pyodide.globals.set("p", p);
    pyodide.globals.set("y", y);
    pyodide.globals.set("T", T);
    pyodide.runPython("rpy_pid, motors = fc_step(r, p, y, T)");

    let rpyt = pyodide.globals.get("rpy_pid").toJs();
    let motors = pyodide.globals.get("motors").toJs();
    for (let i = 0; i < 4; i++) {
      Plotly.extendTraces('rpy_plot', {x:[[t]], y:[[rpyt[i]]]}, [i]);
      Plotly.extendTraces('motor_plot', {x:[[t]], y:[[motors[i]]]}, [i]);
    }
    path.x.push(t);
    path.y.push(rpyt[3]);
    Plotly.update('path', {x: [path.x], y: [path.y]});
    t += 0.1;
    setTimeout(loop, 100);
  }

  loop();
}
