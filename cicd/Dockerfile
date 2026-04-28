FROM python:3.11-slim

#supposedly needed for mysql client libraries
RUN apt-get -q update && \
    apt-get install -yq --no-install-recommends build-essential pkg-config default-libmysqlclient-dev
    
RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

COPY app/ .

CMD ["python", "main.py"]