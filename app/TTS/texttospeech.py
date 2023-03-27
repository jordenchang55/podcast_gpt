import io
import os
import sys

import google.cloud.texttospeech as tts
import sounddevice as sd
import soundfile as sf

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

    def speak(self, text):
        # TODO: No sound here
        data = self._get_speech_data(text)
        sound_data, samplerate = sf.read(io.BytesIO(data))
        print(sound_data)
        sd.play(sound_data, samplerate=samplerate)

    def speak_to_file(self, text, filename):
        data = self._get_speech_data(text)
        with open(filename, "wb") as out:
            out.write(data)
            print(f'Generated speech saved to "{filename}"')

    def _get_speech_data(self, text):
        tts_input = tts.SynthesisInput()
        tts_input.text = text
        response = self.tts_client.synthesize_speech(
            input=tts_input,
            voice=self._voice_params,
            audio_config=self._audio_config,
        )
        return response.audio_content


if __name__ == '__main__':
    client = SpeechClient()
    client.speak("What is the temperature in New York?")
