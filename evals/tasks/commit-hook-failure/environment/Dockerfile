FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest ruff
COPY app/ /app/
WORKDIR /app
COPY repo-setup.sh /tmp/repo-setup.sh
RUN sh /tmp/repo-setup.sh && rm /tmp/repo-setup.sh && git -C /app rev-parse HEAD > /etc/eval-base-sha
