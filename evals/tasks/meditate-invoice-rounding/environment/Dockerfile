FROM python:3.12-slim
RUN pip install --no-cache-dir pytest
COPY app/ /app/
RUN cd /app && find CLAUDE.md .claude -type f -print0 | sort -z | xargs -0 sha256sum > /etc/eval-base-hashes \
 && find /app -name SKILL.md | sort > /etc/eval-base-skill-files \
 && chmod 444 /etc/eval-base-hashes /etc/eval-base-skill-files
WORKDIR /app
