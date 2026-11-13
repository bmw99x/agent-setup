FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git graphviz make && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest
COPY app/ /app/
WORKDIR /app
RUN make diagrams
COPY fakes/ /tmp/fakes/
RUN install -m 755 /tmp/fakes/fakecli.py /usr/local/bin/tracker \
 && install -m 755 /tmp/fakes/fakecli.py /usr/local/bin/wiki \
 && python3 /tmp/fakes/seed.py && rm -rf /tmp/fakes && mkdir -p /var/log/fakes
RUN cp -a /app /opt/base \
 && git init -q && git add -A && git commit -q -m "feat(orders): order lifecycle state machine (SHOP-310)" \
 && git rev-parse HEAD > /etc/eval-base-sha

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
