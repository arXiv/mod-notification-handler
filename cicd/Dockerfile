FROM python:3.11-slim

#supposedly needed for mysql client libraries
RUN apt-get -q update && \
    apt-get install -yq --no-install-recommends build-essential pkg-config default-libmysqlclient-dev
    
RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

COPY app/ app/

#the image is generic — it holds all three jobs and picks none of them. Every Cloud Run
#job sets its own command/args in cicd/terraform. This default only runs when something
#forgot to, and fails loudly rather than silently running the wrong job.
CMD ["sh", "-c", "echo 'No entrypoint given. Set command/args on the Cloud Run job, or run: python -m app.<mod_actions|daily_update|new_subs>.main' >&2; exit 1"]