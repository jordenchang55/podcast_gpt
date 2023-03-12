import speech_recognition as sr

r = sr.Recognizer()

audio_src = sr.Microphone()

with audio_src as src:
    audio = r.listen(src)
    text = r.recognize_google(audio, language="zh_TW")
    print(text)
