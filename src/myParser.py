class Parser:
    def __init__(self):
        self.commands = ["BC","AC","AD","AW","AB","AR","BA","BN"]

    def parse(self, command):
        command = command.upper()
        parts = command.split(' ')
        if parts[0] in self.commands:
            return parts
        else:
            return "ER Unknown command"
