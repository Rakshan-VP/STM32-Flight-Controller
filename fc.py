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
    # For example (assuming motor PWM base is 1000 to 2000)
    base_pwm = 1000 + T * 1000  # scale thrust 0-1 to PWM 1000-2000
    motors = np.zeros(4)
    motors[0] = base_pwm + pid_output[1] + pid_output[0] - pid_output[2]  # Front Right
    motors[1] = base_pwm - pid_output[1] + pid_output[0] + pid_output[2]  # Front Left
    motors[2] = base_pwm - pid_output[1] - pid_output[0] - pid_output[2]  # Rear Left
    motors[3] = base_pwm + pid_output[1] - pid_output[0] + pid_output[2]  # Rear Right

    # Clamp motor PWM signals between 1000 and 2000
    output_pwm = np.clip(motors, 1000, 2000)

    return output_pwm, motors
