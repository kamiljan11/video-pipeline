// How many browser pages render cards at once, and a screenshot that waits out a busy machine (night 2026-11-09/10:
// 6 pages under load ~40 from another job hit page.screenshot's 30 s timeout on every try; each card alone rendered fine).
// Not in any card's key: changing this file renders nothing again (stills stay accepted).
export const PAGES_MAX = 6;
export const PAGES_CAP = 16;  // GFX_PAGES above this is refused: every page is a 2560x1440 chromium tab (memory)
export const SHOT_TIMEOUTS = [30000, 90000, 240000];  // ms per try: a busy machine gets longer waits, not the same one again

// pages = free cores / 4 (one page = chromium compositor + ffmpeg later), 1..PAGES_MAX; GFX_PAGES=<n> overrides
export function pageCount(cpus, load1, env = '') {
  if (env !== '' && env !== undefined) {
    const n = Number(env);
    if (!Number.isInteger(n) || n < 1 || n > PAGES_CAP) throw new Error(`GFX_PAGES=${env}: want a whole number 1-${PAGES_CAP}`);
    return n;
  }
  return Math.max(1, Math.min(PAGES_MAX, Math.floor((cpus - load1) / 4)));
}

const isTimeout = e => e?.name === 'TimeoutError' || /Timeout \d+ms exceeded/.test(String(e?.message));

// page.screenshot with longer waits on a timeout; any other error, or the last timeout, is thrown with the card id
export async function shot(page, opts, id, log = console.error, waits = SHOT_TIMEOUTS) {
  for (let i = 0; i < waits.length; i++) {
    try { return await page.screenshot({ ...opts, timeout: waits[i] }); }
    catch (e) {
      if (!isTimeout(e) || i === waits.length - 1) throw new Error(`${id}: screenshot ${e.message}`);
      log(`slow gfx ${id}: screenshot over ${waits[i] / 1000} s (machine busy), waiting ${waits[i + 1] / 1000} s`);
    }
  }
}
