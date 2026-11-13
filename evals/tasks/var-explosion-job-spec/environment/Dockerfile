FROM python:3.12-slim
RUN pip install --no-cache-dir pytest
COPY app/ /app/
RUN cd /app && find billing_plugin -type f -name '*.py' | sort | xargs sha256sum > /etc/eval-billing-plugin.sha256 \
 && chmod 444 /etc/eval-billing-plugin.sha256
WORKDIR /app
