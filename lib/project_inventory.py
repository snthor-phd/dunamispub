"""Inventory Scrivener projects: correct total word counts, doc counts, last edit.

Usage:  python3 project_inventory.py <root> [name filter]

Read-only. Sums every content.rtf in the package individually — batching them
through one textutil call silently drops files and undercounts.
"""

import sys, os, re

root = os.path.expanduser(sys.argv[1])
needle = sys.argv[2].lower() if len(sys.argv) > 2 else None
rows = []

for dirpath, dirnames, _ in os.walk(root):
    for d in list(dirnames):
        if not d.endswith(".scriv"):
            continue
        dirnames.remove(d)
        proj = os.path.join(dirpath, d)
        if needle and needle not in d.lower():
            continue
        data = os.path.join(proj, "Files", "Data")
        total = docs = 0
        newest = 0.0
        for sub, _, files in os.walk(data):
            for f in files:
                if f != "content.rtf":
                    continue
                fp = os.path.join(sub, f)
                raw = open(fp, encoding="utf-8", errors="replace").read()
                n = len(re.sub(r"\\[a-z]+-?[0-9]* ?|[{}]", "", raw).split())
                if n:
                    docs += 1
                total += n
                newest = max(newest, os.path.getmtime(fp))
        if not newest:
            newest = os.path.getmtime(proj)
        size = sum(
            os.path.getsize(os.path.join(s, f))
            for s, _, fs in os.walk(proj) for f in fs
        )
        rows.append((total, docs, newest, size, proj))

import datetime
for total, docs, newest, size, proj in sorted(rows, reverse=True):
    when = datetime.datetime.fromtimestamp(newest).strftime("%Y-%m-%d")
    print("%7d words | %3d docs | %s | %6.1f MB | %s"
          % (total, docs, when, size / 1e6, proj.replace(os.path.expanduser("~"), "~")))
print("\n%d projects" % len(rows))
