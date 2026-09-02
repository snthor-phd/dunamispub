"""Upload an image to the WordPress.com media library and set it as a post's
featured image — the thing that becomes the link-preview thumbnail.

  python3 set_featured_image.py <image path> <post id> [alt text]

Uses the token in the Keychain. Prints the media id and verifies og:image.
"""

import json
import mimetypes
import os
import subprocess
import sys
import urllib.request
import uuid

SITE = "207097055"
KEYCHAIN = "dunamispub-adventuresinepsilon"
BASE = "https://public-api.wordpress.com/wp/v2/sites/%s" % SITE

path = os.path.expanduser(sys.argv[1])
post_id = sys.argv[2]
alt = sys.argv[3] if len(sys.argv) > 3 else ""

token = subprocess.run(
    ["security", "find-generic-password", "-s", KEYCHAIN, "-w"],
    capture_output=True, text=True, check=True).stdout.strip()

filename = os.path.basename(path)
mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
boundary = uuid.uuid4().hex

with open(path, "rb") as fh:
    blob = fh.read()

body = b"".join([
    ("--%s\r\n" % boundary).encode(),
    ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode(),
    ("Content-Type: %s\r\n\r\n" % mime).encode(),
    blob,
    ("\r\n--%s--\r\n" % boundary).encode(),
])

req = urllib.request.Request(
    BASE + "/media", data=body, method="POST",
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "multipart/form-data; boundary=%s" % boundary})
with urllib.request.urlopen(req, timeout=180) as resp:
    media = json.load(resp)

media_id = media["id"]
print("uploaded: id %s  %s" % (media_id, media["source_url"]))

if alt:
    req = urllib.request.Request(
        "%s/media/%s" % (BASE, media_id),
        data=json.dumps({"alt_text": alt}).encode(), method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=60).read()

req = urllib.request.Request(
    "%s/posts/%s" % (BASE, post_id),
    data=json.dumps({"featured_media": media_id}).encode(), method="POST",
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as resp:
    post = json.load(resp)

print("post %s featured_media: %s" % (post_id, post["featured_media"]))
print("link: %s" % post["link"])
