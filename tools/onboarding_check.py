#!/usr/bin/env python3
"""Check which onboarding steps are done for the manual funnel review.

    python3 tools/onboarding_check.py            # setup steps on this Mac
    python3 tools/onboarding_check.py --live     # also read the sheet, reach Render, test the upload token
    python3 tools/onboarding_check.py --json

Every step id matches a section in skills/onboarding/references/steps.md. Standard library only, so it
runs before the virtual environment exists. Reports only whether a secret is set, never its value.
--live publishes nothing: the upload token is tested against an invalid page name, which the server
rejects after accepting the token (404 = token OK, 401 = wrong token).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "bin" / "python"
DEFAULT_BASE = "https://ad-translation.onrender.com"

PHASES = (
    ("Tools on this Mac", ("system-python", "system-uv", "venv", "chromium")),
    ("Settings file", ("env-file",)),
    ("Google Sheet", ("google-client", "funnel-sheet", "google-signin")),
    ("Publishing to Render", ("upload-token",)),
)
LIVE = ("live-sheet", "live-render", "live-upload-token")
TITLES = {
    "system-python": "Python 3", "system-uv": "uv (Python installer)", "venv": "Python environment (.venv)",
    "chromium": "Chromium browser for captures", "env-file": ".env file",
    "google-client": "Team Google sign-in client", "funnel-sheet": "Funnel sheet linked",
    "google-signin": "Signed in to Google", "upload-token": "Render upload token",
    "live-sheet": "Sheet can be read", "live-render": "Render site reachable",
    "live-upload-token": "Upload token accepted",
}


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")
    return values


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(cmd, 1, "", str(error))


def last_line(done: subprocess.CompletedProcess) -> str:
    lines = (done.stderr or done.stdout or "").strip().splitlines()
    return lines[-1][:200] if lines else f"exit code {done.returncode}"


def http_status(url: str, method: str = "GET", token: str = "") -> tuple[int, str]:
    request = urllib.request.Request(url, method=method, data=b"{}" if method == "POST" else None)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.status, ""
    except urllib.error.HTTPError as error:
        return error.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(getattr(error, "reason", error))


def check_steps(live: bool) -> list[dict]:
    env = read_env()
    results: list[dict] = []

    def add(step: str, ok: bool, detail: str = "") -> None:
        results.append({"id": step, "title": TITLES[step], "ok": ok, "detail": detail})

    add("system-python", sys.version_info >= (3, 9), sys.version.split()[0])
    uv = shutil.which("uv") or next((str(p) for p in (Path.home() / ".local/bin/uv",) if p.is_file()), "")
    add("system-uv", bool(uv), uv or "not installed")
    imports = "import playwright, PIL, googleapiclient, google_auth_oauthlib"
    venv_ok = VENV_PY.is_file() and run([str(VENV_PY), "-c", imports]).returncode == 0
    add("venv", venv_ok, "" if venv_ok else "missing or incomplete")
    chromium_ok = False
    if venv_ok:
        probe = ("from playwright.sync_api import sync_playwright\n"
                 "import os\np=sync_playwright().start()\nprint(os.path.exists(p.chromium.executable_path))\np.stop()")
        chromium_ok = run([str(VENV_PY), "-c", probe]).stdout.strip() == "True"
    add("chromium", chromium_ok, "" if chromium_ok else "not installed")

    add("env-file", (ROOT / ".env").is_file())
    secret_file = ROOT / (env.get("GOOGLE_CLIENT_SECRET_PATH") or "credentials.json")
    client_ok = bool(env.get("GOOGLE_CLIENT_ID") and env.get("GOOGLE_CLIENT_SECRET")) or secret_file.is_file()
    add("google-client", client_ok, "" if client_ok else "GOOGLE_CLIENT_ID/SECRET or credentials.json missing")
    add("funnel-sheet", bool(env.get("FUNNEL_SHEET_ID")), "" if env.get("FUNNEL_SHEET_ID") else "FUNNEL_SHEET_ID empty")
    signin_ok, signin_detail = False, "needs the Python environment first"
    if venv_ok:
        done = run([str(VENV_PY), "tools/google_auth.py", "--check"])
        signin_ok, signin_detail = done.returncode == 0, last_line(done)
    add("google-signin", signin_ok, signin_detail)
    token = env.get("FEEDBACK_UPLOAD_TOKEN", "")
    add("upload-token", bool(token), "set" if token else "FEEDBACK_UPLOAD_TOKEN empty")

    if live:
        base = (env.get("PUBLIC_BASE_URL") or DEFAULT_BASE).rstrip("/")
        if venv_ok and signin_ok and env.get("FUNNEL_SHEET_ID"):
            done = run([str(VENV_PY), "tools/resolve_funnel.py", "--list"])
            add("live-sheet", done.returncode == 0, "" if done.returncode == 0 else last_line(done))
        else:
            add("live-sheet", False, "finish the Google steps first")
        status, error = http_status(f"{base}/feedback/")
        add("live-render", status == 200, f"{base}/feedback/ → {status or error}")
        if token:
            status, error = http_status(f"{base}/api/feedback/_onboarding_check", "POST", token)
            meaning = {404: "accepted", 401: "rejected: wrong token"}.get(status, f"unexpected answer {status or error}")
            add("live-upload-token", status == 404, meaning)
        else:
            add("live-upload-token", False, "FEEDBACK_UPLOAD_TOKEN empty")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="Also test the sheet, Render and the upload token")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = check_steps(args.live)
    done = sum(r["ok"] for r in results)
    if args.json:
        print(json.dumps({"done": done, "total": len(results), "steps": results}, indent=2))
    else:
        print(f"Setup progress: {done} of {len(results)} done")
        by_id = {r["id"]: r for r in results}
        groups = list(PHASES) + ([("Live checks", LIVE)] if args.live else [])
        for title, steps in groups:
            print(f"\n{title}")
            for step in steps:
                r = by_id[step]
                print(f"  {'✅' if r['ok'] else '⬜'} {r['title']} [{step}]" + (f" — {r['detail']}" if r["detail"] else ""))
    return 0 if done == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
