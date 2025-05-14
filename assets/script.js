async function loadPyodideAndRun() {
    let pyodide = await loadPyodide();

    // Load the Python file (main.py) dynamically
    const response = await fetch('src/main.py');
    const pythonCode = await response.text();

    pyodide.runPython(pythonCode);

    document.getElementById('submitBtn').addEventListener('click', () => {
        const roll = parseFloat(document.getElementById('roll').value);
        const pitch = parseFloat(document.getElementById('pitch').value);
        const yaw = parseFloat(document.getElementById('yaw').value);
        const thrust = parseFloat(document.getElementById('thrust').value);

        // Call the Python function to calculate PWM signals
        const pwmSignals = pyodide.globals.convert_to_pwm(roll, pitch, yaw, thrust);

        // Plot the PWM signals on the canvas
        plotPWM(pwmSignals);
    });
}

function plotPWM(pwmSignals) {
    const canvas = document.getElementById('plotCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw the PWM signals
    const labels = ['Front Left', 'Front Right', 'Back Left', 'Back Right'];
    const motorColors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00'];
    
    pwmSignals.forEach((pwm, index) => {
        ctx.beginPath();
        ctx.arc(150 + (index * 180), 200, 30, 0, 2 * Math.PI);
        ctx.fillStyle = motorColors[index];
        ctx.fill();
        
        ctx.fillStyle = '#000000';
        ctx.fillText(labels[index], 150 + (index * 180), 250);
        ctx.fillText(`${Math.round(pwm)}`, 150 + (index * 180), 180);
    });
}

loadPyodideAndRun();
