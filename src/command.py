import random
import socket

class Commands:
    def __init__(self):
        self.commands = {
            "BC": self.bank_code,
            "AC": self.account_create,
            "AD": self.account_deposit,
            "AW": self.account_withdraw,
            "AB": self.account_balance,
            "AR": self.account_remove,
            "BA": self.bank_total,
            "BN": self.bank_number,
        }
        self.accounts = {}

    def execute(self, message, conn):
        parts = message.strip().split()
        cmd = parts[0].upper()
        args = parts[1:]

        if cmd not in self.commands:
            conn.sendall(b"ER Unknown command")
            return

        try:
            self.commands[cmd](conn, args)
        except Exception as e:
            conn.sendall(f"ER {str(e)}".encode())

    def bank_code(self, conn, args):
        ip = args[0] if args else self.get_my_ip()
        conn.sendall(f"BC {ip}".encode())

    def account_create(self, conn, args):
        ip = self.get_my_ip()
        while True:
            acc = random.randint(10000, 99999)
            key = f"{acc}/{ip}"
            if key not in self.accounts:
                self.accounts[key] = 0
                conn.sendall(f"AC {key}".encode())
                break

    def account_deposit(self, conn, args):
        if len(args) != 2:
            conn.sendall(b"ER Invalid AD format")
            return
        key, amount = args
        try:
            amount = int(amount)
        except:
            conn.sendall(b"ER Amount not integer")
            return
        if key not in self.accounts:
            conn.sendall(b"ER Account does not exist")
            return
        self.accounts[key] += amount
        conn.sendall(b"AD")

    def account_withdraw(self, conn, args):
        if len(args) != 2:
            conn.sendall(b"ER Invalid AW format")
            return
        key, amount = args
        try:
            amount = int(amount)
        except:
            conn.sendall(b"ER Amount not integer")
            return
        if key not in self.accounts:
            conn.sendall(b"ER Account does not exist")
            return
        if self.accounts[key] < amount:
            conn.sendall(b"ER Insufficient funds")
            return
        self.accounts[key] -= amount
        conn.sendall(b"AW")

    def account_balance(self, conn, args):
        if len(args) != 1:
            conn.sendall(b"ER Invalid AB format")
            return
        key = args[0]
        if key not in self.accounts:
            conn.sendall(b"ER Account does not exist")
            return
        conn.sendall(f"AB {self.accounts[key]}".encode())

    def account_remove(self, conn, args):
        if len(args) != 1:
            conn.sendall(b"ER Invalid AR format")
            return
        key = args[0]
        if key not in self.accounts:
            conn.sendall(b"ER Account does not exist")
            return
        if self.accounts[key] != 0:
            conn.sendall(b"ER Cannot remove account with funds")
            return
        del self.accounts[key]
        conn.sendall(b"AR")

    def bank_total(self, conn, args):
        total = sum(self.accounts.values())
        conn.sendall(f"BA {total}".encode())

    def bank_number(self, conn, args):
        conn.sendall(f"BN {len(self.accounts)}".encode())

    def get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
