// a scene with every kind that has its own timings (motion.test.mjs; the legacy golden hash is taken on it)
export const ALL = {
  id: 'm1', type: 'scene', dur: 8, els: [
    { k: 'file', id: 'f', x: 0, y: 0, name: 'a.md', rows: [{ t: 'x', mark: 'ok', hl: true }, '~60'], badge: { text: 'nowy' } },
    { k: 'term', id: 't', x: 0, y: 400, cmd: 'ls', out: ['a', 'b'], hl: [1], gone: 6 },
    { k: 'chat', id: 'c', x: 900, y: 0, msgs: [{ who: 'me', t: 'hej' }, { t: '~50' }] },
    { k: 'check', id: 'k', x: 900, y: 500, at: 1 },
    { k: 'ring', x: 0, y: 0, w: 300, h: 200, at: 2, gone: 5 },
    { k: 'say', id: 's', x: 0, y: 800, words: [['to', 1], ['~nie~', 1.4]] },
    { k: 'toggle', id: 'g', x: 900, y: 800, at: 2, text: 'on', out_at: 7 },
    { k: 'line', from: [0, 0], to: [400, 300], at: 1, packet_at: 2 },
    { k: 'chip', id: 'p', x: 1400, y: 0, text: 'x', at: 3, strike_at: 4, anim: 'fade' },
  ],
};
