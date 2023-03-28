from app.buffer import Buffer


class STTBuffer(Buffer):

    def __init__(self):
        self.buffer = ["hello", "world", "!"]
        self.text = ""
        self.cycle = 0

    def add_text(self, text):
        self.text += text

    def cut_string(self):
        self.buffer[self.cycle] = self.text
        self.text = ""
        self.cycle = self.cycle + 1
        if self.cycle == 3:
            self.cycle = 0

    def get_string(self, number=0):
        index = self.output_index(number)
        response = self.buffer[index]
        self.buffer[index] = None
        return response

    def dump(self) -> str:
        return self.get_string(0)

    def is_ready_dump(self, number=0):
        index = self.output_index(number)
        if self.buffer[index] == None:
            return False
        else:
            return True

    def output_index(self, number=0):
        index = self.cycle + number - 1
        if index < 0:
            index = index + 3
        elif index > 2:
            index = index - 3
        return index
