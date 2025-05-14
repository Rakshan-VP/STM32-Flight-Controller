import numpy as np

def convert_to_pwm(roll, pitch, yaw, thrust):
    # Constants for the quadrotor motor configuration
    max_pwm = 2000
    min_pwm = 1000
    pwm_range = max_pwm - min_pwm

    # Calculate the motor PWM values based on input RPYT
    front_left = thrust + roll + pitch + yaw
    front_right = thrust - roll + pitch - yaw
    back_left = thrust + roll - pitch - yaw
    back_right = thrust - roll - pitch + yaw

    # Normalize to PWM range (1000 to 2000)
    motors = np.array([front_left, front_right, back_left, back_right])
    motors = np.clip(motors, -1, 1)  # Ensure the values are within [-1, 1]
    pwm_signals = ((motors + 1) / 2) * pwm_range + min_pwm

    return pwm_signals.tolist()
