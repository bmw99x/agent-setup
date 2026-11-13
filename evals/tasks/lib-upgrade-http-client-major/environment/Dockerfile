FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest uv==0.9.11
COPY wheels/ /opt/wheels/
COPY upstream/ /opt/upstream/
RUN pip install --no-cache-dir --no-index --find-links /opt/wheels tidyhttp==1.3.0
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A && git commit -qm "catalog-sync 0.7.0" \
 && git rev-parse HEAD > /etc/eval-base-sha \
 && pip show tidyhttp | sed -n 's/^Version: //p' > /etc/eval-base-version
