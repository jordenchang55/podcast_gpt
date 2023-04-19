from paddlespeech.cli.tts.infer import TTSExecutor
tts = TTSExecutor()
tts(text="中文語音合成測試。", output="output.wav")