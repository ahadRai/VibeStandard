FROM python:3.13-slim

# Install git and build tools — required for GitPython and building pydantic-core
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install semgrep
RUN pip install semgrep --break-system-packages || true

WORKDIR /app

# Copy and install the vibestandard CLI package first
# so the API can import from it directly
COPY ../vibestandard-analyzers /vibestandard-analyzers
RUN pip install /vibestandard-analyzers --no-cache-dir

# Copy and install API requirements
COPY vibestandard-api/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy API source
COPY vibestandard-api/ .

# Create clone directory
RUN mkdir -p /tmp/vibestandard-clones

# Non-root user for security
RUN addgroup --system vibestandard && \
    adduser --system --ingroup vibestandard vibestandard && \
    chown -R vibestandard:vibestandard /app && \
    chown -R vibestandard:vibestandard /tmp/vibestandard-clones

USER vibestandard

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
