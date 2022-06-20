FROM python:3.9-slim-buster AS builder
RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
  && pip install --upgrade setuptools \
  && pip install -r requirements.txt

COPY bot /app/bot

RUN mkdir /usr/local/share/fonts/

ADD /files /app/files

CMD python -m bot