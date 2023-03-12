import json
import time

import openai

from buffer import Buffer

with open('resources/openai_key.json') as f:
    data = json.load(f)
    openai.api_key = data['api-key']


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

    def start(self, stop_event):
        print("Chat client started...")
        while True:
            if stop_event.is_set():
                break
            if self._buffer.is_ready_dump():
                self._add_user_input(self._buffer.dump())
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

    def _add_user_input(self, text):
        self._message_history.append({
            "role": "user",
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