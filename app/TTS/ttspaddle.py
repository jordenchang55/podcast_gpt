import paddle
from paddlespeech.cli.tts import TTSExecutor
tts_executor = TTSExecutor()
wav_file = tts_executor(
    text="Linux Bonding（也稱為 Linux 套接字綁定，或簡稱 Bonding）是一種技術，用於將兩個或多個網絡接口卡（NIC）組合成單個邏輯接口。",
    output="output_api.wav",
    am="fastspeech2_male",
    am_config=None,
    am_ckpt=None,
    am_stat=None,
    spk_id=0, # spk_id = 167 for male,
    phones_dict=None,
    tones_dict=None,
    speaker_dict=None,
    voc="pwgan_male",
    voc_config=None,
    voc_ckpt=None,
    voc_stat=None,
    lang="mix",
    use_onnx=True,
    device=paddle.get_device())