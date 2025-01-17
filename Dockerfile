# Use the official lightweight Python image.
FROM python:3.11-slim AS base

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME            /app
WORKDIR                 $APP_HOME

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /root/.cache && rm -rf /var/cache/apk/*

FROM base AS poetry

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
COPY ./entrypoint.sh    .

#FROM poetry as pytest
#
#RUN poetry install --no-ansi --no-root --with test
#COPY ./app/tests        ./tests
#
#RUN poetry run coverage run -m pytest && poetry run coverage report -m

FROM base AS app

COPY --from=poetry $APP_HOME/.venv            $APP_HOME/.venv
COPY --from=poetry $APP_HOME/src              $APP_HOME/
COPY --from=poetry $APP_HOME/entrypoint.sh    $APP_HOME/


ENV PATH                                      "$APP_HOME/.venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]
