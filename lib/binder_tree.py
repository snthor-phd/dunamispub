"""Print a Scrivener binder as an indented tree with body and synopsis word counts.

Usage:  python3 binder_tree.py "/path/to/Project.scriv" [subtree title]

Read-only. Never writes to the project.
"""

import sys, os, re, xml.etree.ElementTree as ET

p = sys.argv[1]
want = sys.argv[2].lower() if len(sys.argv) > 2 else None
sx = [f for f in os.listdir(p) if f.endswith(".scrivx")][0]
tree = ET.parse(os.path.join(p, sx))


def counts(uid):
    d = os.path.join(p, "Files", "Data", uid)
    body = syn = 0
    rtf = os.path.join(d, "content.rtf")
    if os.path.exists(rtf):
        raw = open(rtf, encoding="utf-8", errors="replace").read()
        body = len(re.sub(r"\\[a-z]+-?[0-9]* ?|[{}]", "", raw).split())
    st = os.path.join(d, "synopsis.txt")
    if os.path.exists(st):
        syn = len(open(st, encoding="utf-8", errors="replace").read().split())
    return body, syn


def walk(node, depth, printing):
    for item in node.findall("BinderItem"):
        title = (item.findtext("Title") or "").strip()
        uid = item.get("UUID")
        body, syn = counts(uid)
        show = printing or (want and want in title.lower())
        if show:
            bits = []
            if body:
                bits.append("%d words" % body)
            if syn:
                bits.append("synopsis %d" % syn)
            tag = ("  [%s]" % ", ".join(bits)) if bits else "  [empty]"
            print("%s%s%s" % ("    " * depth, title, tag))
        ch = item.find("Children")
        if ch is not None:
            walk(ch, depth + 1 if show else depth, show)


walk(tree.getroot().find("Binder"), 0, want is None)
