FROM python:latest
RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python -m pip install -r ./requirements.txt
COPY . /bot
WORKDIR /bot