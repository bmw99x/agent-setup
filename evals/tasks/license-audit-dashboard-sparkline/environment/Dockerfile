FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pytest \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g --no-fund --no-audit license-checker@25.0.1 && npm cache clean --force
COPY tools/ /opt/eval-tools/
COPY registry-src/ /opt/registry-src/
# Offline npm: pack the fake packages into a local registry, warm a shared cache from it once,
# then pin npm to that cache in offline mode. The registry server does not run at solve time.
RUN node /opt/eval-tools/build-registry.js /opt/registry-src /opt/registry && rm -rf /opt/registry-src \
 && printf 'registry=http://127.0.0.1:4873/\ncache=/opt/npm-cache\nfund=false\naudit=false\nupdate-notifier=false\n' > /usr/local/etc/npmrc \
 && (node /opt/eval-tools/serve-registry.js /opt/registry & sleep 1 \
     && npm cache add chartkit@3.2.0 svgpath-tools@1.6.3 sparkline-lite@1.0.4 \
     && mkdir /tmp/warm && cd /tmp/warm && npm init -y >/dev/null \
     && npm install chartkit sparkline-lite && npx --yes license-checker --summary && cd / && rm -rf /tmp/warm) \
 && echo 'offline=true' >> /usr/local/etc/npmrc \
 && chmod -R a+rwX /opt/npm-cache \
 && rm /usr/local/bin/license-checker \
 && printf '#!/bin/sh\nexec /opt/eval-tools/log-invocation license-checker /usr/local/lib/node_modules/license-checker/bin/license-checker "$@"\n' > /usr/local/bin/license-checker \
 && chmod 0755 /usr/local/bin/license-checker /opt/eval-tools/log-invocation \
 && touch /var/log/license-scans.jsonl && chmod 0666 /var/log/license-scans.jsonl
COPY app/ /app/
COPY app/ /opt/base/
WORKDIR /app

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
