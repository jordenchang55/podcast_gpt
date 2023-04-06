# speech to text by google
from __future__ import division

import json
import logging
import os
import re
import sys
import threading
import time

from google.cloud import speech

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir_path)

from .buffer import STTBuffer
from .mic_constants import DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK
from .microphone import MicrophoneStream

with open('app/resources/api_key.json') as f:
    data = json.load(f)


class ListenClient:
    def __init__(self, buffer: STTBuffer, timeout=120, maximum=200, language_code="zh"):
        # a BCP-47 language tag "zh" "en-US"
        self.speechbuffer = buffer
        self.timeout = timeout
        self.maximum = maximum
        self.language_code = language_code
        self._running_thread = None
        self._stop_event = threading.Event()
        self._stream = None

        # add your own google cloud speech to text api key
        self.client = speech.SpeechClient(client_options={
            'api_key': data['Google-api-key']
        })

        diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=3,
            max_speaker_count=3,
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=DEFAULT_SAMPLE_RATE,
            language_code=self.language_code,
            diarization_config=diarization_config
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

    def start(self):
        if self._stop_event.is_set():
            self._stop_event.clear()
        self._running_thread = threading.Thread(name='listening', target=self._start)
        self._running_thread.start()

    def stop(self):
        if self._stream:
            self._stream.close()
        self._stop_event.set()

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

            if self._stop_event.is_set():
                finalstring = transcript + overwrite_chars
                self.speechbuffer.add_text(finalstring)
                logging.debug("Cut off by stop event, exiting..")
                logging.debug("Final string: %s" % finalstring)
                logging.info("[Guest] - %s", finalstring)

                break

            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")
                sys.stdout.flush()
                num_chars_printed = len(transcript)

            else:
                finalstring = transcript + overwrite_chars
                self.speechbuffer.add_text(finalstring)
                logging.debug("Final string: %s" % finalstring)
                logging.info("[Guest] - %s", finalstring)
                # If timeout break
                if time.time() - self.currenttime > self.timeout:
                    self.currenttime = time.time()
                    self.speechbuffer.cut_string()
                    break
                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                elif re.search(r"\b(exit|quit)\b", transcript, re.I):
                    logging.debug("Exiting audio stream by exit keywords..")
                    self.stop()
                    break

                num_chars_printed = 0

    def _start(self):
        while not self._stop_event.is_set():
            with MicrophoneStream(DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK) as stream:
                self._stream = stream
                audio_generator = stream.generator()
                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )

                responses = self.client.streaming_recognize(
                    self.streaming_config, requests)

                # Now, put the transcription responses to use.
                self.currenttime = time.time()
                try:
                    self.listen_print_loop(responses)
                except Exception as exception:
                    logging.debug("Stream exception: ", exception)
            logging.debug("Stream closed. It will restart shortly.")
            time.sleep(0.1)
