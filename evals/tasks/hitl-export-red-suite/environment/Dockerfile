FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
RUN pip install --no-cache-dir pytest==8.3.5
COPY app/ /app/
WORKDIR /app
RUN cp -a /app /opt/base && chmod -R a-w /opt/base \
 && mv tests/partner_feed/test_feed.py /tmp/test_feed.py \
 && printf 'from app.partner_feed.feed import build_feed\n\n\ndef test_feed_item_carries_decimal_price():\n    products = [{"sku": "MUG-01", "name": "Mug", "price_pence": 1250}]\n\n    assert build_feed(products) == [{"sku": "MUG-01", "title": "Mug", "price": "12.50"}]\n' > tests/partner_feed/test_feed.py \
 && git init -q && git add -A \
 && GIT_AUTHOR_DATE="2026-10-02T10:00:00" GIT_COMMITTER_DATE="2026-10-02T10:00:00" git commit -q -m "backoffice: finance export and Shopwise feed" \
 && cp /tmp/test_feed.py tests/partner_feed/test_feed.py && git add -A \
 && GIT_AUTHOR_NAME="Priya Shah" GIT_AUTHOR_EMAIL="priya@example.com" GIT_AUTHOR_DATE="2026-11-11T16:05:00" GIT_COMMITTER_DATE="2026-11-11T16:05:00" \
    git commit -q -m "test(partner-feed): expect Shopwise v3 item format (WIP)" \
 && git log --oneline
