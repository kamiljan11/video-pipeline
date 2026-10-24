// Project theme: work/theme.json {"theme": "<name>"} picks style/themes/<name>.json, whose "css" tokens override the
// colors of gfx/template.html (:root). No theme.json = the template's own colors. Same rules as themes.py (Python side).
import crypto from 'crypto'; import fs from 'fs'; import path from 'path';

export const THEMES = new URL('../style/themes/', import.meta.url).pathname;
const NAME = /^[a-z0-9-]{1,40}$/, VAR = /^--[a-z0-9-]{1,40}$/, VAL = /^[#a-zA-Z0-9(),.%\s-]{1,80}$/;

// a JSON object, or a named error (not a bare SyntaxError / destructuring TypeError)
function readObject(f, raw = fs.readFileSync(f, 'utf8')) {
  let v;
  try { v = JSON.parse(raw); } catch (e) { throw new Error(`${f}: not valid JSON (${e.message})`); }
  if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error(`${f}: expected a JSON object`);
  return v;
}

// -> null without work/theme.json, else {name, css, key}; key changes with the theme file, so every card is rendered again
export function loadTheme(specFile, dir = THEMES) {
  const f = path.join(path.dirname(specFile), 'theme.json');
  if (!fs.existsSync(f)) return null;
  const { theme } = readObject(f);
  if (typeof theme !== 'string' || !NAME.test(theme)) throw new Error(`${f}: "theme" must be a name like "cetus", got ${JSON.stringify(theme)}`);
  const src = path.join(dir, `${theme}.json`);
  if (!fs.existsSync(src)) throw new Error(`${f}: no theme "${theme}" (style/themes/${theme}.json)`);
  const raw = fs.readFileSync(src, 'utf8'), { css } = readObject(src, raw);
  if (!css || typeof css !== 'object' || Array.isArray(css)) throw new Error(`style/themes/${theme}.json: "css" must be an object of tokens`);
  for (const [k, v] of Object.entries(css)) {
    if (!VAR.test(k) || typeof v !== 'string' || !VAL.test(v)) throw new Error(`style/themes/${theme}.json: bad token ${k}: ${JSON.stringify(v)}`);
  }
  return { name: theme, css, key: `theme:${theme}:${crypto.createHash('sha256').update(raw).digest('hex').slice(0, 16)}` };
}
