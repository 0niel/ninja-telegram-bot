FROM python:3.9-slim-buster AS builder
RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
  && pip install --upgrade setuptools \
  && pip install -r requirements.txt

COPY bot /app/bot

CMD python -m bot