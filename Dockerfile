# PDF Password Remover - Production Dockerfile
FROM python:3.12-slim

# ตั้ง working directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ติดตั้ง dependencies (cache layer)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy ทั้ง project
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# สร้าง non-root user เพื่อความปลอดภัย
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (default 8000, แต่ cloud platforms มักจะใช้ $PORT แทน)
EXPOSE 8000
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/health').read()" || exit 1

# รัน uvicorn ด้วย production config
# ใช้ shell form เพื่อ expand $PORT (cloud platforms เช่น Railway, Fly.io ใช้ PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
