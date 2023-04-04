import logging
import threading
from threading import Event

from app.STT.buffer import STTBuffer
from app.STT.speechtotext import ListenClient
from app.TTS.texttospeech import SpeechClient
from app.client import ChatClient, WebSocketClient
from app.constants import EXIT_KEYWORDS
from app.logger import LoggerFormat

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
fh = logging.FileHandler('test.log', 'w+')
fh.setLevel(logging.INFO)
formatter = LoggerFormat(fmt='[%(levelname)s] [%(threadName)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(fh)

def main():
    buffer = STTBuffer()
    stop_event = Event()
    listen_client = ListenClient(buffer, 1, 30)
    chat_client = ChatClient(buffer)
    speech_client = SpeechClient()
    web_socket_client = WebSocketClient()

    if stop_event.is_set():
        stop_event.clear()
    with open('app/resources/podcast_setup_prompt.txt', 'r') as f:
        prompt = f.read()

    listen_thread = threading.Thread(name='speech', target=listen_client.start,
                                         kwargs={
                                             "block_event": stop_event
                                         })

    GPT_thread = threading.Thread(name='GPT', target=chat_client.start,
                                         kwargs={
                                             "stop_event": stop_event,
                                             "system_message": prompt,
                                             "callback": lambda msg: web_socket_client.send(msg)
                                         })

    GPT_thread.start()
    listen_thread.start()

    logging.info("Now let's say something or command below:\n"
                 "1. type 'history' to list the current conversation\n"
                 "2. type %s to finish", EXIT_KEYWORDS)

    while True:
        try:
            if chat_client.peek_response():
                speech_str = chat_client.take_response()
                logging.info("[GPT] - %s", chat_client.take_response())
                speech_client.speak(speech_str)
        except KeyboardInterrupt:
            stop_event.set()
            break
    
    stop_event.set()
    listen_client.stop()
    chat_client.stop()

    GPT_thread.join()
    listen_thread.join()

if __name__ == '__main__':
    main()
