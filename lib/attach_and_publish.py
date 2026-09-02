"""One-off: add the profile photo to post 454 and publish it now.

Kept in the repo because "attach a featured image and publish immediately"
is the obvious next feature for the publisher, and this is the working
reference for how the endpoint behaves.
"""

import datetime
import json
import subprocess
import sys
import urllib.request

SITE = "207097055"
POST = "454"
MEDIA_ID = 442
MEDIA_URL = ("https://adventuresinepsilon.wordpress.com/wp-content/uploads/"
             "2026/09/pick-03-implant-steve.jpg")
ALT = "Steve in profile, the cochlear implant processor visible behind his ear"

API = "https://public-api.wordpress.com/wp/v2/sites/%s/posts/%s" % (SITE, POST)

token = subprocess.run(
    ["security", "find-generic-password", "-s",
     "dunamispub-adventuresinepsilon", "-w"],
    capture_output=True, text=True, check=True).stdout.strip()


def call(payload=None):
    url = API if payload else API + "?context=edit"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url, data=data, method="POST" if payload else "GET",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


current = call()
body = current["content"]["raw"]

figure = (
    '<figure class="wp-block-image size-large">'
    '<img src="%s?w=768" alt="%s" class="wp-image-%d"/>'
    '</figure>' % (MEDIA_URL, ALT, MEDIA_ID)
)

if "wp-image-%d" % MEDIA_ID not in body:
    body = figure + "\n\n" + body

now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
out = call({
    "content": body,
    "featured_media": MEDIA_ID,
    "status": "publish",
    "date_gmt": now.isoformat(),
})

print("status:   %s" % out["status"])
print("date:     %s" % out["date"])
print("featured: %s" % out["featured_media"])
print("link:     %s" % out["link"])
print("images:   %d" % out["content"]["raw"].count("<img"))
print("paras:    %d" % out["content"]["raw"].count("<p>"))
