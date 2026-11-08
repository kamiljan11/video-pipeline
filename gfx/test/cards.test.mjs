// node --test gfx/test/*.test.mjs   (plan2 cards, gfx/cards_lib.mjs: HTML only, no browser, no render)
// L8 list upto / dim_done, L9 chap_style roadmap / part_tag, L12 lower define, L21 note; legacy specs draw as before
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'child_process';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { chapHtml, checkCard, lineCount, listHtml, lowerHtml, noteHtml, usesCardsLib } from '../cards_lib.mjs';
import { esc, icon } from '../html_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const anims = html => [...html.matchAll(/class="i[^"]*" style="animation:([^"]*)"/g)].map(m => m[1]);

test('legacy list, chap and lower specs give the markup of before (same .mov keys, same stills)', () => {
  const list = { id: 'l', type: 'list', text: 'Trzy rzeczy', items: ['a', 'b <c>'], icons: [null, 'check'], delays: [0.2, 1.5], dur: 5 };
  const old = `<div class="list"><div class="h">${esc(list.text)}</div>${list.items.map((x,i)=>`<div class="i" style="animation:slide .45s ${(list.delays||[])[i]??i}s both">${(list.icons||[])[i]?`<span class="li">${icon(list.icons[i])}</span>`:`<b>${i+1}</b>`}<span>${esc(x)}</span></div>`).join('')}</div>`;
  assert.equal(listHtml(list), old);
  assert.equal(chapHtml({ type: 'chap', text: 'Pamięć', sub: 'CZĘŚĆ 2' }), '<div class="chap"><div class="no">CZĘŚĆ 2</div><div class="t">Pamięć</div></div>');
  assert.equal(lowerHtml({ type: 'lower', text: 'Kamil', sub: 'MAS' }), '<div class="lower"><div class="acc"></div><div class="box"><div class="n">Kamil</div><div class="r">MAS</div></div></div>');
  for (const sp of [list, { type: 'chap' }, { type: 'lower' }, { type: 'kw' }]) assert.equal(usesCardsLib(sp), false);
});

test('L8 a stacked list with dim_done greys each item when the next one comes in', () => {
  const a = anims(listHtml({ id: 's', type: 'list', text: 'Kroki', items: ['jeden', 'dwa', 'trzy'], delays: [0, 2.5, 5.1], dim_done: true, dur: 8 }));
  assert.deepEqual(a, ['slide .45s 0s both,ldim .3s 2.5s forwards', 'slide .45s 2.5s both,ldim .3s 5.1s forwards', 'slide .45s 5.1s both']);
});

