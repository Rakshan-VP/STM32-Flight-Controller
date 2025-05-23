import numpy as np

prev_error = np.zeros(4)
integral = np.zeros(4)

def fc_step(r, p, y, T, gains):
    global prev_error, integral

    gains = np.array(gains)  # convert input to numpy array

    target = np.array([(r-1500)/500, (p-1500)/500, (y-1500)/500, (T-1500)/500])
    actual = np.zeros(4)

    error = target - actual
    integral += error * 0.1
    derivative = (error - prev_error) / 0.1
    prev_error = error

    Kp = gains[:, 0]
    Ki = gains[:, 1]
    Kd = gains[:, 2]

    output = Kp * error + Ki * integral + Kd * derivative
    output_pwm = 1500
    output_pwm = np.clip(output_pwm, 1000, 2000)

    roll, pitch, yaw, thrust = output_pwm
    m1 = thrust + pitch - roll + yaw
    m2 = thrust + pitch + roll - yaw
    m3 = thrust - pitch + roll + yaw
    m4 = thrust - pitch - roll - yaw
    motors = np.clip([m1, m2, m3, m4], 1000, 2000)

    return output_pwm, motors
