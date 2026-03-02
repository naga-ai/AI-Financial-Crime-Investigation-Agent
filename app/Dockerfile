# ── Stage 1: builder ────────────────────────────────────────────────────────
# Install all deps (including build-essential for compiled extensions).
# The final image will NOT contain build-essential, saving ~200 MB.
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Core packages (FastAPI, LangChain, XGBoost, etc.)
COPY requirements-core.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-core.txt

# 2. CPU-only PyTorch first — prevents sentence-transformers from pulling CUDA
#    (~200 MB vs ~2.5 GB for the default CUDA wheel)
RUN pip install --no-cache-dir --prefix=/install \
    torch --index-url https://download.pytorch.org/whl/cpu

# 3. RAG packages that depend on torch
COPY requirements-rag.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-rag.txt


# ── Stage 2: runtime ────────────────────────────────────────────────────────
# Lean final image — no compiler toolchain, only what's needed to run.
FROM python:3.10-slim AS runtime

WORKDIR /app

# Runtime system deps only (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Pre-generate synthetic data + train triage model at build time
RUN python scripts/generate_data.py && \
    python scripts/train_triage.py

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
