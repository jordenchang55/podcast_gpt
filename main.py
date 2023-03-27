import logging
import threading

from app.STT.buffer import Buffer
from app.STT.speechtotext import ListenClient
from app.TTS.texttospeech import SpeechClient
from app.buffer import SpeechBuffer
from app.client import ChatClient, MicClient
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


def read_response(client: ChatClient, stop_event):
    logging.debug("Started listening response on %s", client)
    while True:
        if stop_event.is_set():
            break
        if client.peek_response():
            logging.info("[GPT] - %s", client.take_response())


def test():
    listen_buffer = Buffer()
    listen_client = ListenClient(listen_buffer, timeout=5, maximum=30)
    block_event = threading.Event()
    listen_thread = threading.Thread(name='speech', target=listen_client.start,
                                         kwargs={
                                             "block_event": block_event
                                         })
    listen_thread.start()

    speech_client = SpeechClient()
    while True:
        if listen_buffer.is_ready_dump():
            speech_str = listen_buffer.get_string()
            logging.debug("Buffer: %s" % speech_str)
            speech_client.speak_to_file( speech_str, "test.wav")


def main():
    stop_event = threading.Event()
    buffer = SpeechBuffer(stop_event, timeout=15)
    chat_client = ChatClient(buffer, frequency_penalty=0.1, presence_penalty=0.2)

    with open('app/resources/podcast_setup_prompt.txt', 'r') as f:
        prompt = f.read()
    background_thread = threading.Thread(name='background', target=chat_client.start,
                                         kwargs={
                                             "stop_event": stop_event,
                                             "system_message": prompt
                                         })
    background_thread.start()

    response_thread = threading.Thread(name='response', target=read_response, args=[chat_client, stop_event])
    response_thread.start()

    logging.info("Now let's say something or command below:\n"
                 "1. type 'history' to list the current conversation\n"
                 "2. type %s to finish", EXIT_KEYWORDS)

    mic_client = MicClient(buffer)
    mic_client.start()

    while True:
        try:
            text = input()
            if text in EXIT_KEYWORDS:
                stop_event.set()
                break
            elif text == 'history':
                chat_client.print_history()
                continue
        except KeyboardInterrupt:
            stop_event.set()
            break

    mic_client.stop()
    response_thread.join()
    background_thread.join()


if __name__ == '__main__':
    test()
