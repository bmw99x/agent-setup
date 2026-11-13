FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ripgrep && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest==8.4.2
COPY app/ /opt/base/
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A && git commit -qm "orders service" && chmod -R a-w /opt/base
