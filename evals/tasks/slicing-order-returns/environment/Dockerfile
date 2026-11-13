FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY app/ /app/
RUN cp -a /app /opt/base && chmod -R a-w /opt/base \
 && cd /app && git init -q && git add -A && git commit -qm "shop-api 0.14.0"
WORKDIR /app
