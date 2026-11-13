FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest "pydantic>=2.12" setuptools
COPY parcelhub/ /opt/parcelhub/
RUN pip install --no-cache-dir --no-build-isolation /opt/parcelhub && rm -rf /opt/parcelhub
COPY app/ /app/
WORKDIR /app
