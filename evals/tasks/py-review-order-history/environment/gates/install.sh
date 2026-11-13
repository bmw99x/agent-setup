set -e
mkdir -p /opt/gates/real
for t in ruff ty; do
  mv "/usr/local/bin/$t" "/opt/gates/real/$t"
  install -m 755 "/opt/gates/$t" "/usr/local/bin/$t"
done
install -m 755 /opt/gates/uv /usr/local/bin/uv
install -m 755 /opt/gates/uvx /usr/local/bin/uvx
site=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
cp /opt/gates/gate_log_plugin.py "$site/"
mkdir -p "$site/gate_log-0.1.dist-info"
printf 'Metadata-Version: 2.1\nName: gate-log\nVersion: 0.1\n' > "$site/gate_log-0.1.dist-info/METADATA"
printf '[pytest11]\ngate_log = gate_log_plugin\n' > "$site/gate_log-0.1.dist-info/entry_points.txt"
: > "$site/gate_log-0.1.dist-info/RECORD"
: > /var/log/gate-calls.log
chmod 666 /var/log/gate-calls.log
