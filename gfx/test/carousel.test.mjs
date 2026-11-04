// node --test gfx/test/*.test.mjs   (LinkedIn carousel: slides -> PDF pages, a text that does not fit stops by name)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';
import { pdfPages, slidesHtml } from '../carousel_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'carousel-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));
const CHROME = !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome';
const SLIDES = [
  { type: 'cover', title: '95% firm nie widzi zysku z AI', sub: 'Trzy zasady' },
  { type: 'point', title: 'Proces przed narzędziem', body: 'Policz koszt ręcznej pracy.' },
  { type: 'point', title: 'Jeden cel <b>', body: 'Godziny & złotówki.' },
  { type: 'end', title: 'Cały film na YouTube', body: 'Link w pierwszym komentarzu.' },
];
const render = (slides, name = 'c') => {
  const dir = path.join(work, name); fs.mkdirSync(dir, { recursive: true });
  const spec = path.join(dir, 'linkedin.json'); fs.writeFileSync(spec, JSON.stringify({ carousel: { title: 't', slides } }));
  const pdf = path.join(dir, 'linkedin.pdf');
  return { pdf, dir, r: spawnSync('node', [path.join(GFX, 'carousel.mjs'), spec, pdf], { encoding: 'utf8', timeout: 120000 }) };
};

test('slides: points are numbered, text is escaped, the order cover..end is enforced', () => {
  const html = slidesHtml(SLIDES, 'Kamil Jan', work);
  assert.deepEqual([...html.matchAll(/class="n">(\d+)</g)].map((m) => m[1]), ['1', '2']);
  assert.match(html, /Jeden cel &lt;b&gt;/); assert.match(html, /Godziny &amp; złotówki/);
  assert.match(html, /4\/4<\/span>/);
  for (const [slides, why] of [[[SLIDES[1], SLIDES[3]], /first slide and only the first is "cover"/],
                               [[SLIDES[0], SLIDES[1]], /last slide and only the last is "end"/],
                               [[SLIDES[0], { type: 'quote', title: 'x' }, SLIDES[3]], /cover, point or end/],
                               [[{ ...SLIDES[0], photo: 'gone.jpg' }, SLIDES[3]], /photo .* missing/],
                               [[{ ...SLIDES[0], photo: 'x.gif' }, SLIDES[3]], /\.jpg or \.png/],
                               [[{ ...SLIDES[0], photo: '../elsewhere.png' }, SLIDES[3]], /inside the spec folder/],
                               [[{ ...SLIDES[0], photo: '/etc/x.png' }, SLIDES[3]], /inside the spec folder/],
                               [[SLIDES[0], { ...SLIDES[1], photo: 'a.jpg' }, SLIDES[3]], /only the cover slide/]]) {
    assert.throws(() => slidesHtml(slides, 'K', work), why);
  }
});

test('pdfPages counts pages, not the /Pages tree', () => {
  assert.deepEqual(pdfPages(Buffer.from('/Type /Pages /Type /Page /MediaBox [0 0 810 1012.5] /Type/Page')), { pages: 2, width: 810, height: 1012.5 });
});

test('a carousel renders one 1080x1350 page per slide', { skip: CHROME }, () => {
  const { pdf, r } = render(SLIDES);
  assert.equal(r.status, 0, r.stderr);
  const got = pdfPages(fs.readFileSync(pdf));
  assert.equal(got.pages, 4);
  assert.equal(got.width, 810);  // 1080 px at 96 dpi = 810 pt
  assert.ok(Math.abs(got.height / got.width - 1350 / 1080) < 0.002, `not 4:5: ${got.width}x${got.height}`);
});

test('a cover photo is drawn; a text that does not fit stops by name and leaves no PDF', { skip: CHROME }, () => {
  fs.mkdirSync(path.join(work, 'photo'));
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=red:s=200x200', '-frames:v', '1', path.join(work, 'photo', 'face.png')]);
  const ok = render([{ ...SLIDES[0], photo: 'face.png', sub: "$& $' $` $$ stays text" }, SLIDES[3]], 'photo');
  assert.equal(ok.r.status, 0, ok.r.stderr);
  const text = execFileSync('pdftotext', [ok.pdf, '-'], { encoding: 'utf8' });
  assert.match(text, /\$& \$' \$` \$\$ stays text/);  // String.replace would have spliced the template in here
  const long = render([SLIDES[0], { ...SLIDES[1], body: 'bardzo długi tekst '.repeat(80) }, SLIDES[3]], 'long');
  assert.notEqual(long.r.status, 0);
  assert.match(long.r.stderr, /FAILED carousel .*slide 2: text does not fit/);
  assert.equal(fs.existsSync(long.pdf), false);
});
