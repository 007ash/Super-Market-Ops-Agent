FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r ai_smart_mart && useradd -r -g ai_smart_mart ai_smart_mart

# Install dependencies for reportlab/psycopg2
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

USER ai_smart_mart

EXPOSE 8080

ENTRYPOINT ["python", "-m", "src.main"]
