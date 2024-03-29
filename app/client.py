import json
import logging
import threading
import time
from threading import Event
from typing import Callable

import openai

from app.buffer import Buffer

with open('app/resources/api_key.json') as f:
    data = json.load(f)
    openai.api_key = data['GPT-api-key']


class ChatClient:
    def __init__(self, buffer: Buffer, **kwargs):
        self._buffer = buffer
        # The history will save all the conversation from user and the adopted bot response.
        self._message_history = []
        self._running_thread = None
        self._stop_event = None

        # Other settings for GPT model
        self.model = kwargs['model'] if 'model' in kwargs else "gpt-3.5-turbo"
        self.temperature = kwargs['temperature'] if 'temperature' in kwargs else 0.7
        self.max_tokens = kwargs['max_tokens'] if 'max_tokens' in kwargs else 256
        self.frequency_penalty = kwargs['frequency_penalty'] if 'frequency_penalty' in kwargs else 0
        self.presence_penalty = kwargs['presence_penalty'] if 'presence_penalty' in kwargs else 0

    def start(self, stop_event: Event, system_message: str = None, callback: Callable[[str], None] = None):
        """

        :param stop_event: the shared event among threads to notify when the loop should stop.
        :param system_message: the message send to chat model to control its behavior. As docs suggested, it might
        be ignored or override by the user input, it is better to set it up in the beginning.
        :param callback: pass the message returned by chatGPT.
        """
        logging.info("Chat client started...")
        self._running_thread = threading.Thread(name="chat", target=self._start, args=[callback])
        self._stop_event = stop_event

        if system_message:
            self._add_input(system_message, role='system')

        self._running_thread.start()

    def stop(self):
        self._running_thread.join()

    def add_actual_response(self, text):
        """
        Add the response chosen by user in to message history so that ChatGPT can get more context in the following
        conversation.

        :return: the staged response.
        """
        logging.info("[GPT] - %s" % text)
        self._message_history.append({
            "role": "assistant",
            "content": text
        })

    def print_history(self):
        logging.debug("=" * 10 + "History" + "=" * 10)
        for row in self._message_history:
            logging.debug("%s: %s" % (row['role'], row['content']))
        logging.debug("=" * 30)

    def _add_input(self, text, role='user'):
        self._message_history.append({
            "role": role,
            "content": text
        })

    def _start(self, callback):
        while True:
            if self._stop_event.is_set():
                break
            if self._buffer.is_ready_dump():
                logging.debug("Buffer is ready")
                self._add_input(self._buffer.dump())
                res = self._generate_response()
                self._staged_response = res
                callback(res)
            time.sleep(0.3)

    def _generate_response(self):
        start_time = time.time()
        res = openai.ChatCompletion.create(
            model=self.model,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            messages=self._message_history
        )

        logging.debug("Response in %.2f seconds: %s" % ((time.time() - start_time), res))
        return res['choices'][0]['message']['content'].strip()
