import logging
import paddle
from paddlespeech.cli.tts import TTSExecutor
from playsound import playsound

filename = "output_api.wav"

tts_executor = TTSExecutor()
wav_file = tts_executor(
    text="我认为A,I会带来很多便利和发展机会，但确实也可能对某些行业造成影响，需要我们注重转型和转变。不过，技术的进步总是不可避免的，我们应该适时调整自己的态度和思路，去适应这个新的变化。",
    output=filename,
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

logging.debug(f'Generated speech saved to "{filename}"')
playsound(filename)