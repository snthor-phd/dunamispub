"""RTF to Markdown for Scrivener document bodies.

Scrivener writes each paragraph as a single line terminated by a carriage
return. `textutil -convert txt` preserves those CRs verbatim, so naive
consumers see one long run-on paragraph even though the breaks are there.
Normalising CR to LF first is what makes the paragraph structure visible.
"""

import re
import subprocess


def rtf_to_text(path):
    """Extract plain text from an RTF file, with line endings normalised."""
    out = subprocess.run(
        ["textutil", "-convert", "txt", "-stdout", path],
        capture_output=True, check=True,
    ).stdout.decode("utf-8", errors="replace")
    return out.replace("\r\n", "\n").replace("\r", "\n")


def to_markdown(path):
    """Convert a Scrivener content.rtf into clean Markdown.

    Each source paragraph becomes a Markdown paragraph separated by a blank
    line. Runs of blank lines collapse to one. Trailing whitespace goes.
    """
    text = rtf_to_text(path)
    paragraphs = [p.strip() for p in text.split("\n")]
    paragraphs = [p for p in paragraphs if p]
    return "\n\n".join(paragraphs) + "\n"


SPLIT = re.compile(r"^\s*([A-Z]{2,4}-\d+)\s*[—–-]\s*(.+)$")


def split_title(binder_title):
    """Split 'SR-10 — Alive Again' into ('SR-10', 'Alive Again').

    Returns (None, title) when the document has no topic ID prefix.
    """
    m = SPLIT.match(binder_title or "")
    if m:
        return m.group(1), m.group(2).strip()
    return None, (binder_title or "").strip()


def slugify(title):
    s = title.lower()
    s = re.sub(r"['\u2019]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


if __name__ == "__main__":
    import sys
    print(to_markdown(sys.argv[1]))
