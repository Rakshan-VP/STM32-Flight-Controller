def rpyt_to_pwm_motors(roll_pwm, pitch_pwm, yaw_pwm, thrust_pwm):
    m1 = thrust_pwm - roll_pwm + pitch_pwm - yaw_pwm
    m2 = thrust_pwm + roll_pwm + pitch_pwm + yaw_pwm
    m3 = thrust_pwm + roll_pwm - pitch_pwm - yaw_pwm
    m4 = thrust_pwm - roll_pwm - pitch_pwm + yaw_pwm
    return m1, m2, m3, m4
