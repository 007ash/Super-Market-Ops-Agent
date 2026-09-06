FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r kiranapilot && useradd -r -g kiranapilot kiranapilot

# Install dependencies for reportlab/psycopg2 if needed
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
# Use pip to install dependencies from pyproject.toml
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

USER kiranapilot

EXPOSE 8080

ENTRYPOINT ["python", "-m", "src.main"]
