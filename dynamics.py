def motor_to_rpyt(m1, m2, m3, m4, T_max, l, I_x, I_y, I_z, k_yaw):
    # Convert motor commands to thrusts
    T1 = m1 * T_max
    T2 = m2 * T_max
    T3 = m3 * T_max
    T4 = m4 * T_max

    # Total thrust
    thrust = T1 + T2 + T3 + T4  # in Newtons

    # Torques
    tau_x = l * (T2 + T3 - T1 - T4)  # roll
    tau_y = l * (T1 + T2 - T3 - T4)  # pitch
    tau_z = k_yaw * (-T1 + T2 - T3 + T4)  # yaw

    # Angular accelerations (simplified model)
    roll = tau_x / I_x
    pitch = tau_y / I_y
    yaw = tau_z / I_z

    return roll, pitch, yaw, thrust
