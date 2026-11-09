import os
import re
import subprocess
import sys

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey|secret[_-]?key|auth[_-]?token|access[_-]?token)[\s]*[=:]+[\s]*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", "API Key/Secret"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"github_pat_[a-zA-Z0-9_]{40,}", "GitHub Fine-Grained Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/LLM Key"),
    (r"-----BEGIN [A-Z0-9_-]+ PRIVATE KEY-----", "Private Key"),
    (r"(?i)password[\s]*[=:]+[\s]*['\"]([^'\"]{8,})['\"]", "Password Assignment"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer Token"),
]

SAFE_EXCLUSIONS = [
    "replace-this-with-a-secure-random-secret-key-in-production",
    "rashkar_secure_password",
    "YOUR_KEY_HERE",
    ".env.example",
    "scan_secrets.py"
]

SKIP_DIRS = {".git", ".pytest_cache", "build", ".dart_tool", "__pycache__", ".vscode", ".idea"}

def scan_text(text, source_label):
    findings = []
    for pattern, name in SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            matched_str = match.group(0)
            is_safe = any(safe in matched_str for safe in SAFE_EXCLUSIONS)
            if not is_safe:
                redacted = matched_str[:8] + "..." + matched_str[-4:] if len(matched_str) > 12 else "[REDACTED]"
                findings.append((source_label, name, redacted))
    return findings

def scan_working_tree():
    all_findings = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            if file.endswith((".png", ".jpg", ".jpeg", ".ico", ".db", ".sqlite", ".bin", ".tar", ".gz", ".zip", ".pyc")):
                continue
            path = os.path.join(root, file)
            try:
                if os.path.getsize(path) > 500 * 1024:
                    continue
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    all_findings.extend(scan_text(content, f"File: {path}"))
            except Exception:
                pass
    return all_findings

def scan_git_history():
    all_findings = []
    res = subprocess.run(["git", "log", "--format=%H"], capture_output=True, text=True, check=True)
    commits = res.stdout.strip().split("\n")
    for commit in commits:
        if not commit:
            continue
        proc = subprocess.run(["git", "show", "--no-patch", "-p", commit], capture_output=True, errors="ignore")
        diff_text = proc.stdout or ""
        findings = scan_text(diff_text, f"Commit: {commit[:8]}")
        all_findings.extend(findings)
    return all_findings

if __name__ == "__main__":
    print("--- SCANNING WORKING TREE ---", flush=True)
    tree_findings = scan_working_tree()
    print(f"Working tree findings: {len(tree_findings)}", flush=True)
    for f in tree_findings:
        print(f"  [ALERT] {f[0]} | Type: {f[1]} | Sample: {f[2]}", flush=True)
        
    print("\n--- SCANNING GIT HISTORY ---", flush=True)
    hist_findings = scan_git_history()
    print(f"Git history findings: {len(hist_findings)}", flush=True)
    for f in hist_findings:
        print(f"  [ALERT] {f[0]} | Type: {f[1]} | Sample: {f[2]}", flush=True)
    
    if len(tree_findings) == 0 and len(hist_findings) == 0:
        print("\nRESULT: CLEAN. Zero secret leaks detected in working tree and Git history.", flush=True)
        sys.exit(0)
    else:
        sys.exit(1)
