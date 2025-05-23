// Display slider values live
const sliders = ['roll', 'pitch', 'yaw', 'thrust'];

sliders.forEach(axis => {
  const slider = document.getElementById(axis);
  const label = document.getElementById(`${axis}Val`);
  slider.addEventListener('input', () => {
    label.textContent = slider.value;
  });
});

// Handle "Send" button
function sendRPYT() {
  const r = parseFloat(document.getElementById('roll').value);
  const p = parseFloat(document.getElementById('pitch').value);
  const y = parseFloat(document.getElementById('yaw').value);
  const t = parseFloat(document.getElementById('thrust').value);

  const rpyt = { roll: r, pitch: p, yaw: y, thrust: t };
  console.log("Sending RPYT:", rpyt);

  // Next step: Send to Python (via Pyodide)
  // Example: pyodide.runPython(`handle_rpyt(${r}, ${p}, ${y}, ${t})`)
}
