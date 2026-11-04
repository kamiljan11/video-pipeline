// node gfx/carousel.mjs <linkedin.json> <out.pdf>: the "carousel" of a LinkedIn post spec as a PDF, one 1080x1350 page
// per slide (ADR-0009). Theme: theme.json next to the spec, like the cards (gfx/theme_lib.mjs). A text that does not fit
// its slide stops the render by name instead of being cut off in the PDF.
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import fs from 'fs'; import path from 'path';
import { pdfPages, slidesHtml, themeCss } from './carousel_lib.mjs';
import { loadTheme } from './theme_lib.mjs';

const [specFile, outFile] = process.argv.slice(2);
if (!specFile || !outFile) { console.error('usage: node gfx/carousel.mjs <linkedin.json> <out.pdf>'); process.exit(2); }
const GFX = path.dirname(new URL(import.meta.url).pathname);
const fail = (msg) => { console.error(`FAILED carousel ${specFile}: ${msg}`); process.exit(1); };
let spec, html;
try {
  const rules = JSON.parse(fs.readFileSync(path.join(GFX, '..', 'style', 'linkedin.json'), 'utf8'));
  spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  const body = slidesHtml(spec?.carousel?.slides, rules.author, path.dirname(path.resolve(specFile)));
  html = fs.readFileSync(path.join(GFX, 'carousel.html'), 'utf8')
    .replace('</style>', () => `${themeCss(loadTheme(specFile))}</style>`).replace('<body></body>', () => `<body>${body}</body>`);  // functions: a "$&" in slide text stays text
} catch (e) { fail(e.message); }

const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
try {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  // file:// base so the cover photo (file URL) and the font load; the HTML itself is ours
  const tmp = `${outFile}.html`; fs.writeFileSync(tmp, html);
  try { await page.goto(`file://${path.resolve(tmp)}`, { waitUntil: 'load', timeout: 30000 }); } finally { fs.rmSync(tmp, { force: true }); }
  await page.evaluate(() => document.fonts.ready);
  const broken = await page.evaluate(() => [...document.querySelectorAll('.slide')].flatMap((s, i) => {
    const box = s.querySelector('.box'), img = s.querySelector('img');
    const tooTall = box.scrollHeight > box.clientHeight + 1, tooWide = box.scrollWidth > box.clientWidth + 1;  // a long word clips sideways
    return [...(tooTall || tooWide ? [`slide ${i + 1}: text does not fit (shorten it${tooWide ? ', a word is wider than the slide' : ''})`] : []),
            ...(img && !img.naturalWidth ? [`slide ${i + 1}: photo did not load`] : [])];
  }));
  if (broken.length) throw new Error(broken.join('; '));
  const part = `${outFile}.part`;
  await page.pdf({ path: part, width: '1080px', height: '1350px', printBackground: true, preferCSSPageSize: true });
  const got = pdfPages(fs.readFileSync(part)), want = spec.carousel.slides.length;
  if (got.pages !== want) { fs.rmSync(part, { force: true }); throw new Error(`PDF has ${got.pages} pages, the spec ${want} slides`); }
  fs.renameSync(part, outFile);  // a cut-off render never leaves a PDF under the real name
  console.log(`${outFile}: ${got.pages} pages ${got.width}x${got.height} pt`);
} catch (e) {
  console.error(`FAILED carousel ${specFile}: ${e.message}`); process.exitCode = 1;
} finally { await browser.close(); }
