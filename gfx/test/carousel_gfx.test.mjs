// node --test gfx/test/*.test.mjs   (carousel_gfx.mjs: the Instagram carousel from carousel.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import { IDEA_MAX, checkCarousel, slideHtml, slideWords } from '../carousel_gfx.mjs';

const good = (n = 3) => ({ theme: 'cetus', author: 'Kamil Jan · Higher Minds', slides: [
  { type: 'hook', kicker: 'Higher Minds', title: 'Kiedy przestać dokładać blokady', sub: 'Przesuń' },
  ...Array.from({ length: n }, (_, i) => ({ type: 'idea', text: `Jedna myśl numer ${i}.` })),
  { type: 'call', title: 'Którą blokadę obchodzisz?', call: 'Napisz w komentarzu', bio: 'Link w bio' }] });

test('a good carousel passes; 3 to 8 ideas make 5 to 10 slides', () => {
  assert.deepEqual(checkCarousel(good(3)), []);
  assert.deepEqual(checkCarousel(good(8)), []);
  assert.ok(checkCarousel(good(2))[0].includes('want 5-10'));
  assert.ok(checkCarousel(good(9))[0].includes('want 5-10'));
});

test('structure: hook first, call last, ideas between; shapes named, not TypeErrors', () => {
  const c = good(); c.slides[2].type = 'call';
  assert.ok(checkCarousel(c).some(b => b.includes('only the first slide')));
  const d = good(); d.slides[0].type = 'idea';
  assert.ok(checkCarousel(d).some(b => b.includes('first slide = {"type": "hook"}')));
  for (const x of [null, [], { slides: 5 }, { slides: [null] }]) assert.ok(checkCarousel(x).length > 0, JSON.stringify(x));
  const e = good(); e.slides[1].text = 5;
  assert.ok(checkCarousel(e).some(b => b.includes('"text" = a string')));
});

test('limits: an idea over IDEA_MAX, a long dash, a theme that is not a name', () => {
  const c = good(); c.slides[1].text = 'a '.repeat(IDEA_MAX);
  assert.ok(checkCarousel(c).some(b => b.includes('one idea is at most')));
  const d = good(); d.slides[1].text = 'to jest — myślnik';
  assert.ok(checkCarousel(d).some(b => b.includes('long dash')));
  assert.ok(checkCarousel({ ...good(), theme: '../x' }).some(b => b.includes('"theme"')));
});

test('words of a slide in reading order, with no page number; html escapes and draws one dot per slide', () => {
  const c = good();
  assert.deepEqual(slideWords(c.slides[0]), ['Higher', 'Minds', 'Kiedy', 'przestać', 'dokładać', 'blokady', 'Przesuń']);
  assert.ok(!slideWords(c.slides[1]).some(w => /^\d+$/.test(w)));
  c.slides[1].text = '<i>x</i> "y"';
  const h = slideHtml(c, 1);
  assert.match(h, /&lt;i&gt;x/); assert.doesNotMatch(h, /<i>x<\/i>/);
  assert.equal((h.match(/<b( class="on")?><\/b>/g) ?? []).length, c.slides.length);
});
