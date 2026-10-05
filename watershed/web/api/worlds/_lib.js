// Shared bits for the Watershed API. Queue = one Blob file per action (one put per action: the free
// tier allows 2,000 writes a month); the hourly tick on errata's server reads, applies and deletes them.
const crypto = require('crypto');
const SECRET = process.env.WORLD_SECRET || 'unset';
const keyFor = name => crypto.createHmac('sha256', SECRET).update('watershed:' + name).digest('hex').slice(0, 24);
async function put(path, rec, overwrite) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return { ok: false, status: 500 };
  // API v11 + ?pathname=: refuses to overwrite unless asked (v7 silently overwrote, probed 2026-10-05)
  const r = await fetch('https://blob.vercel-storage.com/?pathname=' + path, {
    method: 'PUT', body: JSON.stringify(rec),
    headers: { authorization: 'Bearer ' + token, 'x-api-version': '11', 'x-content-type': 'application/json',
               'x-add-random-suffix': '0', ...(overwrite ? { 'x-allow-overwrite': '1' } : {}) } });
  const t = r.ok ? '' : await r.text();
  return { ok: r.ok, status: r.status, exists: /already exists/.test(t) };
}
async function body(req) {
  let s = ''; for await (const c of req) { s += c; if (s.length > 2000) break; }
  try { return JSON.parse(s); } catch (e) { return null; }
}
function send(res, code, obj) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'content-type');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(obj, null, 1));
}
const NAME = /^[a-z0-9-]{3,24}$/;
module.exports = { keyFor, put, body, send, NAME };
