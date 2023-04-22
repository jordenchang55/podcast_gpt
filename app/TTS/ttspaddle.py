import logging
import time

import paddle
from paddlespeech.cli.tts import TTSExecutor
from paddlespeech.cli.tts.infer import ONNX_SUPPORT_SET
from paddlespeech.resource import CommonTaskResource
from playsound import playsound

output = "output_api.wav"

tts_executor = TTSExecutor()

am = "fastspeech2_male"
spk_id = 0  # spk_id = 167 for male,
voc = "pwgan_male"
lang = "mix"
device = paddle.get_device()
tts_executor.task_resource = CommonTaskResource(
    task='tts', model_format='onnx')
assert (
        am in ONNX_SUPPORT_SET and voc in ONNX_SUPPORT_SET
), f'the am and voc you choose, they should be in {ONNX_SUPPORT_SET}'
tts_executor._init_from_path_onnx(
    am=am,
    am_ckpt=None,
    phones_dict=None,
    tones_dict=None,
    speaker_dict=None,
    voc=voc,
    voc_ckpt=None,
    lang=lang,
    device=device,
)
sentences = [
    "我认为A,I会带来很多便利和发展机会",
    "但确实也可能对某些行业造成影响",
    "需要我们注重转型和转变",
    "不过，技术的进步总是不可避免的",
    "我们应该适时调整自己的态度和思路，去适应这个新的变化。"
]
for text in sentences:
    start = time.time()
    tts_executor.infer_onnx(text=text, lang=lang, am=am, spk_id=spk_id)
    print("Infer time: %.2f - [%s]" % (time.time() - start, text))
    res = tts_executor.postprocess_onnx(output=output)
    logging.debug(f'Generated speech saved to "{output}"')
    playsound(output)
