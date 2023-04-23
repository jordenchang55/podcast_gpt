FROM nvidia/cuda:11.7.0-cudnn8-runtime-ubuntu20.04
WORKDIR /docker
COPY /app/TTS/ttspaddle.py /docker
# install python 3.10 and pip
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get update && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3-pip libsndfile1

# Install PaddlePaddle
RUN python3 -m pip install paddlepaddle-gpu==2.4.2.post117 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html

# Install Python libraries
RUN python3 -m pip install pytest-runner && \
    python3 -m pip install paddlespeech && \
    python3 -m pip install playsound && \
    python3 -m pip install --upgrade numba
# RUN pip install -r requirements.txt
CMD ["python3", "ttspaddle.py"]