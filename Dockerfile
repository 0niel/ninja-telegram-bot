FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.3.2 \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry using pip
RUN pip install "poetry==$POETRY_VERSION"

# Copy poetry.lock* in case it doesn't exist in the repo
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry install --no-dev --no-root --no-interaction

COPY . /app/

CMD ["python", "-m", "bot"]