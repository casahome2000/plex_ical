FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install tzdata for proper timezone metadata (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends tzdata ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Non-root user (optional)
RUN useradd -m appuser
USER appuser

ENV PORT=8000

# Gunicorn for production serving
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "60", "app:app"]