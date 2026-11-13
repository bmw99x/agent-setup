FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest pytest-xdist pytest-asyncio ruff==0.17.4 ty==0.0.101 \
    "fastapi==0.162.5" "sqlalchemy[asyncio]==2.1.8" "pydantic==2.14.3" httpx requests asyncpg alembic==1.20.1
COPY gates/ /opt/gates/
RUN sh /opt/gates/install.sh
COPY app/ /app/
COPY feature/ /tmp/feature/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm -rf /tmp/repo-setup.sh /tmp/feature
