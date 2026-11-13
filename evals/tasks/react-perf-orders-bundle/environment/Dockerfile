FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends git python3 python3-pytest && rm -rf /var/lib/apt/lists/* \
 && git config --system user.name "Dev" && git config --system user.email "dev@example.com" \
 && git config --system safe.directory '*' && git config --system init.defaultBranch main
WORKDIR /app
COPY app/package.json /app/package.json
RUN npm install --no-audit --no-fund
COPY app/ /app/
RUN git init -q && printf 'node_modules/\n' > .gitignore && git add -A && git commit -qm "Orders admin"
