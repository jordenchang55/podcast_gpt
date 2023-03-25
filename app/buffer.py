import queue
import time
from collections import Counter
from threading import Event


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


class SpeechBuffer(Buffer):
    def __init__(self, stop_event: Event, timeout=120, maximum=200, language_code="zh"):
        self._stop_event = stop_event
        self.timeout = timeout
        self.maximum_words = maximum
        # a BCP-47 language tag "zh" "en-US"
        self.language_code = language_code

        self._buffer = queue.Queue()
        self._counter = Counter()
        self._start_time = time.monotonic()
        self._stop_listen_event = Event()

    def add_text(self, text: str):
        self._buffer.put(text)
        self._counter.update(['words'] * len(text))

    def is_ready_dump(self) -> bool:
        return self._counter['words'] > self.maximum_words or (
                time.monotonic() - self._start_time > self.timeout and self._counter['words'] > 0)

    def dump(self) -> str:
        self._counter.clear()
        self._start_time = time.monotonic()
        s = ""
        while not self._buffer.empty():
            s += self._buffer.get()
        return s
