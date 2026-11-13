'use strict';
// Copyright (C) svgpath-tools authors. Licensed under the GNU Affero General Public License v3.0.
const round = (n) => Math.round(n * 100) / 100;

function polyline(points) {
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${round(x)} ${round(y)}`).join(' ');
}

module.exports = { polyline };
