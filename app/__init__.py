import logging
from threading import Event

from .STT.buffer import STTBuffer
from .STT.speechtotext import ListenClient
from .TTS.texttospeech import SpeechClient
from .buffer import SpeechBuffer, TestBuffer
from .client import ChatClient
from .web_socket import WebSocketClient, WebSocketCallback


class App(WebSocketCallback):
    """
    This class integrates each external service client to listen the dialog of podcast and play corresponding comment
    from ChatGPT with triggers from user.
    """

    def __init__(self):
        self.stop_event = Event()
        self.buffer = STTBuffer()
        self.listen_client = ListenClient(self.buffer, 1, 30)
        self.chat_client = ChatClient(self.buffer)
        self.web_socket_client = WebSocketClient()
        self.speech_client = SpeechClient()

    def start(self):
        self.web_socket_client.start(callback=self)

    def stop(self):
        self.stop_event.set()
        self.listen_client.stop()
        self.web_socket_client.stop()
        self.chat_client.stop()

    def on_connected(self):
        logging.info("Web socket connected")
        if self.stop_event.is_set():
            self.stop_event.clear()
        with open('app/resources/podcast_setup_prompt.txt', 'r') as f:
            prompt = f.read()
        self.listen_client.start()
        self.chat_client.start(self.stop_event, prompt, lambda msg: self._on_gpt_response(msg))

    def on_disconnected(self):
        logging.info("Web socket disconnected")
        self.stop_event.set()
        self.listen_client.stop()
        self.chat_client.stop()

    def on_update(self, event):
        if event['event'] == 'speak':
            self.chat_client.add_actual_response(event['text'])
            self.listen_client.stop()
            self.speech_client.speak(event['text'])
            self.listen_client.start()

    def _on_gpt_response(self, text):
        self.web_socket_client.send(text)
