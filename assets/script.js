async function loadPyodideAndRun() {
    let pyodide = await loadPyodide();

    // Load the Python file (main.py) dynamically
    const response = await fetch('src/main.py');
    const pythonCode = await response.text();

    // Execute the Python code
    pyodide.runPython(pythonCode);

    document.getElementById('submitBtn').addEventListener('click', () => {
        // Get the input values for roll, pitch, yaw, and thrust
        const roll = parseFloat(document.getElementById('roll').value);
        const pitch = parseFloat(document.getElementById('pitch').value);
        const yaw = parseFloat(document.getElementById('yaw').value);
        const thrust = parseFloat(document.getElementById('thrust').value);

        // Check if the inputs are within valid ranges
        if (roll < -1 || roll > 1 || pitch < -1 || pitch > 1 || yaw < -1 || yaw > 1 || thrust < -1 || thrust > 1) {
            alert("Please enter values between -1 and 1 for roll, pitch, yaw, and thrust.");
            return;
        }

        // Call the Python function to calculate PWM signals
        const pwmSignals = pyodide.globals.convert_to_pwm(roll, pitch, yaw, thrust);

        // Plot the PWM signals on the canvas
        plotPWM(pwmSignals);
    });
}

function plotPWM(pwmSignals) {
    const canvas = document.getElementById('plotCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the previous plot

    // Draw the PWM signals
    const labels = ['Front Left', 'Front Right', 'Back Left', 'Back Right'];
    const motorColors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00'];

    // Plot each motor PWM signal
    pwmSignals.forEach((pwm, index) => {
        const motorHeight = pwm - 1000; // Normalize PWM value to the range 0 to 1000
        const motorWidth = 50; // Width of the circle

        // Plot each motor PWM signal as a vertical bar on the canvas
        ctx.beginPath();
        ctx.arc(150 + (index * 180), 200, motorWidth, 0, 2 * Math.PI);
        ctx.fillStyle = motorColors[index];
        ctx.fill();

        // Display text labels
        ctx.fillStyle = '#000000';
        ctx.fillText(labels[index], 150 + (index * 180), 250);
        ctx.fillText(`${Math.round(pwm)}`, 150 + (index * 180), 180);
    });
}

loadPyodideAndRun();
