// Live display for PWM sliders
const sliders = ['roll', 'pitch', 'yaw', 'thrust'];
sliders.forEach(axis => {
  const slider = document.getElementById(axis);
  const label = document.getElementById(`${axis}Val`);
  slider.addEventListener('input', () => {
    label.textContent = slider.value;
  });
});

// Send command
function sendRPYT() {
  const r = parseInt(document.getElementById('roll').value);
  const p = parseInt(document.getElementById('pitch').value);
  const y = parseInt(document.getElementById('yaw').value);
  const t = parseInt(document.getElementById('thrust').value);
  const mode = document.getElementById('flightMode').value;
  const rtl = document.getElementById('rtlSwitch').checked;

  const command = {
    roll: r,
    pitch: p,
    yaw: y,
    thrust: t,
    mode: mode,
    rtl_enabled: rtl
  };

  console.log("Transmitter Output:", command);

  // TODO: Pass to Pyodide or simulator logic
  // Example: pyodide.runPython(`handle_command(${JSON.stringify(command)})`)
}
