def motor_to_rpyt(m1, m2, m3, m4, T_max, max_roll, max_pitch, max_yaw):
    # Thrusts from normalized motor commands
    T1 = m1 * T_max
    T2 = m2 * T_max
    T3 = m3 * T_max
    T4 = m4 * T_max

    # Total thrust
    thrust = T1 + T2 + T3 + T4

    # RPY angular accelerations (scaled)
    roll  = (m2 + m3 - m1 - m4) * max_roll
    pitch = (m1 + m2 - m3 - m4) * max_pitch
    yaw   = (-m1 + m2 - m3 + m4) * max_yaw

    return roll, pitch, yaw, thrust
