import logging
import queue
import time
from collections import Counter
from threading import Event

from google.cloud import speech

from STT.speechtotext import MicrophoneStream
from constants import EXIT_KEYWORDS


class Buffer:
    """
    This class defines the interface of Buffer.
    """

    def add_text(self, text: str):
        raise NotImplementedError()

    def is_ready_dump(self) -> bool:
        raise NotImplementedError()

    def dump(self) -> str:
        raise NotImplementedError()


class TestBuffer(Buffer):
    """
    This buffer is used for testing. It provides functions to set fake data.
    """

    def __init__(self):
        self.text = ""
        self.is_ready = False

    def add_text(self, text: str):
        self.text += text

    def is_ready_dump(self) -> bool:
        return self.is_ready

    def dump(self) -> str:
        dump_text = self.text
        self.text = ""
        self.is_ready = False
        return dump_text

    def set_ready_dump(self, is_ready: bool):
        self.is_ready = is_ready


class SpeechBuffer(Buffer):
    def __init__(self, source: MicrophoneStream, stop_event: Event, timeout=120, maximum=200, language_code="zh"):
        self._stop_event = stop_event
        self.source = source
        self.timeout = timeout
        self.maximum_words = maximum
        # a BCP-47 language tag "zh" "en-US"
        self.language_code = language_code

        self._buffer = queue.Queue()
        self._counter = Counter()
        self._start_time = time.monotonic()
        self._stop_listen_event = Event()
        # add your own google cloud speech to text api key
        self.speech_client = speech.SpeechClient.from_service_account_json(
            "STT/myapikey.json"
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.source.get_sample_rate(),
            language_code=self.language_code,
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

    def add_text(self, text: str):
        self._buffer.put(text)
        self._counter.update(['words'] * len(text))

    def is_ready_dump(self) -> bool:
        return self._counter['words'] > self.maximum_words or (
                time.monotonic() - self._start_time > self.timeout and self._counter['words'] > 0)

    def dump(self) -> str:
        self._counter.clear()
        self._start_time = time.monotonic()
        s = ""
        while not self._buffer.empty():
            s += self._buffer.get()
        return s

    def start(self):
        logging.debug("Start taking response from mic...")
        self._start_time = time.monotonic()
        while True:
            if self._should_stop():
                break
            with self.source as stream:
                audio_generator = stream.generator()
                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )

                responses = self.speech_client.streaming_recognize(
                    self.streaming_config, requests)
                # Now, put the transcription responses to use.
                try:
                    self._listen_print_loop(responses)
                except Exception as e:
                    logging.warning("Stream too long, restart\n%s", e)

    def stop(self):
        self._stop_listen_event.set()

    def _should_stop(self):
        return self._stop_event.is_set() or self._stop_listen_event.is_set()

    def _listen_print_loop(self, responses):
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
                logging.debug("Temp parsed words: %s...", (transcript + overwrite_chars))

                num_chars_printed = len(transcript)

                if self._should_stop():
                    break

            else:
                final_words = transcript + overwrite_chars
                logging.info("[Mic] - %s", final_words)
                if final_words.strip() in EXIT_KEYWORDS:
                    logging.debug("Listened exit keywords. Exiting..")
                    self._stop_event.set()
                self.add_text(final_words)

                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.

                num_chars_printed = 0
