FROM python:3.11.7

MAINTAINER "engine"

COPY browser /engine/browser

COPY core /engine/core

COPY requirements.txt /engine/

COPY tools/ /engine/tools

COPY lm/ /engine/lm

COPY startup.py /engine/

WORKDIR /engine

RUN pip install -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com

CMD ["python", "startup.py"]
