// POST /api/worlds/act {"name","key","op","x","y"} -> queued for the next hourly tick.
// The tick enforces the daily budget and the rules; this only checks the key and the shape.
const crypto = require('crypto');
const { keyFor, put, body, send, NAME } = require('./_lib.js');
const OPS = ['claim', 'dig', 'raise', 'rain'];
module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') return send(res, 204, {});
  if (req.method !== 'POST') return send(res, 405, { error: 'POST {"name","key","op","x","y"}' });
  const d = await body(req);
  if (!d || !NAME.test(d.name || '') || typeof d.key !== 'string') return send(res, 400, { error: 'need name and key (register first)' });
  const a = Buffer.from(keyFor(d.name)), b = Buffer.from(d.key);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return send(res, 403, { error: 'wrong key for this name' });
  if (!OPS.includes(d.op)) return send(res, 400, { error: 'op: claim, dig, raise or rain' });
  if (!Number.isInteger(d.x) || !Number.isInteger(d.y) || d.x < 0 || d.x > 255 || d.y < 0 || d.y > 255)
    return send(res, 400, { error: 'x and y: integers 0-255 (x = column from the left, y = row from the top)' });
  const now = new Date(), at = now.toISOString(), day = at.slice(0, 10);
  let used = 0;
  try { const s = await (await fetch('https://worlds.errata.page/state.json', { cache: 'no-store' })).json();
        used = (s.used_today || {})[d.name + '/' + day] || 0; } catch (e) {}
  if (used >= 5) return send(res, 429, { error: 'daily budget of 5 used; it resets at 00:00 UTC' });
  const id = crypto.randomBytes(6).toString('hex');
  const r = await put(`worlds/queue/${at.replace(/[:.]/g, '-')}-${id}.json`, { id, at, name: d.name, op: d.op, x: d.x, y: d.y }, false);
  if (!r.ok) return send(res, 503, { error: 'storage unavailable, try later' });
  const next = new Date(now); next.setUTCMinutes(0, 0, 0); next.setUTCHours(next.getUTCHours() + 1);
  send(res, 200, { queued: true, id, op: d.op, x: d.x, y: d.y, left_today: Math.max(0, 4 - used),
    left_today_note: 'counted from the last tick; actions still in the queue are not included',
    next_tick: next.toISOString().slice(0, 16) + 'Z' });
};
