"""Publica el contenido de site/ en GitHub Pages via API REST."""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SITE_DIR = ROOT / "site"
API = "https://api.github.com"


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def request(url, token, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "correcaminos-bot")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        return json.loads(body) if body else {}


def get_sha(repo, path, token, branch):
    url = f"{API}/repos/{repo}/contents/{path}?ref={branch}"
    try:
        return request(url, token)["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def put_file(repo, path, local_file, token, branch="main"):
    content = base64.b64encode(Path(local_file).read_bytes()).decode()
    payload = {
        "message": f"chore: publish {path}",
        "content": content,
        "branch": branch,
    }
    sha = get_sha(repo, path, token, branch)
    if sha:
        payload["sha"] = sha
    url = f"{API}/repos/{repo}/contents/{path}"
    for attempt in range(1, 4):
        try:
            request(url, token, method="PUT", payload=payload)
            return True
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="ignore")[:180]
            print(f"  [{attempt}/3] {path}: HTTP {e.code} {detail}")
            if e.code == 409:
                payload["sha"] = get_sha(repo, path, token, branch)
            time.sleep(2 * attempt)
        except Exception as e:
            print(f"  [{attempt}/3] {path}: {e}")
            time.sleep(2 * attempt)
    return False


def publish(repo=None, branch="main"):
    load_env()
    token = os.environ.get("GITHUB_TOKEN")
    repo = repo or os.environ.get("GITHUB_REPO", "aielitemail-source/correcaminos")
    if not token:
        print("[Publish] Falta GITHUB_TOKEN (define en .env)")
        return False
    if not SITE_DIR.exists():
        print("[Publish] site/ no existe. Ejecuta site_gen.py primero.")
        return False

    files = sorted(f for f in SITE_DIR.rglob("*") if f.is_file())
    ok = failed = 0
    print(f"[Publish] {len(files)} archivos -> {repo}@{branch}")
    for f in files:
        rel = f.relative_to(SITE_DIR).as_posix()
        if put_file(repo, rel, f, token, branch):
            ok += 1
            print(f"  OK  {rel}")
        else:
            failed += 1
            print(f"  ERR {rel}")
    print(f"[Publish] Done: {ok} ok, {failed} failed")
    print(f"[Publish] https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/")
    return failed == 0


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(0 if publish(repo) else 1)