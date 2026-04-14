FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin

WORKDIR /app

# Copy configuration files
COPY pyproject.toml .

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY . .

# Environment variables for the harvester
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV STATE_FILE=/app/data/state.json

# Default command: run all harvesters
# In a real setup, this might be a while loop or a scheduler
CMD ["uv", "run", "python", "main.py", "--all"]
