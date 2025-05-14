async function loadPyodideAndRun() {
    let pyodide = await loadPyodide();
    await pyodide.loadPackage('numpy');

    const response = await fetch('src/main.py');
    const pythonCode = await response.text();

    try {
        pyodide.runPython(pythonCode);
        console.log("Python code loaded successfully.");
    } catch (error) {
        console.error("Error in Python code execution: ", error);
        return;
    }

    document.getElementById('submitBtn').addEventListener('click', () => {
        const roll = parseFloat(document.getElementById('roll').value);
        const pitch = parseFloat(document.getElementById('pitch').value);
        const yaw = parseFloat(document.getElementById('yaw').value);
        const thrust = parseFloat(document.getElementById('thrust').value);

        if ([roll, pitch, yaw, thrust].some(v => v < -1 || v > 1 || isNaN(v))) {
            alert("Please enter values between -1 and 1 for all fields.");
            return;
        }

        console.log(`Received input - Roll: ${roll}, Pitch: ${pitch}, Yaw: ${yaw}, Thrust: ${thrust}`);

        try {
            const pwmSignals = pyodide.globals.get("convert_to_pwm")(roll, pitch, yaw, thrust).toJs();
            document.getElementById('flMotor').textContent = Math.round(pwmSignals[0]);
            document.getElementById('frMotor').textContent = Math.round(pwmSignals[1]);
            document.getElementById('blMotor').textContent = Math.round(pwmSignals[2]);
            document.getElementById('brMotor').textContent = Math.round(pwmSignals[3]);
        } catch (error) {
            console.error("Error while calling Python function: ", error);
        }
    });
}

loadPyodideAndRun();
