// node --test gfx/test/*.test.mjs   (post_gfx.mjs: the LinkedIn post graphic that stands alone, from grafika.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { CSP, checkPostGfx, fitProblems, gfxWords, overflow, postHtml } from '../post_gfx.mjs';

const list = (more = {}) => ({ type: 'list', title: 'Trzy drobiazgi, które oszczędzają nerwy', kicker: 'Praca z AI',
  items: [{ h: 'Pamięć między rozmowami', t: 'Notatka na koniec pracy, wczytana na początku następnej.' },
          { h: 'Stop przy kręceniu się', t: 'Ten sam ruch kilka razy: AI szuka innej drogi.' }], ...more });

test('a good list and a good bar chart pass; the words are counted in reading order', () => {
  assert.deepEqual(checkPostGfx(list()), []);
  const bars = { type: 'bars', title: 'Zmiany bez przeglądu', unit: '%', note: 'Ponad 8 na 10 zmian ktoś ogląda, zanim wejdą do kodu.',
    items: [{ label: 'Przed systemem', value: 92, tone: 'bad' }, { label: 'Dziś', value: 18 }] };
  assert.deepEqual(checkPostGfx(bars), []);
  assert.ok(gfxWords(bars).includes('92%'));
  assert.equal(gfxWords(list())[0], 'Praca');
});

test('a bad spec names every problem: type, title length, entries, too few words, a long dash', () => {
  const bad = checkPostGfx({ type: 'pie', title: 'Jedno', items: [] });
  for (const want of ['"type"', '"title"', 'words on the graphic']) assert.ok(bad.some(b => b.includes(want)), `${want}\n${bad.join('\n')}`);
  assert.ok(checkPostGfx(list({ items: [{ h: 'a' }] })).some(b => b.includes('"items": 2-8')));
  assert.ok(checkPostGfx(list({ note: 'to jest — myślnik' })).some(b => b.includes('long dash')));
  assert.ok(checkPostGfx({ ...list(), type: 'table', head: ['a'], rows: [['x', 'y'], ['z']] }).some(b => b.includes('2 cells')));
});

test('a malformed grafika.json is a named problem, not a TypeError', () => {
  for (const g of [null, [], { type: 'list', title: 'a b', items: [null, { h: 'x' }] }, { type: 'table', title: 'a b', head: 5, rows: [] },
    { type: 'table', title: 'a b', head: ['a', 'b'], rows: [null, ['x', 'y']] }, { type: 'list', title: 'a b', items: [{ h: 'x' }, { h: 'y' }], cols: [{ lines: 5 }] },
    { type: 'bars', title: 'a b', items: [{ label: 'x', value: { toString: null } }, { label: 'y', value: 1 }] }])
    assert.ok(checkPostGfx(g).length > 0, JSON.stringify(g));
});

test('tone and theme are names from a list: markup in them is refused and escaped (review 2026-11-05: /etc/passwd in the graphic)', () => {
  const evil = 'bad"><iframe src="file:///etc/passwd"></iframe><i class="';
  const bars = { type: 'bars', title: 'Zmiany bez przeglądu', unit: '%', note: 'Ponad osiem na dziesięć zmian ktoś ogląda, zanim wejdą.',
    items: [{ label: 'Przed', value: 92, tone: evil }, { label: 'Dziś', value: 18 }] };
  assert.ok(checkPostGfx(bars).some(b => b.includes('"tone"')));
  assert.doesNotMatch(postHtml(bars), /<iframe/);
  const split = { type: 'split', title: 'Tabliczka kontra szlaban', cols: [{ head: 'a', tone: evil, lines: ['x'] }, { head: 'b', lines: ['y'] }] };
  assert.doesNotMatch(postHtml(split), /<iframe/);
  assert.ok(checkPostGfx({ ...list(), theme: '../../style/themes/cetus' }).some(b => b.includes('"theme"')));
  assert.throws(() => postHtml({ ...list(), theme: '../../style/themes/cetus' }), /"theme" must be a name/);
  assert.match(CSP, /default-src 'none'/);  // the page loads no frame, image or script even if markup got through
});

test('html: words escaped, a short bar carries its number outside the fill', () => {
  const h = postHtml(list({ title: '<b>Gotowe</b> bez dowodu' }));
  assert.match(h, /&lt;b&gt;Gotowe/); assert.doesNotMatch(h, /<b>Gotowe/);
  const b = postHtml({ type: 'bars', title: 'x y', unit: '%', items: [{ label: 'a', value: 92 }, { label: 'b', value: 18 }] });
  assert.match(b, /width:100%">92%</); assert.match(b, /class="val" style="left:19.5\d*%">18%</);
});

test('fit: overflow and a half empty page are named, a full page passes', () => {
  assert.deepEqual(fitProblems({ wide: [['h', 400, 400]], bottom: 1100, foot: 1250 }), []);
  assert.ok(overflow({ wide: [['h "x"', 520, 400]], bottom: 1100, foot: 1250 })[0].includes('120 px wider'));
  assert.ok(fitProblems({ wide: [], bottom: 1260, foot: 1250 })[0].includes('into the footer'));
  assert.ok(fitProblems({ wide: [], bottom: 600, foot: 1250 })[0].includes('empty above the footer'));
});

test('a render writes grafika.png and grafika.txt; an overfull list stops with the reason', { skip: !fs.existsSync('/usr/bin/google-chrome') }, async () => {
  const { spawnSync } = await import('child_process');
  const cli = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../post_gfx.mjs');
  const ok = fs.mkdtempSync(path.join(os.tmpdir(), 'post-gfx-ok-')), full = fs.mkdtempSync(path.join(os.tmpdir(), 'post-gfx-full-'));
  fs.writeFileSync(path.join(ok, 'grafika.json'), JSON.stringify(list()));
  const long = 'długi opis pozycji, który zajmuje dwie linie na grafice';
  fs.writeFileSync(path.join(full, 'grafika.json'), JSON.stringify(list({ items: Array.from({ length: 8 }, (_, i) => ({ h: `Pozycja ${i}`, t: `${long} i jeszcze trochę` })) })));
  const r1 = spawnSync('node', [cli, ok], { encoding: 'utf8' });
  assert.equal(r1.status, 0, r1.stderr);
  assert.ok(fs.statSync(path.join(ok, 'grafika.png')).size > 10000);
  assert.match(fs.readFileSync(path.join(ok, 'grafika.txt'), 'utf8'), /^Praca z AI Trzy drobiazgi/);
  const r2 = spawnSync('node', [cli, full], { encoding: 'utf8' });
  assert.notEqual(r2.status, 0); assert.match(r2.stderr, /into the footer/);
  assert.ok(!fs.existsSync(path.join(full, 'grafika.png')));
});
