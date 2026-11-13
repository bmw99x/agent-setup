FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest==8.4.2
COPY app/ /app/
COPY feature/ /tmp/feature/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm -rf /tmp/repo-setup.sh /tmp/feature
