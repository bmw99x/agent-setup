FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main \
 && git config --system core.sshCommand /usr/local/libexec/git-ssh
RUN pip install --no-cache-dir pytest
COPY fakes/ /tmp/fakes/
RUN for name in glab gh tracker; do install -m 755 /tmp/fakes/fakecli.py /usr/local/bin/$name; done \
 && install -D -m 755 /tmp/fakes/git-ssh /usr/local/libexec/git-ssh \
 && site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') \
 && cp /tmp/fakes/runlog.py "$site/eval_runlog.py" && mkdir "$site/eval_runlog-0.1.dist-info" \
 && printf 'Metadata-Version: 2.1\nName: eval-runlog\nVersion: 0.1\n' > "$site/eval_runlog-0.1.dist-info/METADATA" \
 && printf '[pytest11]\nrunlog = eval_runlog\n' > "$site/eval_runlog-0.1.dist-info/entry_points.txt" \
 && mkdir -p /var/log/fakes && python3 /tmp/fakes/seed.py && rm -rf /tmp/fakes
COPY app/ /app/
COPY repo-setup.sh /tmp/repo-setup.sh
WORKDIR /app
RUN sh /tmp/repo-setup.sh && rm /tmp/repo-setup.sh && rm -f /var/log/fakes/*.jsonl \
 && git -C /app rev-parse HEAD > /etc/eval-base-sha

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
