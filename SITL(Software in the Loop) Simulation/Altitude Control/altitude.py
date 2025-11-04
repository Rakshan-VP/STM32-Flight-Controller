import socket
import struct
import threading
import time

HOST = '127.0.0.1'
SEND_PORT = 55000   # Python -> Simulink (commands)
RECV_PORT = 55001   # Simulink -> Python (telemetry)

# =======================================================
# Altitude schedule [end_time (s), altitude (m)]
# =======================================================
schedule = [
    [10.0, 25.0],   # 0–10 s → 25 m
    [25.0, 15.0],   # 10–25 s → 15 m
    [40.0, 10.0]    # 25–40 s → 10 m
]

telemetry_time = 0.0   # shared variable
ramp_duration = 10.0   # seconds to descend to zero


# -------------------------------------------------------
# Thread 1: SEND [1, alt] based on telemetry time
# -------------------------------------------------------
def send_commands():
    global telemetry_time
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SEND_PORT))
    server.listen(1)
    print(f"[SEND] Waiting for Simulink on port {SEND_PORT}...")
    conn, addr = server.accept()
    print(f"[SEND] Connected to Simulink at {addr}")

    try:
        while True:
            alt = schedule[-1][1]  # default = last altitude

            # normal schedule tracking
            for end_time, target_alt in schedule:
                if telemetry_time < end_time:
                    alt = target_alt
                    break
            else:
                # After schedule ends, ramp down smoothly to 0
                final_time = schedule[-1][0]
                final_alt = schedule[-1][1]
                elapsed = telemetry_time - final_time
                if elapsed < ramp_duration:
                    # linear ramp down to zero
                    alt = final_alt * (1 - elapsed / ramp_duration)
                else:
                    alt = 0.0

            cmd = [1.0, alt]
            data = struct.pack('>2d', *cmd)
            conn.sendall(data)
            print(f"[SEND] t={telemetry_time:6.2f}s -> alt_cmd={alt:6.2f}")
            time.sleep(0.1)
    except (ConnectionResetError, BrokenPipeError):
        print("[SEND] Simulink connection closed.")
    finally:
        conn.close()
        server.close()


# -------------------------------------------------------
# Thread 2: RECEIVE telemetry from Simulink
# -------------------------------------------------------
def receive_telemetry():
    global telemetry_time
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, RECV_PORT))
    server.listen(1)
    print(f"[RECV] Waiting for Simulink on port {RECV_PORT}...")
    conn, addr = server.accept()
    print(f"[RECV] Connected to Simulink at {addr}")

    try:
        while True:
            data = conn.recv(8 * 13)
            if len(data) < 104:
                continue
            telemetry = struct.unpack('>13d', data)
            telemetry_time = telemetry[0]
            # Optional debug
            # print(f"[RECV] t={telemetry_time:.2f}")
    except (ConnectionResetError, BrokenPipeError):
        print("[RECV] Simulink connection closed.")
    finally:
        conn.close()
        server.close()


# -------------------------------------------------------
# Main
# -------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=send_commands, daemon=True).start()
    threading.Thread(target=receive_telemetry, daemon=True).start()

    while True:
        time.sleep(1)
