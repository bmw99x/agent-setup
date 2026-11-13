FROM python:3.12-slim
RUN pip install --no-cache-dir pytest azure-identity azure-storage-blob
COPY app/ /app/
WORKDIR /app
