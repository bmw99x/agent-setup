FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest "sqlalchemy==2.1.8" "advanced-alchemy==1.12.0" "fastapi==0.162.5" "aiosqlite==0.22.1" pydantic
COPY app/ /app/
WORKDIR /app
