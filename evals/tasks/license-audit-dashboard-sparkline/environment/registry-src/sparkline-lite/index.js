'use strict';
module.exports = function sparkline(values, width = 120, height = 24) {
  const min = Math.min(...values);
  const span = Math.max(...values) - min || 1;
  const step = values.length > 1 ? width / (values.length - 1) : 0;
  const d = values.map((v, i) => `${i ? 'L' : 'M'}${(i * step).toFixed(2)} ${(height - ((v - min) / span) * height).toFixed(2)}`).join(' ');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><path d="${d}" fill="none" stroke="currentColor"/></svg>`;
};
