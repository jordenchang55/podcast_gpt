# speech to text by google
from __future__ import division

import os
import re
import sys
import time
from threading import Event

from google.cloud import speech

from app.STT.buffer import STTBuffer
from mic_constants import DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK
from microphone import MicrophoneStream

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir_path)


class ListenClient:
    def __init__(self, buffer: STTBuffer, timeout=120, maximum=200, language_code="zh"):
        # a BCP-47 language tag "zh" "en-US"
        self.speechbuffer = buffer
        self.timeout = timeout
        self.maximum = maximum
        self.language_code = language_code

        # add your own google cloud speech to text api key
        self.client = speech.SpeechClient.from_service_account_json(
            "app/resources/myapikey.json"
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=DEFAULT_SAMPLE_RATE,
            language_code=self.language_code,
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

    def start(self, block_event: Event):
        while True:
            if not block_event.is_set():
                with MicrophoneStream(DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK) as stream:
                    audio_generator = stream.generator()
                    requests = (
                        speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator
                    )

                    responses = self.client.streaming_recognize(
                        self.streaming_config, requests)

                    # Now, put the transcription responses to use.
                    self.currenttime = time.time()
                    self.listen_print_loop(responses)
                    if block_event.is_set():
                        break
            else:
                time.sleep(1)

    def listen_print_loop(self, responses):
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.
        """
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.
            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            transcript = result.alternatives[0].transcript

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result
            overwrite_chars = " " * (num_chars_printed - len(transcript))

            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")
                sys.stdout.flush()

                num_chars_printed = len(transcript)

            else:
                finalstring = transcript + overwrite_chars
                self.speechbuffer.add_string(finalstring)
                print(finalstring)
                # If timeout break
                if time.time() - self.currenttime > self.timeout:
                    self.currenttime = time.time()
                    self.speechbuffer.cut_string()
                    break
                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                elif re.search(r"\b(exit|quit)\b", transcript, re.I):
                    print("Exiting..")
                    break

                num_chars_printed = 0
