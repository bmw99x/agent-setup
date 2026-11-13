'use strict';
const { polyline } = require('svgpath-tools');

function sparkline(values, { width = 120, height = 24, stroke = 'currentColor' } = {}) {
  if (!Array.isArray(values) || values.length === 0) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"></svg>`;
  }
  const min = Math.min(...values);
  const span = Math.max(...values) - min || 1;
  const step = values.length > 1 ? width / (values.length - 1) : 0;
  const points = values.map((v, i) => [i * step, height - ((v - min) / span) * height]);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`
    + `<path d="${polyline(points)}" fill="none" stroke="${stroke}"/></svg>`;
}

module.exports = { sparkline };
