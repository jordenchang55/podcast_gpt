import os
import sys
import time
import json
import openai
import speech_recognition as sr

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir_path)
with open('app/resources/api_key.json') as f:
    data = json.load(f)
    openai.api_key = data['GPT-api-key']

def callback(recognizer, audio):
    print("Audio data length: %d" % (len(audio.get_raw_data()),))
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        print("Google Speech Recognition thinks you said " + recognizer.recognize_google(audio, language="zh-TW"))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


def listen_mic():
    # obtain audio from the microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        audio = r.listen(source)

        # recognize speech using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            OPENAI_API_KEY = openai.api_key
            print("Google Speech Recognition thinks you said " + r.recognize_whisper_api(audio, api_key=OPENAI_API_KEY))
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))


listen_mic()
