// helpers every card writer shares (render.mjs, scene_check.mjs, thumbs.mjs): one escape and one icon reader, so a card is
// laid out the same in the check as in the render
import fs from 'fs'; import path from 'path';

const ICONS = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'node_modules', 'lucide-static', 'icons');

// text into HTML, also inside a "quoted" attribute
export const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
// a lucide icon as inline SVG ('' for none); a missing name throws (the caller names the card)
export const icon = n => (n ? fs.readFileSync(path.join(ICONS, `${n}.svg`), 'utf8').replace(/<!--[\s\S]*?-->/g, '') : '');
