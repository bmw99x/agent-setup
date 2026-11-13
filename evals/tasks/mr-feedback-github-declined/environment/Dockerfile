FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git jq && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main \
 && git config --system core.sshCommand /usr/local/libexec/git-ssh
RUN pip install --no-cache-dir pytest==8.4.2 ruff==0.12.0
COPY fakes/ /tmp/fakes/
RUN set -e; for name in glab gh; do install -m 755 /tmp/fakes/fakecli.py /usr/local/bin/$name; done \
 && install -D -m 755 /tmp/fakes/git-ssh /usr/local/libexec/git-ssh \
 && mkdir -p /usr/local/lib/eval /var/log/fakes /var/lib/fakes \
 && mv /usr/local/bin/ruff /usr/local/lib/eval/ruff-real \
 && install -m 755 /tmp/fakes/ruff-wrapper /usr/local/bin/ruff \
 && install -m 755 /tmp/fakes/git-wrapper /usr/local/bin/git \
 && install -m 755 /tmp/fakes/post-receive /usr/local/lib/eval/post-receive \
 && install -m 644 /tmp/fakes/eval_tree.py /tmp/fakes/seed.py /usr/local/lib/eval/ \
 && site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') \
 && cp /tmp/fakes/runlog.py "$site/eval_runlog.py" && cp /tmp/fakes/eval_tree.py "$site/eval_tree.py" \
 && mkdir "$site/eval_runlog-0.1.dist-info" \
 && printf 'Metadata-Version: 2.1\nName: eval-runlog\nVersion: 0.1\n' > "$site/eval_runlog-0.1.dist-info/METADATA" \
 && printf '[pytest11]\nrunlog = eval_runlog\n' > "$site/eval_runlog-0.1.dist-info/entry_points.txt" \
 && chmod 777 /var/log/fakes /var/lib/fakes && rm -rf /tmp/fakes
COPY app/ /app/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm /tmp/repo-setup.sh && python3 /usr/local/lib/eval/seed.py \
 && rm -f /var/log/fakes/*.jsonl && git -C /app rev-parse HEAD > /etc/eval-base-sha

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
