'use strict';
const http = require('http');
const { renderSparkline } = require('./sparkline');

const latencyMs = { api: [120, 98, 143, 110, 87, 95], web: [45, 52, 48, 61, 50, 47] };

function page() {
  const rows = Object.entries(latencyMs)
    .map(([service, values]) => `<tr><td>${service}</td><td>${renderSparkline(values)}</td></tr>`)
    .join('');
  return `<!doctype html><title>Status</title><table>${rows}</table>`;
}

if (require.main === module) {
  http.createServer((req, res) => {
    res.writeHead(200, { 'content-type': 'text/html' });
    res.end(page());
  }).listen(process.env.PORT || 3000);
}

module.exports = { page };
