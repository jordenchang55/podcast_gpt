class Buffer:
    """
    This class defines the interface of Buffer.
    """

    def add_text(self, text: str):
        raise NotImplementedError()

    def is_ready_dump(self) -> bool:
        raise NotImplementedError()

    def dump(self) -> str:
        raise NotImplementedError()


class TestBuffer(Buffer):
    """
    This buffer is used for testing. It provides functions to set fake data.
    """

    def __init__(self):
        self.text = ""
        self.is_ready = False

    def add_text(self, text: str):
        self.text += text

    def is_ready_dump(self) -> bool:
        return self.is_ready

    def dump(self) -> str:
        dump_text = self.text
        self.text = ""
        self.is_ready = False
        return dump_text

    def set_ready_dump(self, is_ready: bool):
        self.is_ready = is_ready
