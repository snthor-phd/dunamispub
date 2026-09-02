"""Resize the section headings on a WordPress page so they sit below the page
title instead of towering over it.

  python3 resize_headings.py <page id> <h2 size> <h3 size> [--apply]

Without --apply it reports what it would change. Read-only by default.
"""

import json
import re
import subprocess
import sys
import urllib.request

SITE = "207097055"
KEYCHAIN = "dunamispub-adventuresinepsilon"
BASE = "https://public-api.wordpress.com/wp/v2/sites/%s" % SITE

page_id = sys.argv[1]
h2_size = sys.argv[2]
h3_size = sys.argv[3]
apply_it = "--apply" in sys.argv

token = subprocess.run(
    ["security", "find-generic-password", "-s", KEYCHAIN, "-w"],
    capture_output=True, text=True, check=True).stdout.strip()


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


page = call("GET", "/pages/%s?context=edit" % page_id)
content = page["content"]["raw"]

BLOCK = re.compile(
    r"<!-- wp:heading( \{.*?\})? -->\s*(<h([23])([^>]*)>)(.*?)(</h[23]>)\s*<!-- /wp:heading -->",
    re.S)

changed = []


def fix(m):
    attrs = json.loads(m.group(1)) if m.group(1) else {}
    level = int(m.group(3))
    size = h3_size if level == 3 else h2_size
    text = re.sub(r"<[^>]+>", "", m.group(5)).strip()

    attrs.setdefault("style", {}).setdefault("typography", {})["fontSize"] = size
    if level == 3:
        attrs["level"] = 3

    open_attrs = re.sub(r'\s*style="[^"]*"', "", m.group(4))
    if "wp-block-heading" not in open_attrs:
        open_attrs += ' class="wp-block-heading"'

    changed.append("h%d  %-32s -> %s" % (level, text[:32], size))
    return ("<!-- wp:heading %s -->\n<h%d%s style=\"font-size:%s\">%s</h%d>\n<!-- /wp:heading -->"
            % (json.dumps(attrs, separators=(",", ":")), level, open_attrs,
               size, m.group(5), level))


new_content = BLOCK.sub(fix, content)

for line in changed:
    print(line)
print("\n%d headings, %d chars -> %d chars" % (len(changed), len(content), len(new_content)))

if apply_it:
    out = call("POST", "/pages/%s" % page_id, {"content": new_content})
    print("Updated. status: %s  link: %s" % (out["status"], out["link"]))
else:
    print("Dry run. Add --apply to write it.")
