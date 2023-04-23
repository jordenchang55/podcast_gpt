FROM nvidia/cuda:11.7.0-cudnn8-runtime-ubuntu20.04
WORKDIR /docker
COPY . .
# install python 3.10 and pip
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt install -y python3.10 python3-pip
# install paddlepaddle
RUN python3 -m pip install paddlepaddle-gpu==2.4.2.post117 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html \
    pip install pytest-runner \
    pip install paddlespeech
# RUN pip install -r requirements.txt
CMD ["python3", "/app/TTS/ttspaddle.py"]
