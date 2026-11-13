FROM python:3.12-slim
RUN pip install --no-cache-dir pytest==8.3.5 pip-licenses==5.0.0 iniconfig==2.0.0 "packaging<25"
COPY tools/ /opt/eval-tools/
COPY index/ /opt/index-src/
# Offline package index: pip resolves only from the local wheelhouse.
RUN python /opt/eval-tools/make_wheels.py /opt/index-src /opt/wheelhouse && rm -rf /opt/index-src \
 && printf '[global]\nno-index = true\nfind-links = /opt/wheelhouse\ndisable-pip-version-check = true\n' > /etc/pip.conf \
 && install -m 0755 /opt/eval-tools/pip-licenses /usr/local/bin/pip-licenses \
 && touch /var/log/license-scans.jsonl && chmod 0666 /var/log/license-scans.jsonl \
 && chown -R 10001:10001 /usr/local/lib/python3.12/site-packages /usr/local/bin
COPY app/ /app/
COPY app/ /opt/base/
WORKDIR /app

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
