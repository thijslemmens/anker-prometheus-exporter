FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN git clone --depth 1 https://github.com/thomluther/anker-solix-api.git /tmp/anker-solix-api \
    && cp -r /tmp/anker-solix-api/api /app/api \
    && rm -rf /tmp/anker-solix-api

COPY exporter.py .

EXPOSE 8000

CMD ["python", "exporter.py"]