FROM python:3.12-slim
RUN pip install --no-cache-dir pytest pytest-mock
COPY app/ /app/
COPY app/ /opt/base/
WORKDIR /app
