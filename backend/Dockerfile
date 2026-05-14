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

# Install dependencies — skip torch to avoid CUDA bloat (~8GB saved)
# CUDA packages (nvidia-*, cuda-*, triton) are torch-only deps and auto-skipped
RUN uv sync --frozen --no-dev \
    --no-install-package torch \
    --index-url https://mirrors.aliyun.com/pypi/simple/

# Install CPU-only PyTorch (BGE embedding only needs CPU inference)
RUN uv pip install torch --index-url https://download.pytorch.org/whl/cpu

# Pre-download embedding model (--no-sync to preserve CPU-only torch)
# HF_ENDPOINT set to hf-mirror.com at runtime via docker-compose.prod.yml
RUN uv run --no-sync python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-zh-v1.5')"

# Copy application code
COPY backend/ .

# Copy prompts into the LPA package for reliable path resolution in Docker
COPY prompts/ /app/app/agents/lpa/prompts/

# Ensure data and media directories exist
RUN mkdir -p /app/data /app/media

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
