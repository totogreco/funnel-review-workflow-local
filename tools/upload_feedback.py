#!/usr/bin/env python3
"""Upload staged feedback pages to the Render dashboard's /feedback/ pages and verify each one live.

    python tools/upload_feedback.py --site-dir .tmp/vercel/funnel-reviews/site --slug ali-flexicore-nlbe
    python tools/upload_feedback.py --site-dir .tmp/vercel/funnel-reviews/site --all   # every staged review

Choose the reviews explicitly: --slug (repeatable) or --all. Before uploading, each staged page must
still match its receipt's content hash, must not be a draft (--allow-draft overrides) and must not
replace a different live page that is newer or of unknown age (--force overrides). Pages staged
before the sha256 marker existed are verified live by their <title> instead.

Needs FEEDBACK_UPLOAD_TOKEN (and optionally PUBLIC_BASE_URL) in .env. Uploads only {slug}/index.html and
its receipt; prints one RESULT line per review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from .publish_feedback_page import staged_page_digest, verify_staged_page
except ImportError:
    from publish_feedback_page import staged_page_digest, verify_staged_page

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
TITLE = re.compile(r"<title>[^<]*</title>")
PUBLISHED = re.compile(r'<meta name="funnel-review-published-at" content="([^"]+)">')
DRAFT_TEXT = "DRAFT — incomplete or unverified review"


def post(url: str, body: Dict[str, Any], token: str) -> None:
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}",
                                              "User-Agent": "FunnelReviewUpload/1.0"})
    with urllib.request.urlopen(request, timeout=60):
        pass


def fetch(url: str) -> Optional[str]:
    """The page body, or None when the server has no page there (404)."""
    request = urllib.request.Request(url, headers={"User-Agent": "FunnelReviewUpload/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def is_draft(html: str, receipt: Dict[str, Any]) -> bool:
    # The CSS always contains the .draft-warning class; only the rendered banner marks a draft.
    return bool(receipt.get("draft")) or '<p class="draft-warning">' in html or DRAFT_TEXT in html


def _moment(value: Any) -> Optional[datetime]:
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def live_published_at(base_url: str, slug: str, live_html: str) -> Optional[datetime]:
    """When the live page was published: its own marker, else the public overview's date for that slug."""
    marker = PUBLISHED.search(live_html)
    if marker:
        return _moment(marker.group(1))
    overview = fetch(f"{base_url}/feedback/") or ""
    for row in re.finditer(r'<article class="review-row"[^>]*data-date="([0-9-]*)"[^>]*>(.*?)</article>', overview, re.S):
        if f'href="/feedback/{slug}/"' in row.group(2) and row.group(1):
            # Date only: treat the live page as published at the end of that day (conservative).
            return _moment(row.group(1) + "T23:59:59.999999+00:00")
    return None


def check_staged(html: str, receipt: Dict[str, Any]) -> Optional[str]:
    """Return the staged content hash; raise when the page no longer matches its receipt."""
    digest = staged_page_digest(html)
    recorded = receipt.get("content_sha256")
    if digest:
        if digest != recorded or not verify_staged_page(html, digest):
            raise ValueError("staged page changed since preparation (hash does not match its receipt)")
        return digest
    if recorded and hashlib.sha256(html.encode()).hexdigest() != recorded:
        raise ValueError("legacy staged page does not match its receipt hash")
    return None


def upload_one(folder: Path, base_url: str, token: str, allow_draft: bool, force: bool) -> Dict[str, Any]:
    slug = folder.name
    url = f"{base_url}/feedback/{slug}/"
    result: Dict[str, Any] = {"slug": slug, "url": url, "verified": False}
    html = (folder / "index.html").read_text(encoding="utf-8")
    receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8")) if (folder / "receipt.json").is_file() else {}
    try:
        digest = check_staged(html, receipt)
    except ValueError as error:
        return {**result, "status": "refused", "reason": str(error)}
    if is_draft(html, receipt) and not allow_draft:
        return {**result, "status": "refused", "reason": "draft page (use --allow-draft to upload it anyway)"}
    live = fetch(url)
    if live is not None and not force:
        live_digest = staged_page_digest(live)
        unchanged = (live_digest == digest) if digest else (live == html)
        if not unchanged:
            staged_at = _moment(receipt.get("published_at") or "")
            live_at = live_published_at(base_url, slug, live)
            if live_at is None or staged_at is None or live_at >= staged_at:
                when = live_at.isoformat() if live_at else "unknown"
                return {**result, "status": "refused",
                        "reason": f"the live page differs and is newer or of unknown age (live: {when}, "
                                  f"staged: {receipt.get('published_at') or 'unknown'}); use --force to replace it"}
    post(f"{base_url}/api/feedback/{slug}", {"html": html, "receipt": receipt}, token)
    live = fetch(url) or ""
    if digest:
        return {**result, "status": "uploaded", "verified": f'content="{digest}"' in live}
    # Pages staged before the sha256 marker: the live page must be this exact page (same <title>, same bytes).
    title = TITLE.search(html)
    verified = live == html and (not title or title.group(0) in live)
    return {**result, "status": "uploaded", "verified": verified,
            "verification": "verified (legacy page, no hash marker)" if verified else "legacy page not found live"}


def upload_all(site: Path, base_url: str, token: str, slugs: Optional[Iterable[str]] = None,
               allow_draft: bool = False, force: bool = False) -> List[Dict[str, Any]]:
    """Upload the named staged reviews (all of them when slugs is None)."""
    wanted = None if slugs is None else list(dict.fromkeys(slugs))
    folders = {p.name: p for p in Path(site).iterdir()
               if p.is_dir() and SLUG.fullmatch(p.name) and (p / "index.html").is_file()}
    results = []
    for name in (sorted(folders) if wanted is None else wanted):
        if name not in folders:
            results.append({"slug": name, "url": f"{base_url}/feedback/{name}/", "verified": False,
                            "status": "refused", "reason": "no staged review with this slug"})
            continue
        results.append(upload_one(folders[name], base_url, token, allow_draft, force))
    return results


def read_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")
    return values


def main() -> int:
    import os

    env = {**read_env_file(ROOT / ".env"), **os.environ}
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site-dir", type=Path, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--slug", action="append", help="Staged review to upload; repeat for several")
    choice.add_argument("--all", action="store_true", help="Upload every staged review")
    parser.add_argument("--allow-draft", action="store_true", help="Also upload pages marked as drafts")
    parser.add_argument("--force", action="store_true",
                        help="Replace a live page even when it differs and is newer or of unknown age")
    args = parser.parse_args()
    token = env.get("FEEDBACK_UPLOAD_TOKEN", "")
    if not token:
        parser.error("FEEDBACK_UPLOAD_TOKEN is not set in .env")
    base = (env.get("PUBLIC_BASE_URL") or "https://ad-translation.onrender.com").rstrip("/")
    results = upload_all(args.site_dir, base, token, None if args.all else args.slug,
                         allow_draft=args.allow_draft, force=args.force)
    for result in results:
        print("RESULT " + json.dumps(result, ensure_ascii=False))
    return 0 if results and all(r["verified"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
