import random
import socket
import json
import os

FILE = "accounts.json"

def send(conn, msg):
    conn.sendall((msg + "\r\n").encode())

def load_accounts():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_accounts(accounts):
    with open(FILE, "w") as f:
        json.dump(accounts, f)

class Commands:
    def __init__(self, lock):
        self.lock = lock
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

    def execute(self, message, conn):
        if not message:
            return

        parts = message.split()
        cmd = parts[0].upper()
        args = parts[1:]

        if cmd not in self.commands:
            send(conn, "ER Unknown command")
            return

        try:
            self.commands[cmd](conn, args)
        except Exception:
            send(conn, "ER Chyba v aplikaci, prosím zkuste to později.")

    def bank_code(self, conn, args):
        send(conn, f"BC {self.get_my_ip()}")

    def account_create(self, conn, args):
        ip = self.get_my_ip()

        with self.lock:
            accounts = load_accounts()

            while True:
                acc = random.randint(10000, 99999)
                key = f"{acc}/{ip}"
                if key not in accounts:
                    accounts[key] = 0
                    save_accounts(accounts)
                    send(conn, f"AC {key}")
                    return

    def account_deposit(self, conn, args):
        if len(args) != 2:
            send(conn, "ER číslo bankovního účtu a částka není ve správném formátu.")
            return

        key, amount = args
        if key.split('/')[1] != self.get_my_ip():
            self.forward_command(key.split('/')[1],f"AD {key} {amount}")
        else:
            try:
                amount = int(amount)
            except:
                send(conn, "ER číslo bankovního účtu a částka není ve správném formátu.")
                return

            with self.lock:
                accounts = load_accounts()

                if key not in accounts:
                    send(conn, "ER Formát čísla účtu není správný.")
                    return

                accounts[key] += amount
                save_accounts(accounts)

            send(conn, "AD")

    def account_withdraw(self, conn, args):
        if len(args) != 2:
            send(conn, "ER číslo bankovního účtu a částka není ve správném formátu.")
            return

        key, amount = args
        if key.split('/')[1] != self.get_my_ip():
            self.forward_command(key.split('/')[1],f"AW {key} {amount}")
        else:
            try:
                amount = int(amount)
            except:
                send(conn, "ER číslo bankovního účtu a částka není ve správném formátu.")
                return

            with self.lock:
                accounts = load_accounts()

                if key not in accounts:
                    send(conn, "ER Formát čísla účtu není správný.")
                    return

                if accounts[key] < amount:
                    send(conn, "ER Není dostatek finančních prostředků.")
                    return

                accounts[key] -= amount
                save_accounts(accounts)

            send(conn, "AW")

    def account_balance(self, conn, args):
        if len(args) != 1:
            send(conn, "ER Formát čísla účtu není správný.")
            return

        key = args[0]
        if key.split('/')[1] != self.get_my_ip():
            self.forward_command(key.split('/')[1],f"AB {key}")

        with self.lock:
            accounts = load_accounts()

            if key not in accounts:
                send(conn, "ER Formát čísla účtu není správný.")
                return

            send(conn, f"AB {accounts[key]}")

    def account_remove(self, conn, args):
        if len(args) != 1:
            send(conn, "ER Formát čísla účtu není správný.")
            return

        key = args[0]

        with self.lock:
            accounts = load_accounts()

            if key not in accounts:
                send(conn, "ER Formát čísla účtu není správný.")
                return

            if accounts[key] != 0:
                send(conn, "ER Nelze smazat bankovní účet na kterém jsou finance.")
                return

            del accounts[key]
            save_accounts(accounts)

        send(conn, "AR")

    def bank_total(self, conn, args):
        with self.lock:
            accounts = load_accounts()
            send(conn, f"BA {sum(accounts.values())}")

    def bank_number(self, conn, args):
        with self.lock:
            accounts = load_accounts()
            send(conn, f"BN {len(accounts)}")

    def get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    def forward_command(self,target_ip, command):

        for port in range(65525, 65536):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    s.connect((target_ip, port))
                    s.sendall((command + "\r\n").encode())
                    response = s.recv(1024).decode().strip()
                    return response
            except (ConnectionRefusedError, socket.timeout):
                continue

        return "ER Bank unreachable"