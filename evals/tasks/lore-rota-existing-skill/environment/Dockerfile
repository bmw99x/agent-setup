FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git jq make && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest pyyaml
COPY fakes/ /tmp/fakes/
RUN for name in glab gh; do install -m 755 /tmp/fakes/fakeforge.py /usr/local/bin/$name; done \
 && site=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') \
 && cp -r /tmp/fakes/sentry_sdk "$site/sentry_sdk" \
 && cp /tmp/fakes/runlog.py "$site/eval_runlog.py" && mkdir "$site/eval_runlog-0.1.dist-info" \
 && printf 'Metadata-Version: 2.1\nName: eval-runlog\nVersion: 0.1\n' > "$site/eval_runlog-0.1.dist-info/METADATA" \
 && printf '[pytest11]\nrunlog = eval_runlog\n' > "$site/eval_runlog-0.1.dist-info/entry_points.txt" \
 && python3 /tmp/fakes/build_history.py /tmp/fakes/history.py && rm -rf /tmp/fakes \
 && chmod 444 /opt/fakes/forge.json && mkdir -p /var/log/fakes && chmod 1777 /var/log/fakes
COPY local-skill/ /app/
RUN printf '.claude/\n' >> /app/.git/info/exclude \
 && git -C /app rev-parse HEAD > /etc/eval-base-sha \
 && (cd /app && find .claude -type f -print0 | sort -z | xargs -0 sha256sum) > /etc/eval-base-hashes \
 && find / \( -path /proc -o -path /sys -o -path /dev -o -path /app \) -prune -o -name SKILL.md -print 2>/dev/null \
    | sort > /etc/eval-base-global-skills \
 && rm -f /var/log/fakes/*.jsonl \
 && chmod 444 /etc/eval-base-sha /etc/eval-base-hashes /etc/eval-base-global-skills
WORKDIR /app

# The agent runs as uid 10001: let it write the fakes' logs/state and push to the local remotes.
RUN for d in /var/log/fakes /var/lib/fakes /srv/git /var/log/psql-prod /var/log/license-scans /var/log/pytest-sessions; do \
      if [ -e "$d" ]; then chmod -R a+rwX "$d"; fi; done
