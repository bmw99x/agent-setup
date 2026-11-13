FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A && git commit -qm "Catalog search with October housekeeping" \
 && git rev-parse HEAD > /etc/eval-base-sha \
 && sha256sum .claude/housekeeping/2026-10-01-search-ranking/* > /etc/eval-old-housekeeping.sha256
