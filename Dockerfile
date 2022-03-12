FROM python:3.10.2-slim-buster

RUN apt-get update && apt-get -y install curl gcc python3-dev build-essential libssl-dev libffi-dev
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY . .

ENV PATH "$PATH:/root/.local/bin"

RUN poetry config virtualenvs.create false
RUN poetry install -n --no-dev
