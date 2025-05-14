async function loadPyodideAndRun() {
    let pyodide = await loadPyodide();

    // Load the Python file (main.py) dynamically
    const response = await fetch('src/main.py');
    const pythonCode = await response.text();

    // Execute the Python code and check for errors
    try {
        pyodide.runPython(pythonCode);
        console.log("Python code loaded successfully.");
    } catch (error) {
        console.error("Error in Python code execution: ", error);
    }

    // Button click handler for submitting the RPYT inputs
    document.getElementById('submitBtn').addEventListener('click', () => {
        // Get the input values for roll, pitch, yaw, and thrust
        const roll = parseFloat(document.getElementById('roll').value);
        const pitch = parseFloat(document.getElementById('pitch').value);
        const yaw = parseFloat(document.getElementById('yaw').value);
        const thrust = parseFloat(document.getElementById('thrust').value);

        // Validate the inputs
        if (roll < -1 || roll > 1 || pitch < -1 || pitch > 1 || yaw < -1 || yaw > 1 || thrust < -1 || thrust > 1) {
            alert("Please enter values between -1 and 1 for roll, pitch, yaw, and thrust.");
            return;
        }

        console.log(`Received input - Roll: ${roll}, Pitch: ${pitch}, Yaw: ${yaw}, Thrust: ${thrust}`);

        // Call the Python function to calculate PWM signals
        try {
            const pwmSignals = pyodide.globals.convert_to_pwm(roll, pitch, yaw, thrust);
            console.log("PWM Signals:", pwmSignals);  // Debugging line to check the output of the Python function

            // Update the motor PWM values in the HTML
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
