FROM python:3.12-slim
RUN pip install --no-cache-dir pytest "fastapi==0.115.12" "httpx==0.28.1" "sqlalchemy==2.0.41" "pydantic==2.11.4"
COPY app/ /app/
WORKDIR /app
