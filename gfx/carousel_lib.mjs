// LinkedIn document post (ADR-0009): slides of linkedin.json -> HTML pages of gfx/carousel.html, one 1080x1350 page each.
// Limits (how many slides, how long a text) are checked by linkedin.py check; here only what the render itself needs.
import fs from 'fs'; import path from 'path'; import { pathToFileURL } from 'url';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const TYPES = new Set(['cover', 'point', 'end']);
const PHOTO = /\.(jpe?g|png)$/i;

// slide i of n -> named error, or the photo's file URL (null without one)
function checkSlide(sp, i, n, baseDir) {
  const at = `slide ${i + 1}`;
  if (!sp || typeof sp !== 'object' || !TYPES.has(sp.type)) throw new Error(`${at}: "type" must be cover, point or end, got ${JSON.stringify(sp?.type)}`);
  if ((i === 0) !== (sp.type === 'cover')) throw new Error(`${at}: the first slide and only the first is "cover"`);
  if ((i === n - 1) !== (sp.type === 'end')) throw new Error(`${at}: the last slide and only the last is "end"`);
  if (typeof sp.title !== 'string' || !sp.title.trim()) throw new Error(`${at}: "title" must be a non-empty text`);
  for (const k of ['sub', 'body']) if (sp[k] !== undefined && typeof sp[k] !== 'string') throw new Error(`${at}: "${k}" must be a text`);
  if (sp.photo === undefined) return null;
  if (sp.type !== 'cover') throw new Error(`${at}: only the cover slide has a "photo"`);
  const f = path.resolve(baseDir, String(sp.photo));
  const rel = path.relative(baseDir, f);
  if (rel.startsWith('..') || path.isAbsolute(rel)) throw new Error(`${at}: photo must be inside the spec folder, got ${JSON.stringify(sp.photo)}`);
  if (!PHOTO.test(f)) throw new Error(`${at}: photo must be .jpg or .png, got ${JSON.stringify(sp.photo)}`);
  if (!fs.existsSync(f)) throw new Error(`${at}: photo ${f} missing`);
  return pathToFileURL(f).href;
}

// -> the <body> HTML of all slides; numbered points count from 1 among the "point" slides
export function slidesHtml(slides, author, baseDir) {
  if (!Array.isArray(slides) || slides.length < 2) throw new Error('carousel.slides: at least a cover and an end slide');
  let k = 0;
  return slides.map((sp, i) => {
    const photo = checkSlide(sp, i, slides.length, baseDir);
    const foot = `<div class="foot"><b>${esc(author)}</b><span${i < slides.length - 1 ? ' class="swipe"' : ''}>${i < slides.length - 1 ? `${i + 1}/${slides.length} &rarr;` : `${i + 1}/${slides.length}`}</span></div>`;
    const p = (t) => (t ? `<p>${esc(t)}</p>` : '');
    if (sp.type === 'cover') {
      return `<section class="slide cover"><div class="box">${photo ? `<img class="photo" src="${esc(photo)}">` : '<div class="bar"></div>'}<h1>${esc(sp.title)}</h1>${p(sp.sub)}</div>${foot}</section>`;
    }
    if (sp.type === 'point') {
      k += 1;
      return `<section class="slide point"><div class="box"><div class="n">${k}</div><h2>${esc(sp.title)}</h2>${p(sp.body)}</div>${foot}</section>`;
    }
    return `<section class="slide end"><div class="box"><div class="bar"></div><h2>${esc(sp.title)}</h2>${p(sp.body)}</div>${foot}</section>`;
  }).join('\n');
}

// theme tokens (gfx/theme_lib.mjs) as a :root override; null = the template's own colors
export function themeCss(theme) {
  return theme ? `:root{${Object.entries(theme.css).map(([k, v]) => `${k}:${v}`).join(';')}}` : '';
}

// a PDF's page count and the size of its first page in points, without poppler (CI has none)
export function pdfPages(buf) {
  const s = buf.toString('latin1');
  const pages = (s.match(/\/Type\s*\/Page(?![s\w])/g) || []).length;
  const box = s.match(/\/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]/);
  return { pages, width: box ? Number(box[1]) : null, height: box ? Number(box[2]) : null };
}
