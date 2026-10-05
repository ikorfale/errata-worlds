// POST /api/worlds/register {"name": "your-name"} -> {"name", "key"}. Names are first come, first served.
// The key is HMAC(secret, name): nothing secret is stored, the Blob file only reserves the name.
const { keyFor, put, body, send, NAME } = require('./_lib.js');
module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') return send(res, 204, {});
  if (req.method !== 'POST') return send(res, 405, { error: 'POST {"name": "..."}' });
  const d = await body(req);
  const name = d && typeof d.name === 'string' ? d.name.trim().toLowerCase() : '';
  if (!NAME.test(name)) return send(res, 400, { error: 'name: 3-24 characters of a-z, 0-9 and -' });
  const r = await put('worlds/players/' + name + '.json', { name, at: new Date().toISOString() }, false);
  if (!r.ok) return send(res, r.exists ? 409 : 503, { error: r.exists ? 'name taken' : 'storage unavailable, try later' });
  send(res, 200, { name, key: keyFor(name), note: 'Keep the key: it is shown once. 5 actions per UTC day; ticks on the hour.',
    act: 'POST /api/worlds/act {"name","key","op":"claim|dig|raise|rain","x":0-255,"y":0-255}' });
};
