// helpers every card writer shares (render.mjs, scene_check.mjs, thumbs.mjs): one escape and one icon reader, so a card is
// laid out the same in the check as in the render
import fs from 'fs'; import path from 'path';

const ICONS = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'node_modules', 'lucide-static', 'icons');

// text into HTML, also inside a "quoted" attribute
export const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
// Polish typography: a one-letter word, a short preposition or "nie" never ends a line (2026-11-08: "BEZ" alone on the blog cover)
const GLUE = /(?<=^|\s)(a|i|o|u|w|z|od|do|na|po|za|we|ze|ku|bez|dla|nad|pod|nie)\s+/giu;
export const keepTogether = (t) => String(t ?? '').replace(GLUE, '$1\u00a0').replace(/\s+([^\s.,!?:;\u2026"\u201d]{1,3}[.,!?:;\u2026"\u201d]*)$/u, '\u00a0$1');  // a final "tak." counts 3 letters
// escaped text with keepTogether: every headline, line or label a viewer reads
export const prose = (t) => esc(keepTogether(t));
// a lucide icon as inline SVG ('' for none); a missing name throws (the caller names the card). Only a lucide name
// (a-z, 0-9, -): a path like "../x" would read any .svg on the disk into the card (pg-review 2026-11-08 security-1)
export const ICON_NAME = /^[a-z0-9-]+$/;
export const icon = n => {
  if (!n) return '';
  if (!(typeof n === 'string' && ICON_NAME.test(n))) throw new Error(`icon = a lucide name (a-z, 0-9, -), got ${JSON.stringify(n)}`);
  return fs.readFileSync(path.join(ICONS, `${n}.svg`), 'utf8').replace(/<!--[\s\S]*?-->/g, '');
};
