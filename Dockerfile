FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mention_monitor ./mention_monitor
COPY run.py config.json README.md SHARE.md ./

RUN mkdir -p /app/data /app/outputs/reports

EXPOSE 8765

CMD ["python", "run.py", "server", "--host", "0.0.0.0", "--port", "8765"]
