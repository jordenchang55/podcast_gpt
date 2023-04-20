from paddlespeech.cli.tts.infer import TTSExecutor
tts = TTSExecutor()
tts(
    text="Linux Bonding（也稱為 Linux 套接字綁定，或簡稱 Bonding）是一種技術，用於將兩個或多個網絡接口卡（NIC）組合成單個邏輯接口。這個邏輯接口的好處是它提供了更高的帶寬、更好的容錯能力和更高的可用性。", 
    # am="fastspeech2_aishell3",
    # voc="hifigan_aishell3",
    # lang="zh", 
    output="output_api.wav")