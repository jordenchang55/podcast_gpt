import logging
import threading
import time

# from buffer import SpeechBuffer
from STT.buffer import Buffer
from STT.speechtotext import SpeechClient
from client import ChatClient, MicClient
from constants import EXIT_KEYWORDS
from logger import LoggerFormat

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
    speech_buffer = Buffer()
    speech_client = SpeechClient(speech_buffer, timeout=5, maximum=30)
    block_event = threading.Event()
    speech_thread = threading.Thread(name='speech', target=speech_client.start,
                                         kwargs={
                                             "block_event": block_event
                                         })
    speech_thread.start()
    while True:
        if speech_buffer.is_ready_dump():
            logging.debug("Buffer: %s" % speech_buffer.get_string())


def main():
    stop_event = threading.Event()
    buffer = SpeechBuffer(stop_event, timeout=15)
    chat_client = ChatClient(buffer, frequency_penalty=0.1, presence_penalty=0.2)

    with open('./resources/podcast_setup_prompt.txt', 'r') as f:
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
