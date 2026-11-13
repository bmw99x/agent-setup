FROM python:3.12-slim
RUN pip install --no-cache-dir pytest==8.3.5 fastapi==0.115.6 httpx==0.28.1
COPY tools/ /opt/eval-tools/
COPY app/ /app/
WORKDIR /app
RUN python manage.py migrate && python -m scripts.seed_dev \
 && python /opt/eval-tools/legacy_ref_digest.py var/dev.db > /etc/eval-legacy-ref.sha256 && chmod 444 /etc/eval-legacy-ref.sha256 \
 && rm -rf /app/.pytest_cache && cp -a /app /opt/base && chmod -R a-w /opt/base
