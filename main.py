import threading
import time

from buffer import TestBuffer
from client import ChatClient
from STT.speechtotext import speechstring

def read_response(client: ChatClient, stop_event):
    print("Started listening response on %s" % client)
    while True:
        if stop_event.is_set():
            break
        if client.peek_response():
            print(client.take_response())


def main():
    stop_event = threading.Event()

    test_buffer = TestBuffer()
    chat_client = ChatClient(test_buffer, frequency_penalty=0.1, presence_penalty=0.2)

    first_message = "Hi, tell me a joke"
    background_thread = threading.Thread(name='background', target=chat_client.start, 
                                         kwargs={"stop_event": stop_event, "system_message": first_message})
    background_thread.start()

    response_thread = threading.Thread(name='response', target=read_response, args=[chat_client, stop_event])
    response_thread.start()

    teststring = speechstring()
    speech_thread = threading.Thread(name='speech', target=teststring.start)
    speech_thread.start()

    print("Now let's type something or command below:\n"
          "1. type 'history' to list the current conversation\n"
          "2. type 'exit' to finish")

    while True:
        # text = input()
        # identify the string start with "toGPT"
        text:str = teststring.speechstr()
        while text.startswith("toGPT:"):
            text = text[6:]
            if text == 'exit':
                stop_event.set()
                break
            elif text == 'history':
                chat_client.print_history()
                continue
            test_buffer.add_text(text)
            test_buffer.set_ready_dump(True)

    response_thread.join()
    background_thread.join()
    speech_thread.join()


if __name__ == '__main__':
    main()
