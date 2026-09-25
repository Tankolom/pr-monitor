FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vupaket ./vupaket
COPY run.py .
RUN useradd -r -u 10001 app && mkdir -p /app/data && chown app /app/data
USER app
EXPOSE 8080
CMD ["python", "run.py"]
