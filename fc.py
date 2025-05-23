import numpy as np

# Initialize integral and previous error terms as globals or outside function for persistence
integral_error = np.zeros(4)
prev_error = np.zeros(4)

def fc_step(r, p, y, T, gains, dt=0.01):
    global integral_error, prev_error

    # Current error vector: assuming desired setpoint is zero for r, p, y, and thrust target T
    error = np.array([r, p, y, T])

    Kp = np.array([g[0] for g in gains])
    Ki = np.array([g[1] for g in gains])
    Kd = np.array([g[2] for g in gains])

    # Integral term update
    integral_error += error * dt

    # Derivative term
    derivative = (error - prev_error) / dt

    # PID output for each control axis
    pid_output = Kp * error + Ki * integral_error + Kd * derivative

    prev_error = error

    # Mixer for quadcopter (simplified)
    # Motor layout: M1, M2, M3, M4
    # Mix pitch, roll, yaw corrections and add thrust
    motors = np.zeros(4)
    motors[0] = pid_output[1] + pid_output[0] - pid_output[2] + pid_output[3]  # Front Right
    motors[1] = pid_output[1] + pid_output[0] + pid_output[2] + pid_output[3]  # Front Left
    motors[2] = pid_output[1] - pid_output[0] - pid_output[2] + pid_output[3]  # Rear Left
    motors[3] = pid_output[1] - pid_output[0] + pid_output[2] + pid_output[3]  # Rear Right

    # Clamp motor PWM signals between 1000 and 2000
    output_pwm = np.clip(motors, 1000, 2000)

    return output_pwm, motors
