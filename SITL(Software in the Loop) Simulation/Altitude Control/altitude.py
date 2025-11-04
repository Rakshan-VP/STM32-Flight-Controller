import socket
import struct
import threading
import time

HOST = '127.0.0.1'
SEND_PORT = 55000   # Python -> Simulink  (commands)
RECV_PORT = 55001   # Simulink -> Python  (telemetry)

# ------------------------------------------------------
# Thread 1: SEND commands to Simulink (port 55000)
# ------------------------------------------------------
def send_commands():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, SEND_PORT))
    server.listen(1)
    print(f"[SEND] Waiting for Simulink on port {SEND_PORT}...")
    conn, addr = server.accept()
    print(f"[SEND] Connected to Simulink at {addr}")

    try:
        while True:
            # Example command vector (2 doubles)
            commands = [1.0, 25.0]
            data = struct.pack('>2d', *commands)
            conn.sendall(data)
            print(f"[SEND] Sent commands: {commands}")
            time.sleep(0.1)  # Match Simulink sample time
    except (ConnectionResetError, BrokenPipeError):
        print("[SEND] Simulink connection closed.")
    finally:
        conn.close()
        server.close()

# ------------------------------------------------------
# Thread 2: RECEIVE 12×1 telemetry vector (port 55001)
# ------------------------------------------------------
def receive_telemetry():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, RECV_PORT))
    server.listen(1)
    print(f"[RECV] Waiting for Simulink on port {RECV_PORT}...")
    conn, addr = server.accept()
    print(f"[RECV] Connected to Simulink at {addr}")

    try:
        while True:
            # Expecting 12 doubles (96 bytes)
            data = conn.recv(8 * 12)
            if len(data) < 96:
                continue  # skip partial reads
            telemetry = struct.unpack('>12d', data)
            print(f"[RECV] Telemetry: {telemetry}")
    except (ConnectionResetError, BrokenPipeError):
        print("[RECV] Simulink connection closed.")
    finally:
        conn.close()
        server.close()

# ------------------------------------------------------
# Launch both threads
# ------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=send_commands, daemon=True).start()
    threading.Thread(target=receive_telemetry, daemon=True).start()

    # Keep main thread alive
    while True:
        time.sleep(1)
