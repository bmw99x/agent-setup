FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest uv==0.9.11
COPY wheels/ /opt/wheels/
COPY upstream/ /opt/upstream/
COPY app/ /app/
WORKDIR /app
RUN for s in billing reports notifications; do (cd services/$s && uv sync --frozen -q); done \
 && git init -q && git add -A && git commit -qm "finance monorepo" \
 && git rev-parse HEAD > /etc/eval-base-sha
