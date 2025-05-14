let pyodideReady = loadPyodide();

async function runPython() {
  await pyodideReady;

  const num1 = document.getElementById("num1").value;
  const num2 = document.getElementById("num2").value;

  // Load main.py as a string
  const response = await fetch("main.py");
  let pyCode = await response.text();

  // Replace placeholders in the Python code
  pyCode = pyCode.replace("{{NUM1}}", num1).replace("{{NUM2}}", num2);

  try {
    const result = await pyodide.runPythonAsync(pyCode);
    document.getElementById("output").textContent = "Result: " + result;
  } catch (err) {
    document.getElementById("output").textContent = "Error: " + err;
  }
}
