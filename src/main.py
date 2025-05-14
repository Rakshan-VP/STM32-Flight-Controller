import numpy as np

def convert_to_pwm(roll, pitch, yaw, thrust):
    mix = np.array([
        [1, -1, -1, 1],  # Front-left
        [1, -1, 1, -1],  # Front-right
        [1, 1, -1, -1],  # Back-left
        [1, 1, 1, 1]     # Back-right
    ])
    inputs = np.array([thrust, roll, pitch, yaw])
    motor_outputs = mix @ inputs
    motor_outputs = np.clip(motor_outputs, -2, 2)
    pwm = 1000 + ((motor_outputs + 2) / 4) * 1000
    return pwm.tolist()
