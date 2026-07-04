FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY mcp_server/ ./mcp_server/
COPY data/ ./data/
COPY pyproject.toml .

ENV PYTHONPATH=/app/src:/app

EXPOSE 8081

CMD ["python", "mcp_server/server.py"]
