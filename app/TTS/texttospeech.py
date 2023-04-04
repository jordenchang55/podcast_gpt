import io
import logging

import json
import google.cloud.texttospeech as tts
import sounddevice as sd
import soundfile as sf
from playsound import playsound


# dir_path = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(dir_path)

with open('app/resources/api_key.json') as f:
    data = json.load(f)

class SpeechClient:
    def __init__(self, language_code="cmn-TW", voice_name="cmn-TW-Standard-A"):
        # cmn-TW en-US
        self.tts_client = tts.TextToSpeechClient(client_options={
            'api_key': data['Google-api-key']
        })
        self._voice_params = tts.VoiceSelectionParams()
        self._voice_params.language_code = language_code
        self._voice_params.name = voice_name

        self._audio_config = tts.AudioConfig()
        self._audio_config.audio_encoding = tts.AudioEncoding.LINEAR16

    def speak(self, text):
        data = self._get_speech_data(text)
        sound_data, samplerate = sf.read(io.BytesIO(data))
        sd.play(sound_data, samplerate=samplerate)
        sd.wait()

    def speak_to_file(self, text, filename):
        data = self._get_speech_data(text)
        with open(filename, "wb") as out:
            out.write(data)
            logging.debug(f'Generated speech saved to "{filename}"')
            playsound(filename)

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
    client.speak("What is the weather today?")
