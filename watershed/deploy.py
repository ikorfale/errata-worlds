#!/usr/bin/env python3
"""Deploy the Watershed site (worlds.errata.page, Vercel project errata-worlds): page + API + the latest tick.
Uploads by digest, only files Vercel does not have yet. Key from ~/.config/agent-accounts/vercel.key, never printed."""
import os, json, hashlib, urllib.request, urllib.error, time, sys
KEY = open(os.path.expanduser('~/.config/agent-accounts/vercel.key')).read().strip()
TEAM = 'gerundiums-projects'; HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.expanduser('~/errata-site/worlds/index.html')
def req(url, data=None, method=None, raw=False, hdr=None):
    h = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json', **(hdr or {})}
    r = urllib.request.Request(url, data, h, method=method)
    return json.load(urllib.request.urlopen(r, timeout=120))
files = {}
def add(rel, raw): files[rel] = raw
for root in ('web', 'site'):
    base = os.path.join(HERE, root)
    for d, _, fs in os.walk(base):
        for f in fs:
            p = os.path.join(d, f); add(os.path.relpath(p, base), open(p, 'rb').read())
add('index.html', open(PAGE, 'rb').read())
add('robots.txt', b'User-agent: *\nAllow: /\nSitemap: https://worlds.errata.page/sitemap.xml\n')
add('sitemap.xml', ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    f'<url><loc>https://worlds.errata.page/</loc><lastmod>{time.strftime("%Y-%m-%d")}</lastmod></url></urlset>\n').encode())
cache = os.path.join(HERE, 'state', 'uploaded.txt'); have = set(open(cache).read().split()) if os.path.exists(cache) else set()
meta = []
for rel, raw in files.items():
    sha = hashlib.sha1(raw).hexdigest()
    if sha not in have:
        r = urllib.request.Request(f'https://api.vercel.com/v2/files?slug={TEAM}', raw,
            {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/octet-stream', 'x-vercel-digest': sha})
        urllib.request.urlopen(r, timeout=120).read(); have.add(sha)
    meta.append({'file': rel, 'sha': sha, 'size': len(raw)})
open(cache, 'w').write('\n'.join(sorted(have)))
body = json.dumps({'name': 'errata-worlds', 'project': 'errata-worlds', 'target': 'production', 'files': meta,
                   'projectSettings': {'framework': None}}).encode()
try: d = req(f'https://api.vercel.com/v13/deployments?slug={TEAM}', body)
except urllib.error.HTTPError as e:
    if e.code == 400 and b'missing_files' in (b := e.read()):  # digest cache went stale: forget it and retry once
        os.remove(cache); os.execv(sys.executable, [sys.executable] + sys.argv)
    raise
for _ in range(45):
    s = req(f"https://api.vercel.com/v13/deployments/{d['id']}?slug={TEAM}")
    if s.get('readyState') in ('READY', 'ERROR', 'CANCELED'): break
    time.sleep(4)
print(s.get('readyState'), len(meta), 'files')
