import socket
import multiprocessing
from command import Commands

HOST = "0.0.0.0"
PORT = 65525

def handle_client(conn, addr, lock):
    commands = Commands(lock)

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            message = data.decode().strip()
            commands.execute(message, conn)


def run_server():
    lock = multiprocessing.Lock()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()

            p = multiprocessing.Process(
                target=handle_client,
                args=(conn, addr, lock)
            )
            p.daemon = True
            p.start()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_server()
