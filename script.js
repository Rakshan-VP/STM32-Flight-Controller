let pyodide = null;

// Function to load Pyodide
async function loadPyodideAndInitialize() {
  try {
    // Load Pyodide (this might take some time)
    pyodide = await loadPyodide();
    console.log("Pyodide successfully loaded!");
  } catch (err) {
    console.error("Failed to load Pyodide:", err);
  }
}

// Initialize Pyodide when the window loads
window.onload = loadPyodideAndInitialize;

async function runPython() {
  // Check if Pyodide is loaded
  if (pyodide === null) {
    console.error("Pyodide is not loaded yet.");
    document.getElementById("output").textContent = "Error: Pyodide is not loaded yet.";
    return;
  }

  const num1 = document.getElementById("num1").value;
  const num2 = document.getElementById("num2").value;

  // Load Python code from main.py
  const response = await fetch("main.py");
  let pyCode = await response.text();

  // Replace placeholders with actual values
  pyCode = pyCode.replace("{{NUM1}}", num1).replace("{{NUM2}}", num2);

  try {
    // Run the Python code using Pyodide
    const result = await pyodide.runPythonAsync(pyCode);
    document.getElementById("output").textContent = "Result: " + result;
  } catch (err) {
    console.error("Error running Python code:", err);
    document.getElementById("output").textContent = "Error: " + err;
  }
}
