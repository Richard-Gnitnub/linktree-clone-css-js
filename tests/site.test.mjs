import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');

test('the page has responsive and accessible landmarks', () => {
  assert.match(html, /<html lang="en-GB">/);
  assert.match(html, /<meta name="viewport" content="width=device-width, initial-scale=1">/);
  assert.match(html, /<main id="main-content">/);
  assert.match(html, /id="share-status"[^>]*role="status"/);
  assert.match(html, /<h1>/);
});

test('the Blog destination is the actual Rich B Modeller blog', () => {
  assert.match(html, /href="https:\/\/richbmodeller\.com\/blogs\/news"/);
  assert.doesNotMatch(html, /ellenfoot-yard\.vercel\.app|bytes\.dev/);
});

test('all listed destinations are HTTPS links with separate copy controls', () => {
  const rows = [...html.matchAll(/<li class="service">([\s\S]*?)<\/li>/g)].map((match) => match[1]);
  assert.equal(rows.length, 3);
  for (const row of rows) {
    const match = row.match(/<a class="service-link" href="([^"]+)">/);
    assert.ok(match, 'each service requires a real destination');
    assert.equal(new URL(match[1]).protocol, 'https:');
    assert.ok(row.indexOf('</a>') < row.indexOf('<button'), 'copy button must not be nested in the link');
    assert.match(row, /type="button" data-copy aria-label="Copy [^"]+ link"/);
  }
});

test('TrackTemplate has a separate featured section with a direct repository link', () => {
  assert.match(html, /<section class="featured-project" aria-labelledby="tracktemplate-title">/);
  assert.match(html, /href="https:\/\/github\.com\/Richard-Gnitnub\/tracktemplate"/);
});
