"""Add a document to a folder in a Scrivener project's binder.

  python3 add_binder_doc.py <project.scriv> <folder title> <doc title> <body file> [--synopsis file] [--label N] [--status N] [--apply]

GUARDED. The only tool here that writes to a .scriv, so it refuses unless:
  · Scrivener does not hold the project (Files/user.lock absent)
  · Files/version.txt matches the version this was built against
  · a timestamped copy of the .scrivx is taken first

Read-only without --apply.
"""

import os
import re
import shutil
import sys
import time
import uuid
import xml.etree.ElementTree as ET

EXPECTED_VERSION = "23"

RTF = ("{\\rtf1\\ansi\\ansicpg1252\\cocoartf2761\n"
       "{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica;}\n"
       "{\\colortbl;\\red255\\green255\\blue255;}\n"
       "\\pard\\partightenfactor0\n"
       "\\f0\\fs26 \\cf0 %s}")


def rtf_escape(text):
    out = []
    for ch in text:
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ord(ch) > 127:
            out.append("\\u%d?" % ord(ch))
        else:
            out.append(ch)
    return "".join(out).replace("\n\n", "\\\n\\\n").replace("\n", "\\\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    project = os.path.expanduser(args[0])
    folder_title = args[1]
    doc_title = args[2]
    body_file = args[3]

    synopsis = ""
    for f in flags:
        if f.startswith("--synopsis="):
            synopsis = open(os.path.expanduser(f.split("=", 1)[1])).read().strip()
    label = next((f.split("=", 1)[1] for f in flags if f.startswith("--label=")), None)
    status = next((f.split("=", 1)[1] for f in flags if f.startswith("--status=")), None)
    apply_it = "--apply" in flags

    # --- gates ---------------------------------------------------------
    lock = os.path.join(project, "Files", "user.lock")
    if os.path.exists(lock):
        sys.exit("REFUSED: Scrivener has this project open (user.lock present).")

    version = open(os.path.join(project, "Files", "version.txt")).read().strip()
    if version != EXPECTED_VERSION:
        sys.exit("REFUSED: project format %s, expected %s." % (version, EXPECTED_VERSION))

    scrivx = os.path.join(project, [f for f in os.listdir(project)
                                    if f.endswith(".scrivx")][0])

    tree = ET.parse(scrivx)
    binder = tree.getroot().find("Binder")

    def find(node):
        for item in node.findall("BinderItem"):
            if (item.findtext("Title") or "").strip().lower() == folder_title.lower():
                return item
            kids = item.find("Children")
            if kids is not None:
                hit = find(kids)
                if hit is not None:
                    return hit
        return None

    folder = find(binder)
    if folder is None:
        sys.exit("REFUSED: no folder titled %r in the binder." % folder_title)

    body = open(os.path.expanduser(body_file)).read().strip()
    new_uuid = str(uuid.uuid4()).upper()

    print("project:  %s" % project)
    print("folder:   %s" % folder_title)
    print("new doc:  %s" % doc_title)
    print("uuid:     %s" % new_uuid)
    print("words:    %d" % len(body.split()))
    if not apply_it:
        print("\nDry run. Add --apply to write it.")
        return

    backup = scrivx + ".bak-" + time.strftime("%Y%m%dT%H%M%S")
    shutil.copy2(scrivx, backup)
    print("backup:   %s" % os.path.basename(backup))

    data_dir = os.path.join(project, "Files", "Data", new_uuid)
    os.makedirs(data_dir)
    with open(os.path.join(data_dir, "content.rtf"), "w") as fh:
        fh.write(RTF % rtf_escape(body))
    if synopsis:
        with open(os.path.join(data_dir, "synopsis.txt"), "w") as fh:
            fh.write(synopsis)

    children = folder.find("Children")
    if children is None:
        children = ET.SubElement(folder, "Children")

    stamp = time.strftime("%Y-%m-%d %H:%M:%S ") + time.strftime("%z")
    item = ET.SubElement(children, "BinderItem")
    item.set("UUID", new_uuid)
    item.set("Type", "Text")
    item.set("Created", stamp)
    item.set("Modified", stamp)
    ET.SubElement(item, "Title").text = doc_title
    meta = ET.SubElement(item, "MetaData")
    ET.SubElement(meta, "IncludeInCompile").text = "Yes"
    if label is not None:
        ET.SubElement(meta, "LabelID").text = label
    if status is not None:
        ET.SubElement(meta, "StatusID").text = status

    tree.write(scrivx, encoding="UTF-8", xml_declaration=True)

    # verify it still parses
    try:
        ET.parse(scrivx)
        print("written and re-parsed cleanly.")
    except ET.ParseError as exc:
        shutil.copy2(backup, scrivx)
        sys.exit("Write produced invalid XML (%s). Backup restored." % exc)


if __name__ == "__main__":
    main()
