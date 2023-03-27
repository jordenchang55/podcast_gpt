import os
import sys

import google.cloud.texttospeech as tts

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir_path)


class SpeechClient:
    def __init__(self):
        self.tts_client = tts.TextToSpeechClient.from_service_account_file(
            "../STT/myapikey.json"
        )
        self._voice_params = tts.VoiceSelectionParams(
            language_code="en-US", name="en-US-Studio-O"
        )
        self._audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    def speak_to_file(self, text, filename):
        response = self.tts_client.synthesize_speech(
            input=text,
            voice=self._voice_params,
            audio_config=self._audio_config,
        )

        with open(filename, "wb") as out:
            out.write(response.audio_content)
            print(f'Generated speech saved to "{filename}"')


if __name__ == '__main__':
    client = SpeechClient()
    client.speak_to_file("What is the temperature in New York?", "en-US-Studio-O.wav")
