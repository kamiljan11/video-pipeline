// node --test gfx/test/*.test.mjs   (motion_tokens.mjs: frames at 30 fps, curves by role, the motion lint; scene "motion": "tokens")
import test from 'node:test';
import crypto from 'crypto';
import assert from 'node:assert/strict';
import { EASE, F, FPS, STAGGER, STAGGER_MAX, easesBothWays, motionProblems, sec, staggerProblems } from '../motion_tokens.mjs';
import { checkScene, scene } from '../scene_lib.mjs';
import { motionLint } from '../scene_check.mjs';
import { ALL } from './motion_fixture.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;

test('tokens are frames at 30 fps, turned into seconds that land on a frame', () => {
  assert.equal(FPS, 30);
  assert.deepEqual([F.tick, F.micro, F.fast, F.base, F.slow], [2, 4, 6, 12, 24]);
  assert.equal(sec(F.base), 0.4);
  assert.equal(sec(F.fast), 0.2);
  assert.ok(Object.values(STAGGER).every(f => f <= STAGGER_MAX));
  assert.equal(Object.keys(EASE).length, 4);
  assert.equal(Object.keys(STAGGER).length, 5);
});

test('a curve that eases both ways is told apart from land, pop and the old entrances', () => {
  for (const tf of ['ease-in-out', 'cubic-bezier(.45,0,.55,1)', 'cubic-bezier(.65,0,.35,1)', EASE.shift]) assert.ok(easesBothWays(tf), tf);
  for (const tf of [EASE.land, EASE.pop, EASE.leave, 'ease-out', 'ease', 'cubic-bezier(.215,.61,.355,1)', 'cubic-bezier(.2,1.6,.4,1)', 'cubic-bezier(.4,0,.2,1)'])
    assert.ok(!easesBothWays(tf), tf);
});

test('the lint names an ease-in-out entrance once per curve, and leaves moves and loops alone', () => {
  const html = '<i style="animation:scdraw .28s cubic-bezier(.45,0,.55,1) 1.00s forwards"></i><i style="animation:scdraw .2s cubic-bezier(.45,0,.55,1) 2s forwards"></i>'
    + '<i style="animation:scfade .2s 1s both,sccur .7s cubic-bezier(.45,0,.55,1) 2s both"></i><style>.b{animation:scb1 17s ease-in-out infinite alternate}</style>';
  assert.deepEqual(motionProblems(html), ['entrance eases both ways: scdraw cubic-bezier(.45,0,.55,1) (2x); use land or pop']);
});

test('a card without "motion" is drawn byte for byte as before tokens (golden: sha1 of the fixture with scene_lib.mjs at 5cd9d32)', () => {
  assert.equal(crypto.createHash('sha1').update(scene(ALL, esc, icon)).digest('hex'), '6e28193a0cfc7d93754f54cd43baa49295089c3f');
});

test('a card without "motion" keeps the old timings (and the old check draw eases both ways); "tokens" passes the lint', () => {
  const old = scene(ALL, esc, icon), tok = scene({ ...ALL, motion: 'tokens' }, esc, icon);
  assert.match(old, /scpop \.5s cubic-bezier\(\.2,1\.4,\.4,1\)|scup \.55s cubic-bezier\(\.2,\.9,\.2,1\)/);
  assert.ok(motionProblems(old).length > 0, 'the old check/ring/toggle draw is ease-in-out');
  assert.deepEqual(motionProblems(tok), []);
  assert.ok(!/undefined/.test(tok) && !/undefined/.test(old), 'every timing is filled in');
  assert.match(tok, new RegExp(`scup 0\\.4s ${EASE.land.replace(/[().]/g, '\\$&')}`));
  assert.match(tok, new RegExp(`scgone 0\\.2s|scfadeout 0\\.2s ${EASE.leave.replace(/[().]/g, '\\$&')}`));  // exit = half the entrance
  assert.deepEqual(motionLint({ ...ALL, motion: 'tokens' }), []);
  assert.deepEqual(motionLint(ALL), []);  // not linted: finished films are not failed after the fact
});

test('rows and terminal lines in "tokens" come in one stagger step apart (5 and 3 frames)', () => {
  const tok = scene({ ...ALL, motion: 'tokens' }, esc, icon);
  const delays = [...tok.matchAll(/class="ol[^"]*" style="animation:scfade [^ ]+ [^ ]+ ([\d.]+)s/g)].map(m => +m[1]);
  assert.equal(delays.length, 2);
  assert.ok(Math.abs(delays[1] - delays[0] - sec(STAGGER.word)) < 0.011, String(delays));
});

test('"motion" other than "tokens" is named; a stagger step over 12 frames is named with its fix', () => {
  assert.ok(checkScene({ ...ALL, motion: 'snappy' }).some(b => b.includes('"motion" = "tokens"')));
  const slow = { ...ALL, motion: 'tokens', els: [{ k: 'chat', id: 'c', x: 0, y: 0, step: 0.5, msgs: [{ t: 'a' }, { t: 'b' }] }] };
  assert.deepEqual(staggerProblems(slow), ['m1: c "step" 0.5s = 15 frames (stagger max 12); give the items their own "at" when they follow speech']);
  assert.equal(motionLint(slow).length, 1);
});
