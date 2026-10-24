// node pip_assets.mjs SIZE -> gfx/pip_mask.png (white rounded rect on black), gfx/pip_frame.png (shadow + accent border, transparent)
// node pip_assets.mjs SIZE #RRGGBB NAME -> only gfx/pip_frame_NAME_RRGGBB.png in that accent (a project theme, style/themes/NAME.json;
// the accent in the file name: themes.pip_frame() asks for a new frame after an edit of --acc)
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
const S = Number(process.argv[2] || 600), R = Math.round(S * 0.08), PAD = 40;
const [ACC = '#2de2c4', NAME] = process.argv.slice(3);
if (!/^#[0-9a-fA-F]{6}$/.test(ACC) || (NAME !== undefined && !/^[a-z0-9-]{1,40}$/.test(NAME))) throw new Error(`usage: pip_assets.mjs SIZE [#RRGGBB NAME], got ${ACC} ${NAME}`);
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome' });
const p = await b.newPage({ viewport: { width: S, height: S } });
await p.setContent(`<html><body style="margin:0;background:#000"><div style="width:${S}px;height:${S}px;background:#fff;border-radius:${R}px"></div></body></html>`);
if (!NAME) await p.screenshot({ path: '/home/kamil-jan/video-pipeline/gfx/pip_mask.png' });
const q = await b.newPage({ viewport: { width: S + 2 * PAD, height: S + 2 * PAD } });
await q.setContent(`<html><body style="margin:0;background:transparent"><div style="position:absolute;left:${PAD - 6}px;top:${PAD - 6}px;width:${S + 12}px;height:${S + 12}px;border-radius:${R + 6}px;background:${ACC};box-shadow:0 14px 40px rgba(0,0,0,.55)"></div></body></html>`);
await q.screenshot({ path: `/home/kamil-jan/video-pipeline/gfx/pip_frame${NAME ? `_${NAME}_${ACC.slice(1).toUpperCase()}` : ''}.png`, omitBackground: true });
await b.close(); console.log('pip assets', S);
