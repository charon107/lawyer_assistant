FROM python:3.12-slim

WORKDIR /app

# Use Aliyun mirrors for apt and pip
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip (avoids slow ghcr.io pull)
RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies with Aliyun PyPI mirror (no dev deps)
RUN uv sync --frozen --no-dev --index-url https://mirrors.aliyun.com/pypi/simple/

# Pre-download embedding model
# HF_ENDPOINT set to hf-mirror.com at runtime via docker-compose.prod.yml
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-zh-v1.5')"

# Copy application code
COPY backend/ .

# Copy prompts into the LPA package for reliable path resolution in Docker
COPY prompts/ /app/app/agents/lpa/prompts/

# Ensure data and media directories exist
RUN mkdir -p /app/data /app/media

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
