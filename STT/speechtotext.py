# speech to text by google
from __future__ import division

import queue
import re
import sys
import time

import pyaudio
from google.cloud import speech

from constants import DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate=DEFAULT_SAMPLE_RATE, chunk=DEFAULT_CHUNK):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

    def get_sample_rate(self):
        return self._rate


class speechstring:
    def __init__(self, timeout=120, maximum=200, language_code="zh"):
        # a BCP-47 language tag "zh" "en-US"
        self.speechstring = None
        self.speechbuffer = ""
        self.block = False
        self.timeout = timeout
        self.maximum = maximum
        self.language_code = language_code
        self.currenttime = time.time()

        # add your own google cloud speech to text api key
        self.client = speech.SpeechClient.from_service_account_json(
            "STT/myapikey.json"
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=DEFAULT_SAMPLE_RATE,
            language_code=self.language_code,
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

    def start(self):
        while True:
            if self.block == False:
                with MicrophoneStream(DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK) as stream:
                    audio_generator = stream.generator()
                    requests = (
                        speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator
                    )

                    responses = self.client.streaming_recognize(
                        self.streaming_config, requests)

                    # Now, put the transcription responses to use.
                    try:
                        self.listen_print_loop(responses)
                    except Exception as exception:
                        print("stream too long, restart")
            if self.speechbuffer == "quit":
                break

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

                if self.block:
                    break

            else:
                self.makestring(transcript + overwrite_chars)
                print(self.speechbuffer)

                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                if re.search(r"\b(exit|quit)\b", transcript, re.I):
                    print("Exiting..")
                    break

                num_chars_printed = 0

    def makestring(self, string):
        # make unblock timeout
        self.speechbuffer += string
        timeoutflag = time.time() - self.currenttime > self.timeout
        maximumflag = len(self.speechbuffer) > self.maximum
        if timeoutflag or maximumflag:
            self.currenttime = time.time()
            self.speechstring = "toGPT:" + str(string)
            self.speechbuffer = ""

    def speechstr(self):
        # check string length
        if self.speechstring is not None:
            sendstring = self.speechstring
            self.speechstring = None
        else:
            sendstring = "test"
        return sendstring

    def blockflag(self, status):
        self.block = status
