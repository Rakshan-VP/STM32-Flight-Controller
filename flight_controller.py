def pwm_to_normalized(pwm):
    return (pwm - 1500) / 500

def mix_controls(roll, pitch, yaw, thrust):
    m1 = thrust + roll + pitch - yaw
    m2 = thrust - roll + pitch + yaw
    m3 = thrust - roll - pitch - yaw
    m4 = thrust + roll - pitch + yaw
    return [max(1000, min(2000, m)) for m in [m1, m2, m3, m4]]

def flight_controller(cmd):
    r = pwm_to_normalized(cmd['roll'])
    p = pwm_to_normalized(cmd['pitch'])
    y = pwm_to_normalized(cmd['yaw'])
    t = (cmd['thrust'] - 1000) / 1000
    motors = mix_controls(r, p, y, 1000 + t * 1000)
    return motors
