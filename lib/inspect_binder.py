import sys, os, re, xml.etree.ElementTree as ET

p = sys.argv[1]
sx = [f for f in os.listdir(p) if f.endswith(".scrivx")][0]
tree = ET.parse(os.path.join(p, sx))
sep = " / "

def wordcount(uid):
    rtf = os.path.join(p, "Files", "Data", uid, "content.rtf")
    if not os.path.exists(rtf):
        return 0, None
    raw = open(rtf, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"\\[a-z]+-?[0-9]* ?|[{}]", "", raw)
    return len(txt.split()), rtf

def walk(node, path):
    for item in node.findall("BinderItem"):
        title = (item.findtext("Title") or "").strip()
        uid = item.get("UUID")
        kind = item.get("Type")
        here = path + [title]
        n, rtf = wordcount(uid)
        low = title.lower()
        if "rebuild" in low or "recovered" in low or n > 500:
            loc = sep.join(here)
            print("%6d words | %-12s | %s" % (n, kind, loc))
            if rtf and ("rebuild" in low or "recovered" in low):
                print("        uuid: %s" % uid)
                print("        path: %s" % rtf)
        ch = item.find("Children")
        if ch is not None:
            walk(ch, here)

walk(tree.getroot().find("Binder"), [])
