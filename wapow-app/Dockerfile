FROM python:3.12-slim

WORKDIR /app

# Install Poetry
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Copy dependency files first (better layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev; production only)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

EXPOSE 3001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "3001"]
