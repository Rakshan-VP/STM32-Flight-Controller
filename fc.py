import numpy as np

prev_error = np.zeros(4)
integral = np.zeros(4)

def fc_step(r, p, y, T, gains):  # gains shape (4,3) with columns: kp, ki, kd
    target = np.array([r, p, y, T])  # in 1000-2000 scale
    actual = np.array([1500, 1500, 1500, 1500])  # assumed current state in PWM scale

    global prev_error, integral
    error = target - actual  # error in PWM units (e.g. -500 to +500)
    integral += error * 0.1
    derivative = (error - prev_error) / 0.1
    prev_error = error

    # Extract gains: shape is (4,3) with columns kp, ki, kd
    Kp = np.array([g[0] for g in gains])
    Ki = np.array([g[1] for g in gains])
    Kd = np.array([g[2] for g in gains])

    output = Kp * error + Ki * integral + Kd * derivative  # all in PWM units
    output_pwm = 1500 + output  # center around 1500
    output_pwm = np.clip(output_pwm, 1000, 2000)

    roll, pitch, yaw, thrust = output_pwm
    m1 = thrust + pitch - roll + yaw
    m2 = thrust + pitch + roll - yaw
    m3 = thrust - pitch + roll + yaw
    m4 = thrust - pitch - roll - yaw
    motors = np.clip([m1, m2, m3, m4], 1000, 2000)

    return output_pwm, motors
