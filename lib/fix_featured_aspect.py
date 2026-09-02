"""Patch a block-template's featured-image aspect ratio.

  python3 fix_featured_aspect.py <template id> <ratio|auto> [--apply]

The Single Posts template hard-codes {"aspectRatio":"16/9"} on the
post-featured-image block, which crops a taller photo top and bottom no matter
what global styles say. Block attributes win over global styles, so the fix has
to happen here.

Read-only without --apply.
"""

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request

SITE = "207097055"
KEYCHAIN = "dunamispub-adventuresinepsilon"
BASE = "https://public-api.wordpress.com/wp/v2/sites/%s/templates" % SITE

template_id = sys.argv[1]
ratio = sys.argv[2]
apply_it = "--apply" in sys.argv

token = subprocess.run(
    ["security", "find-generic-password", "-s", KEYCHAIN, "-w"],
    capture_output=True, text=True, check=True).stdout.strip()
auth = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
url = "%s/%s" % (BASE, urllib.parse.quote(template_id, safe=""))

req = urllib.request.Request(url + "?context=edit", headers=auth)
with urllib.request.urlopen(req, timeout=60) as r:
    tpl = json.load(r)

content = tpl["content"]["raw"]
found = re.findall(r"<!-- wp:post-featured-image([^>]*)/-->", content)
print("post-featured-image blocks found: %d" % len(found))
for f in found:
    print("  current attrs:%s" % (f.strip() or " (none)"))

new = re.sub(
    r"<!-- wp:post-featured-image[^>]*/-->",
    '<!-- wp:post-featured-image {"aspectRatio":"%s"} /-->' % ratio,
    content)

if new == content:
    print("Nothing to change.")
    sys.exit(0)

print("  -> aspectRatio:%s" % ratio)

if apply_it:
    body = json.dumps({"content": new}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=auth)
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    print("Updated template %s" % out["id"])
else:
    print("Dry run. Add --apply to write it.")
