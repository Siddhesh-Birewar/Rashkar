import urllib.request
import re

url = "https://raw.githubusercontent.com/geohacker/india/master/taluk/india_taluk.geojson"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    chunk = resp.read(1024 * 500).decode("utf-8", errors="ignore")
    props = re.findall(r'"properties":\s*(\{[^}]+\})', chunk)
    print("Found properties count:", len(props))
    for p in props[:5]:
        print("  ", p)
