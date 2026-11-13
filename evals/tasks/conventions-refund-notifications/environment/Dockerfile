FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest "fastapi==0.115.12" "httpx<0.29" "pydantic>=2.11,<3"
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A && git commit -qm "Refunds API"
