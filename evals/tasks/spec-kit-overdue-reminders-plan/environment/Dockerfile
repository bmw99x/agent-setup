FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git jq && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest==8.3.5
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A -- . ':!specs' ':!.specify/feature.json' && git commit -qm "Lending desk 0.4.0" \
 && git checkout -q -b 001-overdue-reminders && git add -A && git commit -qm "docs(spec): overdue reminders spec (approved)" \
 && git rev-parse HEAD > /etc/eval-base-sha && cp -a /app /opt/base && chmod 444 /etc/eval-base-sha
