import logging
import threading

from buffer import SpeechBuffer
from client import ChatClient
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

    listening_thread = threading.Thread(name="listening", target=buffer.start)
    listening_thread.start()

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

    response_thread.join()
    background_thread.join()
    listening_thread.join()


if __name__ == '__main__':
    main()
