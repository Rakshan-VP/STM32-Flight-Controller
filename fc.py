import numpy as np

prev_error = np.zeros(4)
integral = np.zeros(4)
actual = np.array([1500, 1500, 1500, 1000])  # initialize thrust at 1000 PWM

def fc_step(r, p, y, T, gains):
    global prev_error, integral, actual
    
    target = np.array([r, p, y, T])
    
    error = target - actual
    integral += error * 0.1
    derivative = (error - prev_error) / 0.1
    prev_error = error
    
    Kp = np.array([g[0] for g in gains])
    Ki = np.array([g[1] for g in gains])
    Kd = np.array([g[2] for g in gains])
    
    output = Kp * error + Ki * integral + Kd * derivative
    
    output_pwm = 1500 + output
    output_pwm = np.clip(output_pwm, 1000, 2000)
    
    actual = output_pwm
    
    roll, pitch, yaw, thrust = output_pwm
    m1 = thrust + pitch - roll + yaw
    m2 = thrust + pitch + roll - yaw
    m3 = thrust - pitch + roll + yaw
    m4 = thrust - pitch - roll - yaw
    motors = np.clip([m1, m2, m3, m4], 1000, 2000)
    
    return output_pwm, motors
