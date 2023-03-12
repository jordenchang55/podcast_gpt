import json
import time

import openai

from buffer import Buffer

with open('resources/openai_key.json') as f:
    data = json.load(f)
    openai.api_key = data['api-key']


class ChatClient:
    def __init__(self, buffer: Buffer, **kwargs):
        self.buffer = buffer
        self.staged_response = ""

        # Other settings for GPT model
        self.model_engine = kwargs['engine'] if 'engine' in kwargs else "davinci"
        self.temperature = kwargs['temperature'] if 'temperature' in kwargs else 0.5
        self.max_tokens = kwargs['max_tokens'] if 'max_tokens' in kwargs else 100
        self.top_p = 1

    def start(self, event):
        print("Chat client started...")
        while True:
            if event.is_set():
                break
            if self.buffer.is_ready_dump():
                self._generate_response(self.buffer.dump())
            time.sleep(0.1)

    def get_response(self):
        return self.staged_response

    def reset_response(self):
        self.staged_response = ""

    def _generate_response(self, text):
        print("Generate response for %s" % text)
        model_engine = "davinci"  # Change this to the model you want to use
        temperature = 0.5
        max_tokens = 100
        top_p = 1
        frequency_penalty = 0
        presence_penalty = 0

        # Generate a response from GPT-3
        res = openai.Completion.create(
            engine=model_engine,
            prompt=text,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )

        print("response: %s" % res)

        self.staged_response += res.choices[0].text
