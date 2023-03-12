import threading

from buffer import TestBuffer
from client import ChatClient


def read_response(client: ChatClient, event):
    print("Started listening response on %s" % client)
    while True:
        if event.is_set():
            break
        if client.staged_response:
            print(client.staged_response)
            client.reset_response()


def main():
    event = threading.Event()

    test_buffer = TestBuffer()
    chat_client = ChatClient(test_buffer)

    background_thread = threading.Thread(name='background', target=chat_client.start, kwargs={"event": event})
    background_thread.start()

    response_thread = threading.Thread(name='response', target=read_response, args=[chat_client, event])
    response_thread.start()

    print("Now let's type something or type 'exit' to finish")
    while True:
        text = input()
        if text == 'exit':
            event.set()
            break
        test_buffer.add_text(text)
        test_buffer.set_ready_dump(True)

    # try:
    #     listening_task.cancel()
    # except asyncio.CancelledError:
    #     print("Listening task has been cancelled")
    # await listening_task

    response_thread.join()
    background_thread.join()


if __name__ == '__main__':
    main()
