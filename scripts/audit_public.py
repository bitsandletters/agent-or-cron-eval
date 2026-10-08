#!/usr/bin/env python3
"""Check tracked files and reachable history before public release; prints no matched contents."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


PATTERNS = {
    "home_directory": re.compile(rb"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_credential": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{35,})"),
    "provider_credential": re.compile(rb"(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}|xai-[A-Za-z0-9]{24,})"),
    "aws_access_id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}
FORBIDDEN_NAMES = {"auth.json", ".env", "host.stdout.txt", "host.stderr.txt", "host-events.jsonl", "usage.raw.txt", "review-key.private.json"}
issues = []
paths = git("ls-files", "-z").decode().split("\0")
paths = [p for p in paths if p]
for name in paths:
    parts = Path(name).parts
    if parts[0] in ("runs", "exports", ".venv") or Path(name).name in FORBIDDEN_NAMES:
        issues.append({"file": name, "kind": "private_artifact_path"})
    data = (ROOT / name).read_bytes()
    for kind, pattern in PATTERNS.items():
        if pattern.search(data):
            issues.append({"file": name, "kind": kind})
    if name.startswith("examples/") and name.endswith("results.jsonl"):
        for line in data.splitlines():
            row = json.loads(line)
            if not (row.get("mock") is True or row.get("host") == "python" and row.get("arm") == "A"):
                issues.append({"file": name, "kind": "non_synthetic_example"})

objects = git("rev-list", "--objects", "--all").decode().splitlines()
blobs = 0
for obj in objects:
    sha = obj.split(" ", 1)[0]
    if git("cat-file", "-t", sha).strip() != b"blob":
        continue
    blobs += 1
    data = git("cat-file", "blob", sha)
    for kind, pattern in PATTERNS.items():
        if pattern.search(data):
            issues.append({"object": sha, "kind": kind})
print(json.dumps({"tracked_files": len(paths), "history_blobs_checked": blobs, "issues": issues,
                  "limit": "Pattern scan plus manual tracked-file review; not a guarantee against every secret format."}, indent=2))
raise SystemExit(1 if issues else 0)
