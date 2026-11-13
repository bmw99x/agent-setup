FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git jq && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main \
 && git config --system core.sshCommand /usr/local/libexec/git-ssh
RUN pip install --no-cache-dir pytest==8.3.4 ruff==0.8.4 \
 && mkdir -p /opt/ruff-real && mv /usr/local/bin/ruff /opt/ruff-real/ruff
COPY fakes/ /opt/fakes/
RUN for name in glab gh; do install -m 755 /opt/fakes/fakecli.py /usr/local/bin/$name; done \
 && install -m 755 /opt/fakes/ruff-wrapper.py /usr/local/bin/ruff \
 && install -D -m 755 /opt/fakes/git-ssh /usr/local/libexec/git-ssh \
 && site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') \
 && cp /opt/fakes/runlog.py "$site/eval_runlog.py" && mkdir "$site/eval_runlog-0.1.dist-info" \
 && printf 'Metadata-Version: 2.1\nName: eval-runlog\nVersion: 0.1\n' > "$site/eval_runlog-0.1.dist-info/METADATA" \
 && printf '[pytest11]\nrunlog = eval_runlog\n' > "$site/eval_runlog-0.1.dist-info/entry_points.txt" \
 && mkdir -p /var/log/fakes /var/lib/fakes
COPY app/ /app/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm /tmp/repo-setup.sh \
 && EVAL_NO_RUNLOG=1 PYTHONDONTWRITEBYTECODE=1 python3 /opt/fakes/seed.py \
 && rm -rf /opt/fakes /var/log/fakes/*.jsonl

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
