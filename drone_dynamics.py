# drone_dynamics.py

def motor_to_rpyt(motors):
    # Simplified inverse mixing demo (just average)
    m1, m2, m3, m4 = motors
    roll = (m1 - m2 - m3 + m4) / 4
    pitch = (m1 + m2 - m3 - m4) / 4
    yaw = (-m1 - m2 + m3 + m4) / 4
    thrust = sum(motors) / 4
    return [roll, pitch, yaw, thrust]

# For 2D path simulation, you can extend this file later
def update_path(vx, vy):
    # Dummy placeholder for Pyodide usage
    return [0, 0]
