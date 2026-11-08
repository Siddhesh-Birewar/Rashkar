from bs4 import BeautifulSoup
import httpx

def inspect_html():
    url = "https://dataful.in/datasets/5632/"
    r = httpx.get(url, follow_redirects=True, timeout=15.0)
    soup = BeautifulSoup(r.text, "html.parser")
    for s in soup.find_all("script"):
        src = s.get("src")
        if src:
            print("Script src:", src)
        else:
            text = s.text.strip()
            if "download" in text.lower() or "dataset" in text.lower() or "5632" in text:
                print("Inline script snippet:", text[:300])

if __name__ == "__main__":
    inspect_html()
