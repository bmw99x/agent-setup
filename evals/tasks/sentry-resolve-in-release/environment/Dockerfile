FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git jq && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY app/ /app/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm /tmp/repo-setup.sh
COPY fakes/ /tmp/fakes/
RUN install -m 755 /tmp/fakes/sentry.py /usr/local/bin/sentry \
 && install -D -m 644 /tmp/fakes/spec.json /usr/local/share/sentry-fake/spec.json \
 && cd /tmp/fakes && python3 seed.py && rm -rf /tmp/fakes /var/log/fakes && mkdir -p /var/log/fakes

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
