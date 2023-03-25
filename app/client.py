import json
import logging
import os
import time
from threading import Event

import openai
import speech_recognition as sr

from .buffer import Buffer
from .constants import DEFAULT_CHUNK, DEFAULT_SAMPLE_RATE, EXIT_KEYWORDS

print("path", os.getcwd())
with open('app/resources/openai_key.json') as f:
    data = json.load(f)
    openai.api_key = data['GPT-api-key']


class ChatClient:
    def __init__(self, buffer: Buffer, **kwargs):
        self._buffer = buffer
        self._staged_response = ""
        # The history will save all the conversation from user and the adopted bot response.
        self._message_history = []

        # Other settings for GPT model
        self.model = kwargs['model'] if 'model' in kwargs else "gpt-3.5-turbo"
        self.temperature = kwargs['temperature'] if 'temperature' in kwargs else 0.7
        self.max_tokens = kwargs['max_tokens'] if 'max_tokens' in kwargs else 256
        self.frequency_penalty = kwargs['frequency_penalty'] if 'frequency_penalty' in kwargs else 0
        self.presence_penalty = kwargs['presence_penalty'] if 'presence_penalty' in kwargs else 0

    def start(self, stop_event: Event, system_message=None):
        """

        :param stop_event: the shared event among threads to notify when the loop should stop.
        :param system_message: the message send to chat model to control its behavior. As docs suggested, it might
        be ignored or override by the user input, it is better to set it up in the beginning.
        """
        logging.info("Chat client started...")
        if system_message:
            self._add_input(system_message, role='system')
        while True:
            if stop_event.is_set():
                break
            if self._buffer.is_ready_dump():
                logging.debug("Buffer is ready")
                self._add_input(self._buffer.dump())
                self._generate_response()
            time.sleep(0.1)

    def peek_response(self):
        return self._staged_response

    def take_response(self):
        """
        Return the content in the staged response and reset it. If you only want to check the content,
        use :func:`peek_response` instead. The taken response will be saved into the history so that
        in the future conversation, the bot will have the context.
        :return: the staged response.
        """
        response = self._staged_response
        self.reset_response()
        self._message_history.append({
            "role": "assistant",
            "content": response
        })
        return response

    def reset_response(self):
        self._staged_response = ""

    def print_history(self):
        print("=" * 10 + "History" + "=" * 10)
        for row in self._message_history:
            print("%s: %s" % (row['role'], row['content']))
        print("=" * 30)

    def _add_input(self, text, role='user'):
        self._message_history.append({
            "role": role,
            "content": text
        })

    def _generate_response(self):
        start_time = time.time()
        res = openai.ChatCompletion.create(
            model=self.model,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            messages=self._message_history
        )

        print("Response in %.2f seconds: %s" % ((time.time() - start_time), res))
        self._staged_response = res['choices'][0]['message']['content'].strip()


class MicClient:
    def __init__(self, buffer: Buffer, pause_timeout=None, sample_rate=DEFAULT_SAMPLE_RATE, chunk=DEFAULT_CHUNK):
        self._buffer = buffer
        self._stop_listen_event = Event()
        self._sample_rate = sample_rate
        self._chunk = chunk
        self._pause_timeout = pause_timeout

        self._stop_listening = None

    def _callback(self, recognizer, audio):
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            text = recognizer.recognize_google(audio, language="zh-TW")
            logging.info("[Mic] - %s" % text)
            if text in EXIT_KEYWORDS:
                self.stop()
                logging.debug("Heard exit keywords. Exiting...")
                return
            self._buffer.add_text(text)
        except sr.UnknownValueError:
            logging.debug("Could not understand audio")
        except sr.RequestError as e:
            logging.debug("Could not request results from Google Speech Recognition service; {0}".format(e))

    def start(self):
        logging.debug("Start taking response from mic...")
        r = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            r.adjust_for_ambient_noise(source)
        self._stop_listening = r.listen_in_background(mic, callback=self._callback,
                                                      phrase_time_limit=self._pause_timeout)

    def stop(self):
        self._stop_listening()
