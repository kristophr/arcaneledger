FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATA_DIR=/app/data \
    DEFAULT_IMPORT=/imports/export.csv

WORKDIR /app

COPY app.py /app/app.py
COPY static /app/static

RUN mkdir -p /app/data /imports

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/api/health', timeout=3).read()"

CMD ["python", "app.py", "serve"]
