import tkinter as tk
from tkinter import scrolledtext
import logging
import threading

class TextHandler(logging.Handler):
    """
    Special logging handler that sends text to the Tkinter window.
    Must be thread-safe as the server runs in a different thread.
    """

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)  # Auto-scroll down

        # Tkinter is not thread-safe, schedule update in main thread
        self.text_widget.after(0, append)

class BankGUI:
    def __init__(self, bank_node):
        self.bank_node = bank_node
        self.root = tk.Tk()
        self.root.title(f"P2P Bank Node - {self.bank_node.my_ip}:{self.bank_node.my_port}")
        self.root.geometry("800x700")

        # --- Top Info Panel ---
        info_frame = tk.Frame(self.root, pady=5)
        info_frame.pack(fill=tk.X)

        lbl_info = tk.Label(info_frame, text=f"My IP: {self.bank_node.my_ip} | Port: {self.bank_node.my_port}",
                            font=("Arial", 10, "bold"))
        lbl_info.pack()

        # --- Main Log Area ---
        self.log_area = scrolledtext.ScrolledText(self.root, state='disabled', height=20, bg="#f0f0f0")
        self.log_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Setup redirection of logs to window
        self.setup_gui_logging()

        # --- Input Panel ---
        input_frame = tk.Frame(self.root, pady=10)
        input_frame.pack(fill=tk.X, padx=10)

        self.cmd_entry = tk.Entry(input_frame, font=("Courier", 12))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.cmd_entry.bind('<Return>', self.send_command)  # Send on Enter

        btn_send = tk.Button(input_frame, text="Send", command=self.send_command, bg="#dddddd")
        btn_send.pack(side=tk.RIGHT)

        # --- Quick Commands (Buttons) ---
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill=tk.X)

        quick_cmds = [("My Balance (BA)", "BA"), ("My Clients (BN)", "BN"), ("Create Account (AC)", "AC")]
        for label, code in quick_cmds:
            btn = tk.Button(btn_frame, text=label, command=lambda c=code: self.inject_command(c))
            btn.pack(side=tk.LEFT, padx=5)

    def setup_gui_logging(self):
        """Adds a handler that sends logs to the text area."""
        handler = TextHandler(self.log_area)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)

        # Connect to root logger to catch everything
        logging.getLogger().addHandler(handler)
        logging.info("Waiting for commands...")

    def inject_command(self, cmd_text):
        """Inserts text into input (for buttons)."""
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd_text)
        if cmd_text in ["BA", "BN", "AC"]:  # Immediately send simple commands
            self.send_command()

    def send_command(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        self.cmd_entry.delete(0, tk.END)

        # Log our command
        logging.info(f">>> USER: {cmd}")

        # Run in thread to prevent GUI freezing
        threading.Thread(target=self._execute_async, args=(cmd,), daemon=True).start()

    def _execute_async(self, cmd):
        """Execute command in background."""
        try:
            response = self.bank_node.execute_command(cmd)
            logging.info(f"<<< RESPONSE: {response}")
        except Exception as e:
            logging.error(f"GUI Error: {e}")

    def start(self):
        self.root.mainloop()