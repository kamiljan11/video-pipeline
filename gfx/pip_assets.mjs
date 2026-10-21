// node pip_assets.mjs SIZE -> gfx/pip_mask.png (white rounded rect on black), gfx/pip_frame.png (shadow + accent border, transparent)
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
const S = Number(process.argv[2] || 600), R = Math.round(S * 0.08), PAD = 40;
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome' });
const p = await b.newPage({ viewport: { width: S, height: S } });
await p.setContent(`<html><body style="margin:0;background:#000"><div style="width:${S}px;height:${S}px;background:#fff;border-radius:${R}px"></div></body></html>`);
await p.screenshot({ path: '/home/kamil-jan/video-pipeline/gfx/pip_mask.png' });
const q = await b.newPage({ viewport: { width: S + 2 * PAD, height: S + 2 * PAD } });
await q.setContent(`<html><body style="margin:0;background:transparent"><div style="position:absolute;left:${PAD - 6}px;top:${PAD - 6}px;width:${S + 12}px;height:${S + 12}px;border-radius:${R + 6}px;background:#2de2c4;box-shadow:0 14px 40px rgba(0,0,0,.55)"></div></body></html>`);
await q.screenshot({ path: '/home/kamil-jan/video-pipeline/gfx/pip_frame.png', omitBackground: true });
await b.close(); console.log('pip assets', S);
