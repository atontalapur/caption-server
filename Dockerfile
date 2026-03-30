FROM python:3.12-slim

# HF Spaces runs containers as a non-root user (uid 1000)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install dependencies first (layer-cached until requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Persistent style cache lives here — HF Spaces mounts /data as a persistent volume
# when "persistent storage" is enabled in the Space settings.
RUN mkdir -p /app/data/writings && chown -R appuser:appuser /app

USER appuser

ENV PORT=7860
ENV STYLE_CACHE_PATH=/app/data/style_cache.json

EXPOSE 7860

CMD ["python", "-m", "app.main"]
