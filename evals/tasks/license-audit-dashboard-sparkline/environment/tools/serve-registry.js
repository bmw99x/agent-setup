'use strict';
// Serves /opt/registry as an npm registry: /<name> -> packument, /<name>/-/<file>.tgz -> tarball.
const http = require('http');
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
  const file = url.includes('/-/') ? path.join(root, url) : path.join(root, url, 'packument.json');
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, { 'content-type': 'application/json' }); res.end('{"error":"not found"}'); return; }
    res.writeHead(200, { 'content-type': file.endsWith('.tgz') ? 'application/octet-stream' : 'application/json' });
    res.end(data);
  });
}).listen(4873, '127.0.0.1');
