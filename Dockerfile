# Use the official lightweight Python image.
FROM python:3.11-slim as base

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME            /app
WORKDIR                 $APP_HOME

RUN apt-get update && rm -rf /root/.cache && rm -rf /var/cache/apk/*

FROM base as poetry

ENV POETRY_HOME                     /opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT   true
ENV PATH                            "$POETRY_HOME/bin:$PATH"

RUN apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python - \
    && rm -rf /root/.cache && rm -rf /var/cache/apk/*

COPY ./pyproject.toml   .
COPY ./poetry.lock      .

RUN poetry install --no-cache --no-interaction --no-ansi --no-root

COPY ./app/src          ./src

FROM poetry as pytest

RUN poetry install --no-ansi --no-root --with test
COPY ./app/tests        ./tests

RUN poetry run coverage run -m pytest && poetry run coverage report -m

FROM base as app

COPY --from=poetry $APP_HOME/.venv  $APP_HOME/.venv
COPY --from=poetry $APP_HOME/src    $APP_HOME/src

ENV PATH                            "$APP_HOME/.venv/bin:$PATH"

ENTRYPOINT [ "python" ]
