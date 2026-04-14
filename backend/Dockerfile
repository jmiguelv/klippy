FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV QDRANT_HOST=qdrant
ENV REDIS_HOST=redis
ENV DATA_DIR=/app/data

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
