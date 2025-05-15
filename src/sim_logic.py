import json
import random

def run_simulation(config):
    # Placeholder simulation logic
    roll = round(random.uniform(-1, 1), 2)
    pitch = round(random.uniform(-1, 1), 2)
    yaw = round(random.uniform(-1, 1), 2)
    thrust = round(random.uniform(0, 1), 2)
    motors = [round(1500 + 500 * random.uniform(-1, 1), 2) for _ in range(4)]
    pos = {
        "lat": config['start']['lat'] + random.uniform(-0.0001, 0.0001),
        "lon": config['start']['lon'] + random.uniform(-0.0001, 0.0001),
        "alt": config['start']['alt'] + random.uniform(-1, 1),
    }
    return json.dumps({
        "roll": roll,
        "pitch": pitch,
        "yaw": yaw,
        "thrust": thrust,
        "motors": motors,
        "pos": pos
    })
