import socket
import threading
import command
import myParser

HOST = "127.0.0.1"
PORT = 65525
p = myParser.Parser()
cur_command = command.Commands()

def listen():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()


def handle_peer(conn, addr):
    with conn:
        data = conn.recv(1024)
        if not data:
            return

        msg = p.parse(data)
        if msg.startswith("ER"):
            conn.sendall(msg.encode())
        else:
            cur_command.execute(msg, conn)

def local_command_loop():
    print("\nEnter command :")
    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue

        class DummyConn:
            def sendall(self, data):
                print(data.decode().strip())

        dummy_conn = DummyConn()
        cur_command.execute(cmd, dummy_conn)

if __name__ == "__main__":
    threading.Thread(target=listen, daemon=True).start()
    local_command_loop()
