window.updateLabel = function (id, val) {
  document.getElementById(id).innerText = val;
};

window.runSimulation = async function () {
  const roll = parseInt(document.getElementById("roll").value);
  const pitch = parseInt(document.getElementById("pitch").value);
  const yaw = parseInt(document.getElementById("yaw").value);
  const thrust = parseInt(document.getElementById("thrust").value);

  const flightMode = document.getElementById("mode").value;
  const rtl = document.getElementById("rtl").checked;

  const command = { roll, pitch, yaw, thrust, flightMode, rtl };

  await pyodide.runPythonAsync(`
import json
cmd = json.loads('''${JSON.stringify(command)}''')
motors = flight_controller(cmd)
response = motor_to_rpyt(motors)
  `);

  const rpyt = pyodide.globals.get("response").toJs();
  const motor = pyodide.globals.get("motors").toJs();

  Plotly.newPlot("rpyt-plot", [
    { y: rpyt[0], name: "Roll" },
    { y: rpyt[1], name: "Pitch" },
    { y: rpyt[2], name: "Yaw" },
    { y: rpyt[3], name: "Thrust" },
  ], { title: "RPYT Response" });

  Plotly.newPlot("motor-plot", [
    { y: motor[0], name: "M1" },
    { y: motor[1], name: "M2" },
    { y: motor[2], name: "M3" },
    { y: motor[3], name: "M4" },
  ], { title: "Motor Commands" });
};
