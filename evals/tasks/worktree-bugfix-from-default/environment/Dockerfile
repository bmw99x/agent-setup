FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY app/ /app/
COPY repo-setup.sh capture-baseline.py /tmp/
RUN bash /tmp/repo-setup.sh && python3 /tmp/capture-baseline.py /app/repo && rm /tmp/repo-setup.sh /tmp/capture-baseline.py
WORKDIR /app/repo

# The agent runs as uid 10001: it creates worktrees beside the checkout and pushes to the local remote.
RUN chmod -R a+rwX /app
