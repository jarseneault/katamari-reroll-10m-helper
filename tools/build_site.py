#!/usr/bin/env python3
"""Inline data/northstar-objects.json into index.html (between the DATA markers)."""
import base64, hashlib, json, pathlib, re

root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root / "data/northstar-objects.json").read_text())
rows = [[o["name"], o["ja"], o["size"], o["volume"], o["placed"], o["gain"], o["catchCm"]] for o in data["objects"]]
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
html = (root / "index.html").read_text()
html, n = re.subn(r"(/\*DATA\*/).*?(/\*END\*/)", lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
assert n == 1, "DATA markers not found"
# Pin the inline script by hash so the page runs no other script.
script = re.search(r"<script>(.*?)</script>", html, flags=re.S).group(1)
digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
csp = ("default-src 'none'; script-src 'sha256-%s'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; base-uri 'none'; form-action 'none'" % digest)
html, n = re.subn(r'(<meta http-equiv="Content-Security-Policy" content=")[^"]*(")', lambda m: m.group(1) + csp + m.group(2), html)
assert n == 1, "CSP meta not found"
(root / "index.html").write_text(html)
print(f"inlined {len(rows)} objects")