test('L8 upto shows items 1..k: the earlier ones stand still (dimmed with dim_done), only the k-th comes in', () => {
  const sp = { id: 'u', type: 'list', text: 'Kroki', items: ['jeden', 'dwa', 'trzy', 'cztery'], upto: 3, dim_done: true, delays: [null, null, 0.4], dur: 4 };
  const html = listHtml(sp);
  assert.equal((html.match(/class="i/g) ?? []).length, 3, 'item 4 is not on the card yet');
  assert.ok(!html.includes('cztery'));
  assert.deepEqual(anims(html), ['none', 'none', 'slide .45s 0.4s both']);
  assert.equal((html.match(/class="i done"/g) ?? []).length, 2);
  assert.ok(html.startsWith('<style>') && html.indexOf('<div class="list">') > 0, 'own css before the card: nth-child of the items unchanged');
  assert.deepEqual(anims(listHtml({ ...sp, delays: undefined, dim_done: undefined })), ['none', 'none', 'slide .45s 0.3s both']);
});

test('L8 bad upto / delays stop by name', () => {
  const base = { id: 'b', type: 'list', text: 'x', items: ['a', 'b', 'c'], dur: 4 };
  for (const [patch, msg] of [[{ upto: 4 }, /"upto" = a whole number 1..3/], [{ upto: 0 }, /"upto"/], [{ dim_done: 'yes' }, /"dim_done" = true or false/],
    [{ upto: 2, delays: [0.1, 0.5] }, /"delays"\[0\]: item 1 is already on the card/], [{ dim_done: true, delays: [0, 2, 1] }, /must not go back in time/],
    [{ dim_done: true, delays: [0, 3, null] }, /must not go back in time/],  // a missing delay = its index (2 s), before item 2 at 3 s
    [{ dim_done: true, delays: [0, 9] }, /"delays"\[1\] = seconds 0..dur/], [{ upto: 2, canvas: 'v' }, /16:9 only/]])
    assert.throws(() => checkCard({ ...base, ...patch }), msg, JSON.stringify(patch));
});

test('L9 roadmap: every part in the same place, done / current / next styled apart, only the current row moves', () => {
  const parts = ['Pamięć', 'Narzędzia', 'Agenci', 'Koszty'];
  const html = chapHtml({ id: 'c2', type: 'chap', chap_style: 'roadmap', parts, current: 3, dur: 4 });
  const rows = [...html.matchAll(/<div class="r (\w+)" style="animation:([^"]*)"><b>([\s\S]*?)<\/b><span>([^<]*)<\/span>/g)].map(m => [m[1], m[2], m[4]]);
  assert.deepEqual(rows.map(r => r[0]), ['done', 'done', 'cur', 'next']);
  assert.deepEqual(rows.map(r => r[2]), parts);
  assert.deepEqual(rows.map(r => r[1] === 'none'), [true, true, false, true]);
  assert.match(html, /<div class="no">3\/4<\/div>/);
  assert.match(html, /<div class="r done"[^>]*><b>\s*<svg/, 'a done part has a check mark');
  const opening = chapHtml({ id: 'c0', type: 'chap', chap_style: 'roadmap', parts, current: 0, text: 'Plan', dur: 6 });
  assert.equal((opening.match(/class="r next"/g) ?? []).length, 4, 'the opening roadmap: nothing done yet');
  assert.equal((opening.match(/slide \.45s/g) ?? []).length, 4, 'its rows come in one by one');
  assert.ok(!opening.includes('class="no"'));
});

test('L9 part_tag: a small corner tag with the part number and title, not a full screen', () => {
  const html = chapHtml({ id: 't2', type: 'chap', chap_style: 'part_tag', parts: ['A b', 'Narzędzia'], current: 2, dur: 4 });
  assert.match(html, /<div class="ptag"><b>2\/2<\/b><span>Narzędzia<\/span><\/div>/);
  assert.match(html, /\.ptag\{position:absolute;left:70px;top:60px/, 'top left: the face circle (PiP) is bottom right');
  assert.ok(!html.includes('class="chap'));
  for (const [patch, msg] of [[{ chap_style: 'map' }, /"chap_style" = "roadmap" or "part_tag"/], [{ current: 0 }, /"current" = the part that starts here, 1..2/],
    [{ parts: ['jedna'] }, /"parts" = 2..8 part titles/], [{ parts: ['x'.repeat(41), 'b'] }, /at most 40 characters/]])
    assert.throws(() => checkCard({ id: 't', type: 'chap', chap_style: 'part_tag', parts: ['a', 'b'], current: 1, dur: 3, ...patch }), msg);
});

test('L12 define: the term in the accent over its definition, on the lower third, >= 6 s', () => {
  const sp = { id: 'd', type: 'lower', define: true, text: 'RAG', sub: 'model najpierw szuka w twoich dokumentach, potem odpowiada', dur: 7 };
  const html = lowerHtml(sp);
  assert.match(html, /<div class="lower define">.*<div class="n">RAG<\/div><div class="r">model najpierw/);
  assert.match(html, /\.lower\.define \.n\{color:var\(--acc\)\}/, 'theme token, no new colour');
  assert.throws(() => checkCard({ ...sp, dur: 5 }), /stays >= 6 s/);
  assert.throws(() => checkCard({ ...sp, sub: Array(21).fill('słowo').join(' ') }), /1..20 words, got 21/);
  assert.throws(() => checkCard({ ...sp, text: 'a b c d e' }), /the term, 1..4 words/);
  assert.throws(() => checkCard({ ...sp, define: 'yes' }), /"define" = true/);
});

test('L21 note: <= 14 words / 3 lines, bottom left (away from the face circle), >= 4 s', () => {
  const sp = { id: 'n', type: 'note', text: 'Link do repozytorium\nw opisie filmu', icon: 'link', dur: 5 };
  const html = noteHtml(sp);
  assert.match(html, /\.note\{position:absolute;left:110px;bottom:120px/);
  assert.match(html, /<div class="t">Link do repozytorium<br>w opisie filmu<\/div>/);
  assert.match(html, /<span class="ni">\s*<svg/);
  assert.ok(usesCardsLib(sp));
  assert.throws(() => checkCard({ ...sp, text: Array(15).fill('raz').join(' ') }), /1..14 words, got 15/);
  assert.throws(() => checkCard({ ...sp, text: 'a\nb\nc\nd' }), /at most 3 lines/);
  assert.throws(() => checkCard({ ...sp, dur: 3 }), /stays >= 4 s/);
  assert.throws(() => checkCard({ ...sp, canvas: 'v' }), /16:9 only/);
});

test('lineCount wraps at whole words', () => {
  assert.equal(lineCount('abc def', 7), 1);
  assert.equal(lineCount('abc defg', 7), 2);
  assert.equal(lineCount('a\nb', 40), 2);
  assert.equal(lineCount('', 40), 1);
});

test('render.mjs stops a bad new card by name before it opens a browser', () => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'cards-'));
  try {
    const f = path.join(work, 'gfx_specs.json');
    fs.writeFileSync(f, JSON.stringify([{ id: 'n1', type: 'note', text: Array(20).fill('za').join(' '), dur: 5 }]));
    const r = spawnSync('node', [path.join(GFX, 'render.mjs'), f, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 30000 });
    assert.notEqual(r.status, 0);
    assert.match(r.stderr, /FAILED gfx n1: "n1": a note is 1..14 words, got 20/);
    assert.ok(!fs.existsSync(path.join(work, 'gfx')), 'nothing rendered, no output folder');
  } finally { fs.rmSync(work, { recursive: true, force: true }); }
});
