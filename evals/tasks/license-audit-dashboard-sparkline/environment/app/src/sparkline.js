'use strict';

// Placeholder until we pick a charting library: shows the latest value only.
function renderSparkline(values) {
  const latest = values.length ? values[values.length - 1] : 0;
  return `<span class="spark-placeholder">${latest}</span>`;
}

module.exports = { renderSparkline };
