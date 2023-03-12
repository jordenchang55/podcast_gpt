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
