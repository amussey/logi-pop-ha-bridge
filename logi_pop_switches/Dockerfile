ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache python3 py3-pip curl build-base

ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry using curl
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root \
    && rm -rf /root/.cache/pip /root/.cache/pypoetry

# Copy the application code
COPY logi_ha_bridge/ /app/logi_ha_bridge
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
