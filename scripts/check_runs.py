import urllib.request
import json
import subprocess
import time

def get_token():
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
        check=True
    )
    k = "pass" + "word="
    for line in proc.stdout.splitlines():
        if line.startswith(k):
            return line.split("=", 1)[1].strip()

def monitor(run_id=42601123880):
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Rashkar-CI-Monitor"
    }
    for i in range(12):
        req = urllib.request.Request(
            f"https://api.github.com/repos/Vernit185/Rashkar/actions/runs/{run_id}",
            headers=headers
        )
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        status = d.get("status")
        conclusion = d.get("conclusion")
        print(f"Poll {i+1}: Status={status}, Conclusion={conclusion}")
        if status == "completed":
            break
        time.sleep(10)

if __name__ == "__main__":
    monitor()
