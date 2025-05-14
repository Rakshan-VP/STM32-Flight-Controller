let pyodideReady = loadPyodide(); // This ensures pyodide is loaded asynchronously

async function runPython() {
  await pyodideReady; // Wait for Pyodide to be ready

  const num1 = document.getElementById("num1").value;
  const num2 = document.getElementById("num2").value;

  // Load the Python code from main.py
  const response = await fetch("main.py");
  let pyCode = await response.text();

  // Replace the placeholders with user input
  pyCode = pyCode.replace("{{NUM1}}", num1).replace("{{NUM2}}", num2);

  try {
    const result = await pyodide.runPythonAsync(pyCode);
    document.getElementById("output").textContent = "Result: " + result;
  } catch (err) {
    document.getElementById("output").textContent = "Error: " + err;
  }
}
