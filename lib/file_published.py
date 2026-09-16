"""File a published document under Published/<destination>/<year>.

  python3 lib/file_published.py <project.scriv> <uuid> <destination> [year] [--apply]

The step-7 writer. GUARDED like add_binder_doc:
  · refuses while Scrivener holds the project (Files/user.lock present)
  · refuses unless Files/version.txt matches EXPECTED_VERSION
  · takes a timestamped .scrivx backup first
  · re-parses afterward and restores the backup on any failure

The move is text surgery: the document's <BinderItem> block is cut and pasted
byte-for-byte into the target folder's <Children>. Nothing else in the file is
re-serialised, so Scrivener sees exactly what it wrote, minus one move.

Pending moves (queued while Scrivener was open) live in PENDING and are retried
by the watcher each time it runs with the project closed.
"""

import json
import os
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET

EXPECTED_VERSION = "23"
PENDING = os.path.expanduser(
    "~/Library/Application Support/DunamisPub/pending_filing.json")

TAG = re.compile(r"<(/?)BinderItem\b[^>]*?(/?)>")


def _item_span(text, start):
    """End offset of the <BinderItem> element that opens at `start`."""
    depth = 0
    for m in TAG.finditer(text, start):
        closing, selfclose = m.group(1), m.group(2)
        if selfclose:
            if depth == 0:
                return m.end()
            continue
        depth += -1 if closing else 1
        if depth == 0:
            return m.end()
    raise ValueError("unbalanced BinderItem")


def _open_tag(text, uuid):
    m = re.search(r'<BinderItem\b[^>]*\bUUID="%s"[^>]*>' % re.escape(uuid), text)
    return m.start() if m else None


def _uuid_of(item):
    return item.get("UUID")


def _target_uuid(root, dest, year):
    """UUID of Published/<dest>/<year>, or None."""
    def child(node, title):
        kids = node.find("Children") if node.tag == "BinderItem" else node
        if kids is None:
            return None
        for it in kids.findall("BinderItem"):
            if (it.findtext("Title") or "").strip().lower() == title.lower():
                return it
        return None
    binder = root.find("Binder")
    # Published may sit at top level or under the draft folder
    pub = None
    for it in binder.iter("BinderItem"):
        if (it.findtext("Title") or "").strip().lower() == "published":
            pub = it
            break
    if pub is None:
        return None
    d = child(pub, dest)
    y = child(d, str(year)) if d is not None else None
    return _uuid_of(y) if y is not None else None


def move(project, uuid, dest, year, apply_it=False):
    """Returns (ok, message)."""
    project = os.path.expanduser(project)
    if os.path.exists(os.path.join(project, "Files", "user.lock")):
        return False, "Scrivener has the project open"
    version = open(os.path.join(project, "Files", "version.txt")).read().strip()
    if version != EXPECTED_VERSION:
        return False, "format %s, expected %s" % (version, EXPECTED_VERSION)

    scrivx = os.path.join(project, [f for f in os.listdir(project)
                                    if f.endswith(".scrivx")][0])
    text = open(scrivx, encoding="utf-8").read()
    target = _target_uuid(ET.fromstring(text), dest, year)
    if target is None:
        return False, "no Published/%s/%s folder" % (dest, year)
    if target == uuid:
        return False, "target is the document itself"

    s = _open_tag(text, uuid)
    if s is None:
        return False, "document %s not in binder" % uuid
    e = _item_span(text, s)
    # take the whole line(s) including leading indentation
    ls = text.rfind("\n", 0, s) + 1
    le = text.find("\n", e)
    le = len(text) if le < 0 else le + 1
    if text[ls:s].strip():
        ls = s
    block = text[ls:le]
    if _open_tag(block, target) is not None:
        return False, "target folder is inside the document"
    rest = text[:ls] + text[le:]

    ts = _open_tag(rest, target)
    te = _item_span(rest, ts)
    folder = rest[ts:te]
    indent = re.match(r"[ \t]*", rest[rest.rfind("\n", 0, ts) + 1:]).group(0)
    close = folder.rfind("</Children>")
    if close >= 0:
        at = ts + close
        # insert before the indentation of </Children>
        line_start = rest.rfind("\n", 0, at) + 1
        new = rest[:line_start] + block + rest[line_start:]
    else:
        end_tag = folder.rfind("</BinderItem>")
        if end_tag < 0:
            return False, "target folder is self-closing; not handled"
        at = ts + end_tag
        line_start = rest.rfind("\n", 0, at) + 1
        wrapped = "%s    <Children>\n%s%s    </Children>\n" % (indent, block, indent)
        new = rest[:line_start] + wrapped + rest[line_start:]

    # verify: parses, doc now sits under target, item count unchanged
    root = ET.fromstring(new)
    before = len(list(ET.fromstring(text).iter("BinderItem")))
    after = len(list(root.iter("BinderItem")))
    def kids(it):
        c = it.find("Children")
        return list(c) if c is not None else []
    parent_ok = any(
        _uuid_of(it) == target and any(_uuid_of(c) == uuid for c in kids(it))
        for it in root.iter("BinderItem"))
    if before != after or not parent_ok:
        return False, "verification failed; nothing written"
    if not apply_it:
        return True, "dry run OK: would file under Published/%s/%s" % (dest, year)

    backup = scrivx + ".bak-" + time.strftime("%Y%m%dT%H%M%S")
    n = 1
    while os.path.exists(backup):
        n += 1
        backup = "%s.bak-%s-%d" % (scrivx, time.strftime("%Y%m%dT%H%M%S"), n)
    shutil.copy2(scrivx, backup)
    with open(scrivx, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        ET.parse(scrivx)
    except ET.ParseError as exc:
        shutil.copy2(backup, scrivx)
        return False, "write invalid (%s); backup restored" % exc
    return True, "filed under Published/%s/%s (backup %s)" % (
        dest, year, os.path.basename(backup))


# --- pending queue ---------------------------------------------------------

def queue(uuid, dest, year, title=""):
    items = load_pending()
    items = [i for i in items if i["uuid"] != uuid]
    items.append({"uuid": uuid, "dest": dest, "year": str(year), "title": title})
    _save(items)


def load_pending():
    if os.path.exists(PENDING):
        return json.load(open(PENDING))
    return []


def _save(items):
    os.makedirs(os.path.dirname(PENDING), exist_ok=True)
    json.dump(items, open(PENDING, "w"), indent=2)


def drain(project, log=print):
    """Try every pending move. Keeps the ones that can't run yet."""
    items = load_pending()
    if not items:
        return
    left = []
    for it in items:
        ok, msg = move(project, it["uuid"], it["dest"], it["year"], apply_it=True)
        log("Filing '%s': %s" % (it.get("title") or it["uuid"], msg))
        if not ok and "open" in msg:
            left.append(it)
        elif not ok and "not in binder" not in msg:
            left.append(it)
    _save(left)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 3:
        raise SystemExit(__doc__)
    yr = a[3] if len(a) > 3 else time.strftime("%Y")
    ok, msg = move(a[0], a[1], a[2], yr, "--apply" in sys.argv)
    print(msg)
    sys.exit(0 if ok else 1)
