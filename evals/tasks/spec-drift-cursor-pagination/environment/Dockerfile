FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest pyyaml
COPY app/ /app/
WORKDIR /app
RUN cp -a /app /opt/base \
 && git init -q && git add -A && git commit -q -m "feat: add GET /orders listing endpoint" \
 && git rev-parse HEAD > /etc/eval-base-sha
