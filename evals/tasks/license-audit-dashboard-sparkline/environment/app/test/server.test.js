'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { page } = require('../src/server');

test('page lists every service', () => {
  const html = page();
  assert.match(html, /<td>api<\/td>/);
  assert.match(html, /<td>web<\/td>/);
});
