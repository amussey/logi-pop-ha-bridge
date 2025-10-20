FROM python:3.12-slim

ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 -

# Create application directory
RUN mkdir /app
WORKDIR /app

# Install dependencies
ADD pyproject.toml /app/pyproject.toml
RUN poetry config virtualenvs.create false \
    && poetry install --no-root \
    && rm -rf /root/.cache/pip /root/.cache/pypoetry

# Copy the application code
ADD logi_ha_bridge /app/logi_ha_bridge
COPY run.sh /app/run.sh
RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]
