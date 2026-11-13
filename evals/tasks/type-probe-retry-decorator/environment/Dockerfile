FROM python:3.12-slim
RUN pip install --no-cache-dir pytest==8.4.2 mypy==2.4.1 ty==0.0.101
COPY app/ /app/
WORKDIR /app
