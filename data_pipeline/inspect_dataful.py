import urllib.request
import re

req = urllib.request.Request("https://dataful.in/datasets/5632/", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")

pushes = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
full_text = "".join(pushes).replace('\\"', '"').replace('\\\\', '\\')

urls = re.findall(r'https?://[^\s"<>]+', full_text)
print(f"Total URLs in payload: {len(urls)}")
for u in sorted(set(urls)):
    if any(k in u.lower() for k in ["s3", "bucket", "desagri", "upag", "download", "resource", "media", "dataful"]):
        print(f"  Candidate: {u}")


