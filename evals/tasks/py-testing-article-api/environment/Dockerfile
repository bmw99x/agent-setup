FROM python:3.12-slim
RUN pip install --no-cache-dir pytest pytest-asyncio "fastapi>=0.115" httpx "ruff>=0.6"
COPY app/ /app/
COPY app/ /opt/base/
WORKDIR /app
