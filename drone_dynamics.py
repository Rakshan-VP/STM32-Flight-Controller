def motor_to_rpyt(motors):
    thrust = sum(motors) / 4
    roll = (motors[0] + motors[3] - motors[1] - motors[2]) / 4
    pitch = (motors[0] + motors[1] - motors[2] - motors[3]) / 4
    yaw = (-motors[0] + motors[1] + motors[2] - motors[3]) / 4
    return {
        'roll': roll / 500,
        'pitch': pitch / 500,
        'yaw': yaw / 500,
        'thrust': (thrust - 1000) / 1000
    }
