FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git nodejs && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY fakes/forge.py /usr/local/bin/glab
RUN cp /usr/local/bin/glab /usr/local/bin/gh && chmod 755 /usr/local/bin/glab /usr/local/bin/gh
COPY repo/ /tmp/repo/
COPY repo-setup.sh /tmp/repo-setup.sh
RUN sh /tmp/repo-setup.sh && rm -rf /tmp/repo /tmp/repo-setup.sh
WORKDIR /app

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
