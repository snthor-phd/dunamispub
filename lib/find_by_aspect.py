"""Find candidate source images by aspect ratio, for matching a resized export
back to its original on disk. Read-only.

  python3 find_by_aspect.py <dir> <target_ratio> [tolerance]
"""

import os
import subprocess
import sys

directory = os.path.expanduser(sys.argv[1])
target = float(sys.argv[2])
tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
EXT = (".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff")

rows = []
for name in sorted(os.listdir(directory)):
    if not name.lower().endswith(EXT):
        continue
    path = os.path.join(directory, name)
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True).stdout
    dims = {}
    for line in out.splitlines():
        if ":" in line:
            k, _, v = line.strip().partition(": ")
            dims[k] = v
    try:
        w = int(dims["pixelWidth"])
        h = int(dims["pixelHeight"])
    except (KeyError, ValueError):
        continue
    if h == 0:
        continue
    ratio = w / h
    if abs(ratio - target) <= tol:
        rows.append((abs(ratio - target), ratio, w, h, name))

for delta, ratio, w, h, name in sorted(rows):
    print("%.4f  %5dx%-5d  %s" % (ratio, w, h, name))
print("\n%d candidates of %d files" % (len(rows), len(os.listdir(directory))))
