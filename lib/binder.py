"""Read-only access to a Scrivener 3 project's binder.

Never writes. If Scrivener changes its format, lookups return nothing rather
than raising, and the caller reports the silence instead of acting on it.
"""

import os
import xml.etree.ElementTree as ET


class Project:
    def __init__(self, path):
        self.path = os.path.expanduser(path)
        names = [f for f in os.listdir(self.path) if f.endswith(".scrivx")]
        if not names:
            raise FileNotFoundError("No .scrivx in %s" % self.path)
        self.scrivx = os.path.join(self.path, names[0])

    # --- state -----------------------------------------------------------

    @property
    def is_open(self):
        """True while Scrivener holds the project. Never write when open."""
        return os.path.exists(os.path.join(self.path, "Files", "user.lock"))

    @property
    def format_version(self):
        v = os.path.join(self.path, "Files", "version.txt")
        return open(v).read().strip() if os.path.exists(v) else None

    def content_path(self, uuid):
        return os.path.join(self.path, "Files", "Data", uuid, "content.rtf")

    def synopsis(self, uuid):
        p = os.path.join(self.path, "Files", "Data", uuid, "synopsis.txt")
        return open(p, encoding="utf-8", errors="replace").read().strip() \
            if os.path.exists(p) else ""

    # --- binder ----------------------------------------------------------

    def _root(self):
        return ET.parse(self.scrivx).getroot().find("Binder")

    def find_folder(self, title):
        """Locate a folder by exact title, anywhere in the binder."""
        wanted = title.strip().lower()

        def search(node):
            for item in node.findall("BinderItem"):
                if (item.findtext("Title") or "").strip().lower() == wanted:
                    return item
                children = item.find("Children")
                if children is not None:
                    hit = search(children)
                    if hit is not None:
                        return hit
            return None

        return search(self._root())

    def documents_in(self, folder_title):
        """Text documents directly inside a folder.

        Returns a list of dicts: uuid, title, label, status, synopsis.
        An empty list can mean an empty folder OR a folder that no longer
        exists — use folder_exists() to tell those apart.
        """
        folder = self.find_folder(folder_title)
        if folder is None:
            return []
        children = folder.find("Children")
        if children is None:
            return []
        out = []
        for item in children.findall("BinderItem"):
            if item.get("Type") != "Text":
                continue
            meta = item.find("MetaData")
            get = (lambda tag: meta.findtext(tag) if meta is not None else None)
            uuid = item.get("UUID")
            out.append({
                "uuid": uuid,
                "title": (item.findtext("Title") or "").strip(),
                "label": get("LabelID"),
                "status": get("StatusID"),
                "synopsis": self.synopsis(uuid),
            })
        return out

    def folder_exists(self, title):
        return self.find_folder(title) is not None

    def labels(self):
        """Map label ID -> name, as defined in project settings."""
        root = ET.parse(self.scrivx).getroot()
        settings = root.find("LabelSettings")
        if settings is None:
            return {}
        out = {}
        for label in settings.iter("Label"):
            out[label.get("ID")] = (label.text or "").strip()
        return out
