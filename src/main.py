import math

def get_rpyt_at_time(time):
    # Example: Simple linear motion for RPYT
    roll = math.sin(time) * 45  # Roll oscillates between -45° to 45°
    pitch = math.cos(time) * 45  # Pitch oscillates between -45° to 45°
    yaw = time * 10  # Yaw increases with time
    thrust = 1000  # Constant thrust for simplicity
    
    return roll, pitch, yaw, thrust
