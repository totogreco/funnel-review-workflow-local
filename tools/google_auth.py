#!/usr/bin/env python3
"""Sign in to Google once so the funnel review can read the FUNNEL-BUILDING sheet.

    .venv/bin/python tools/google_auth.py            # opens the browser, saves token.json
    .venv/bin/python tools/google_auth.py --check    # only reports whether token.json works

Read-only: asks for the Sheets read-only scope and nothing else. The OAuth client comes from
GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env, or from credentials.json (GOOGLE_CLIENT_SECRET_PATH).
Never prints a token or secret.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def read_env(path: Path = ROOT / ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")
    return {**values, **{k: v for k, v in os.environ.items() if k in values}}


def resolve(env: dict[str, str], key: str, default: str) -> Path:
    path = Path(env.get(key) or default)
    return path if path.is_absolute() else ROOT / path


def client_config(env: dict[str, str]) -> dict | None:
    client_id, secret = env.get("GOOGLE_CLIENT_ID", ""), env.get("GOOGLE_CLIENT_SECRET", "")
    if client_id and secret:
        return {"installed": {
            "client_id": client_id, "client_secret": secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }}
    return None


def check_token(env: dict[str, str]) -> tuple[bool, str]:
    """True when token.json exists and can be refreshed/used. Never prints its contents."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token = resolve(env, "GOOGLE_TOKEN_PATH", "token.json")
    if not token.is_file():
        return False, "token.json not found"
    try:
        creds = Credentials.from_authorized_user_file(str(token))
        if not creds.valid:
            if not creds.refresh_token:
                return False, "token has no refresh token; sign in again"
            creds.refresh(Request())
            token.write_text(creds.to_json(), encoding="utf-8")
    except Exception as error:  # expired/revoked/wrong client: all mean "sign in again"
        return False, f"sign-in no longer valid ({type(error).__name__}); sign in again"
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="Only check the saved sign-in")
    args = parser.parse_args()
    env = read_env()

    if args.check:
        ok, reason = check_token(env)
        print("google sign-in:", reason)
        return 0 if ok else 1

    from google_auth_oauthlib.flow import InstalledAppFlow

    config = client_config(env)
    secret_file = resolve(env, "GOOGLE_CLIENT_SECRET_PATH", "credentials.json")
    if config:
        flow = InstalledAppFlow.from_client_config(config, SCOPES)
    elif secret_file.is_file():
        flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), SCOPES)
    else:
        print("error: no Google OAuth client. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env "
              "(from the owner), or put credentials.json in this folder.", file=sys.stderr)
        return 1
    creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
    token = resolve(env, "GOOGLE_TOKEN_PATH", "token.json")
    token.write_text(creds.to_json(), encoding="utf-8")
    token.chmod(0o600)
    print(f"saved {token.name} (scopes: {', '.join(creds.scopes or SCOPES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
