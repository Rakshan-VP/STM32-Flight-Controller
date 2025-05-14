let pyodide;

async function loadPyodideAndRun() {
  // Load Pyodide once the window is ready
  pyodide = await loadPyodide();
  console.log("Pyodide loaded successfully");
}

window.onload = loadPyodideAndRun; // Ensure Pyodide is loaded when the page is ready

async function runPython() {
  if (!pyodide) {
    console.error("Pyodide is not loaded yet.");
    return;
  }

  const num1 = document.getElementById("num1").value;
  const num2 = document.getElementById("num2").value;

  // Load the Python code from the main.py file
  const response = await fetch("main.py");
  let pyCode = await response.text();

  // Replace placeholders with the user inputs
  pyCode = pyCode.replace("{{NUM1}}", num1).replace("{{NUM2}}", num2);

  try {
    const result = await pyodide.runPythonAsync(pyCode);
    document.getElementById("output").textContent = "Result: " + result;
  } catch (err) {
    document.getElementById("output").textContent = "Error: " + err;
  }
}
