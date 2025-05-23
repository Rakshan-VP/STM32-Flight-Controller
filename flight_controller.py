# flight_controller.py

def flight_controller(cmd):
    # cmd = [roll, pitch, yaw, thrust] all normalized -1 to 1 (except thrust 0-1)
    # Just map directly for demo:
    roll, pitch, yaw, thrust = cmd
    # Motor mixing (simplified)
    m1 = thrust + roll - yaw
    m2 = thrust - roll - yaw
    m3 = thrust - roll + yaw
    m4 = thrust + roll + yaw
    return [m1, m2, m3, m4]
