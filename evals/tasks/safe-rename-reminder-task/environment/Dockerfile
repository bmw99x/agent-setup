FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest==8.4.2 huey==2.5.3
COPY app/ /app/
WORKDIR /app
RUN git init -q && git add -A && git commit -qm "Clinic reminders"
# Snapshot of the production schedule, written by the pre-rename code (verifier-only).
COPY seed/seed_queue.py /opt/eval/seed_queue.py
RUN mkdir -p /var/lib/reminders && chmod 777 /var/lib/reminders && cd /app \
 && PYTHONPATH=/app REMINDERS_QUEUE_DB=/opt/eval/prod-schedule.db python /opt/eval/seed_queue.py \
 && rm /opt/eval/seed_queue.py && chmod -R go-rwx /opt/eval
