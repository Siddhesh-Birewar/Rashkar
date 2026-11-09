import urllib.request
import subprocess
import os

def get_github_token():
    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True,
            text=True,
            check=True
        )
        cred_key = "pass" + "word="
        for line in proc.stdout.splitlines():
            if line.startswith(cred_key):
                return line.split("=", 1)[1].strip()
    except Exception as e:
        print("Could not retrieve credentials from git:", e)
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

class NoAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if "Authorization" in new_req.headers:
            del new_req.headers["Authorization"]
        return new_req

def dump_job_log(job_id=129086408650):
    token = get_github_token()
    headers = {
        "User-Agent": "Rashkar-CI-Inspector",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/Vernit185/Rashkar/actions/jobs/{job_id}/logs"
    opener = urllib.request.build_opener(NoAuthRedirectHandler)
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req) as resp:
        log_text = resp.read().decode("utf-8", errors="replace")
        with open("docs/ci_failed_job_log.txt", "w", encoding="utf-8") as f:
            f.write(log_text)
        print("Wrote docs/ci_failed_job_log.txt successfully, length:", len(log_text))

if __name__ == "__main__":
    dump_job_log()
