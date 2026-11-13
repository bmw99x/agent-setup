'use strict';
// Pack each package under argv[2] into a registry tree at argv[3] with packuments.
const { execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const [src, out] = process.argv.slice(2);
for (const dir of fs.readdirSync(src)) {
  const pkg = JSON.parse(fs.readFileSync(path.join(src, dir, 'package.json')));
  const dest = path.join(out, pkg.name, '-');
  fs.mkdirSync(dest, { recursive: true });
  const tgz = execFileSync('npm', ['pack', '--silent', '--pack-destination', dest], { cwd: path.join(src, dir) })
    .toString().trim().split('\n').pop();
  const data = fs.readFileSync(path.join(dest, tgz));
  const manifest = {
    ...pkg,
    _id: `${pkg.name}@${pkg.version}`,
    dist: {
      tarball: `http://127.0.0.1:4873/${pkg.name}/-/${tgz}`,
      shasum: crypto.createHash('sha1').update(data).digest('hex'),
      integrity: 'sha512-' + crypto.createHash('sha512').update(data).digest('base64'),
    },
  };
  const packument = { name: pkg.name, 'dist-tags': { latest: pkg.version }, versions: { [pkg.version]: manifest },
    time: { [pkg.version]: '2026-03-01T00:00:00.000Z' } };
  fs.writeFileSync(path.join(out, pkg.name, 'packument.json'), JSON.stringify(packument));
}
