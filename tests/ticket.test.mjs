import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
const publishedUrl = 'https://richard-gnitnub.github.io/linktree-clone-css-js/';

test('the ticket uses the published URL even when the site is previewed elsewhere', async () => {
  const canonical = [...html.matchAll(/<link\s+rel="canonical"\s+href="([^"]+)"/g)];
  assert.equal(canonical.length, 1, 'the generator needs one unambiguous published URL');
  assert.equal(canonical[0][1], publishedUrl);
  const pdf = await readFile(new URL('../assets/sharing-ticket.pdf', import.meta.url));
  const destinations = [...pdf.toString('latin1').matchAll(/\/URI\s*\(([^)]*)\)/g)].map(match => match[1]);
  assert.equal(destinations.length, 3, 'the A4 sheet has three clickable tickets');
  assert.ok(destinations.every(url => url === publishedUrl), 'all tickets must link to the published site');
});

test('the ticket offers valid local downloads without JavaScript', async () => {
  const section = html.match(/<section class="sharing-ticket" aria-labelledby="ticket-title">([\s\S]*?)<\/section>/)?.[1];
  assert.ok(section, 'the ticket needs an accessible section');
  const downloads = [...section.matchAll(/<a[^>]+href="([^"]+)"[^>]+download="([^"]+)"/g)];
  assert.equal(downloads.length, 2, 'offer the sharing image and print sheet');
  for (const [, path, filename] of downloads) {
    assert.match(path, /^assets\/[\w-]+\.(png|pdf)$/, 'download a local static file');
    assert.equal(filename.split('.').at(-1), path.split('.').at(-1));
    const data = await readFile(new URL('../' + path, import.meta.url));
    if (path.endsWith('.png')) {
      assert.deepEqual(data.subarray(0, 8), Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
      const preview = section.match(/width="(\d+)" height="(\d+)"/);
      assert.ok(preview);
      assert.equal(data.readUInt32BE(16), Number(preview[1]));
      assert.equal(data.readUInt32BE(20), Number(preview[2]));
    } else {
      assert.equal(data.subarray(0, 5).toString(), '%PDF-');
    }
  }
});
