FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data TORCH_HOME=/models OMP_NUM_THREADS=2

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg rubberband-cli libsndfile1 git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# torch — CPU-сборка (≈200 МБ вместо ≈2 ГБ с CUDA)
RUN pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

# скачиваем веса модели при сборке, чтобы первый трек не ждал загрузку
RUN python -c "from beat_this.inference import Audio2Beats; Audio2Beats(checkpoint_path='final0', device='cpu', dbn=False)"

COPY app ./app
COPY static ./static
COPY eval ./eval

RUN useradd -m -u 1000 takt && mkdir -p /data && chown -R takt /data /models
USER takt
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--workers", "2"]
