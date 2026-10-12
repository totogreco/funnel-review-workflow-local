#!/usr/bin/env python3
"""Render, stage and (historically) publish funnel review pages.

Since 2026-10-07 feedback pages live on Render at /feedback/{slug}/. For a local
review, stage the page here with --prepare-only, check it, then upload it with
tools/upload_feedback.py --site-dir <site_dir> --slug <slug>, which verifies the
live page on Render.

Vercel (one shared project, each review at /{slug}/, funnel.ecom-machine.com) is
the retired destination: deploying without --prepare-only still targets it and
is kept only for reference/recovery. The staging directory at
.tmp/vercel/{project}/site/ accumulates reviews across runs.

A --draft page may only be staged (--prepare-only); drafts are never deployed.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from .generate_feedback_page import generate
    from .feedback_dashboard import render_dashboard
except ImportError:
    from generate_feedback_page import generate
    from feedback_dashboard import render_dashboard

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/funnel_review_hosting.json"
VERCEL_IGNORE = "**/receipt.json\n.vercel\n.env*\n"
VERCEL_CONFIG = {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "framework": None,
    "buildCommand": "",
    "installCommand": "",
    "outputDirectory": ".",
    "headers": [{"source": "/(.*)", "headers": [
        {"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}
    ]}],
}


def _slug(value):
    value = unicodedata.normalize("NFKD", str(value).replace("™", "").replace("®", ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not result:
        raise ValueError("A nonempty value is required for slug generation")
    return result


def review_slug(meta):
    """Name every review funnel-builder-product-country using sheet metadata."""
    fields = ("funnel_builder", "brand_name", "country")
    missing = [field for field in fields
               if not isinstance(meta.get(field), str) or not meta[field].strip()]
    if missing:
        raise ValueError("Review naming requires sheet metadata: " + ", ".join(missing))
    return "-".join(_slug(meta[field]) for field in fields)


def write_json(path, data):
    temporary = path.with_suffix(".pending.json")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def deployment_receipt_path(receipt_dir, slug):
    """One receipt per review: parallel sessions publishing other reviews to the
    shared site must not overwrite this review's deployment record."""
    return Path(receipt_dir) / "deployments" / f"{slug}.json"


def generate_index(site_dir):
    """Refresh the builder-grouped dashboard for every publication."""
    (site_dir / "index.html").write_text(render_dashboard(site_dir), encoding="utf-8")


def prepare(issues_file, title="Funnel Review", draft=False,
            config_file=DEFAULT_CONFIG, output_root=None):
    config = json.loads(Path(config_file).read_text())
    if config.get("provider") != "vercel" or not config.get("scope"):
        raise ValueError(
            "Configure provider=vercel and an explicit scope "
            "in the hosting config"
        )
    project = config.get("project")
    if not project:
        raise ValueError(
            "Set a fixed 'project' name in the hosting config"
        )
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", project):
        raise ValueError("Invalid project name")
    base_url = config.get("base_url", "").rstrip("/")
    if base_url and not re.fullmatch(r"https://[a-zA-Z0-9.-]+", base_url):
        raise ValueError("base_url must be an HTTPS origin without a path")

    issues_file = Path(issues_file).resolve()
    data = json.loads(issues_file.read_text())
    meta = data.get("meta", {})
    rev_slug = review_slug(meta)

    receipt_dir = Path(output_root or ROOT / ".tmp" / "vercel") / project
    site_dir = receipt_dir / "site"
    site_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        html_file = Path(tmp) / "feedback.html"
        generate(str(issues_file), str(html_file), title, draft=draft)
        html = html_file.read_text(encoding="utf-8")

    # Lets tools/upload_feedback.py tell whether a live page is newer than this one.
    published_at = datetime.now(timezone.utc).isoformat()
    html = html.replace("<head>", f'<head><meta name="funnel-review-published-at" content="{published_at}">', 1)
    digest = hashlib.sha256(html.encode()).hexdigest()
    marker = (
        f'<meta name="funnel-review-content-sha256" content="{digest}">'
    )
    html = html.replace("<head>", "<head>\n" + marker, 1)

    review_dir = site_dir / rev_slug
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "index.html").write_text(html, encoding="utf-8")
    write_json(review_dir / "receipt.json", {
        "title": title, "draft": draft, "content_sha256": digest,
        "review_name": rev_slug,
        "issue_count": len(data.get("issues", [])),
        "funnel_builder": meta["funnel_builder"],
        "run_id": meta.get("run_id", ""),
        "published_at": published_at,
        "funnel_id": meta.get("funnel_id", ""),
        "brand_name": meta.get("brand_name", ""),
        "country": meta.get("country", ""),
    })

    write_json(site_dir / "vercel.json", VERCEL_CONFIG)
    (site_dir / ".vercelignore").write_text(VERCEL_IGNORE)
    generate_index(site_dir)

    receipt_path = deployment_receipt_path(receipt_dir, rev_slug)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "provider": "vercel", "scope": config["scope"], "project": project,
        "review_name": rev_slug,
        "review_slug": rev_slug, "run_id": meta.get("run_id", ""),
        "content_sha256": digest, "title": title, "draft": draft,
        "issues_file": str(issues_file),
        "site_dir": str(site_dir.resolve()),
        "status": "prepared",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
    }
    if base_url:
        receipt["base_url"] = base_url
    elif receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if (previous.get("project") == project
                and previous.get("base_url")):
            receipt["base_url"] = previous["base_url"]
    write_json(receipt_path, receipt)
    return receipt_path, receipt


def content_marker(digest):
    return f'<meta name="funnel-review-content-sha256" content="{digest}">'


def staged_page_digest(content):
    """The sha256 recorded in a staged page's marker, or None for a page without one."""
    match = re.search(r'<meta name="funnel-review-content-sha256" content="([0-9a-f]{64})">', content)
    return match.group(1) if match else None


def verify_staged_page(content, digest):
    """True when the page carries this digest's marker and its content still matches it."""
    marker = content_marker(digest)
    original = content.replace("<head>\n" + marker, "<head>", 1)
    return marker in content and hashlib.sha256(original.encode()).hexdigest() == digest


def validate_site(receipt):
    """Only upload self-contained reports and known hosting files."""
    site = Path(receipt["site_dir"])
    root_files = {"index.html", "vercel.json", ".vercelignore", ".gitignore"}
    for path in site.rglob("*"):
        relative = path.relative_to(site)
        if path.is_symlink():
            raise ValueError(f"Unexpected file symlink: {relative}")
        if relative.parts[0] == ".vercel":
            continue  # CLI metadata, explicitly excluded from upload.
        if path.is_dir():
            if len(relative.parts) == 1 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", path.name):
                continue
        elif ((len(relative.parts) == 1 and path.name in root_files)
              or (len(relative.parts) == 2 and path.name in {"index.html", "receipt.json"})):
            continue
        raise ValueError(f"Unexpected file in staging directory: {relative}")
    if (site / ".vercelignore").read_text() != VERCEL_IGNORE:
        raise ValueError("Unexpected file exclusion configuration")
    if json.loads((site / "vercel.json").read_text()) != VERCEL_CONFIG:
        raise ValueError("Unexpected hosting configuration")
    for page in site.glob("*/index.html"):
        if page.parent.name.startswith("."):
            continue
        info = json.loads((page.parent / "receipt.json").read_text())
        if not verify_staged_page(page.read_text(encoding="utf-8"), info["content_sha256"]):
            raise ValueError(f"Staged report changed: {page.parent.name}")
    current = site / receipt["review_slug"] / "receipt.json"
    if json.loads(current.read_text())["content_sha256"] != receipt["content_sha256"]:
        raise ValueError("Staged report changed since preparation")
    link = site / ".vercel" / "project.json"
    if link.exists() and json.loads(link.read_text()).get("projectName") != receipt["project"]:
        raise ValueError("Staging directory is linked to a different Vercel project")


def run_vercel(arguments, cwd):
    executable = shutil.which("vercel")
    if not executable:
        raise RuntimeError(
            "Vercel CLI is missing. Install with: npm install -g vercel"
        )
    environment = os.environ.copy()
    for name in ("VERCEL_PROJECT_ID", "VERCEL_ORG_ID"):
        environment.pop(name, None)
    result = subprocess.run(
        [executable, *arguments], cwd=cwd, env=environment,
        text=True, capture_output=True, timeout=300,
    )
    if result.returncode:
        raise RuntimeError(
            f"Vercel {arguments[0]} failed:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def remove_cli_environment(site):
    path = site / ".env.local"
    if path.is_symlink():
        raise ValueError("Unexpected environment symlink in staging directory")
    if path.exists():
        path.unlink()


def verify_url(url, digest):
    if not url.startswith("https://"):
        raise ValueError("The published URL must use HTTPS")
    request = Request(
        url, headers={"User-Agent": "FunnelReviewPublisher/1.0"},
    )
    with urlopen(request, timeout=45) as response:
        html = response.read().decode("utf-8")
    marker = (
        f'<meta name="funnel-review-content-sha256" content="{digest}">'
    )
    if marker not in html:
        raise RuntimeError(
            "The URL did not return this report. "
            "Check deployment status and access protection."
        )


def deployment_url_from_output(output):
    value = output.strip()
    if value.startswith("{"):
        payload = json.loads(value)
        deployment = payload.get("deployment", payload)
        value = deployment.get("url", "")
        if value and not value.startswith("https://"):
            value = "https://" + value
    if not re.fullmatch(r"https://[a-zA-Z0-9.-]+\.vercel\.app/?", value):
        raise RuntimeError(
            "Vercel did not return a deployment URL; "
            "use --verify-only to recover without redeploying"
        )
    return value


def production_url(receipt, site):
    projects = json.loads(run_vercel([
        "project", "ls", "--filter", receipt["project"],
        "--format", "json", "--scope", receipt["scope"],
    ], site))
    match = next(
        (p for p in projects.get("projects", [])
         if p.get("name") == receipt["project"]),
        None,
    )
    if not match or not match.get("latestProductionUrl"):
        raise RuntimeError(
            "No production URL returned; inspect the project"
        )
    url = match["latestProductionUrl"]
    if not url.startswith("https://"):
        url = "https://" + url
    return url


def publish(receipt_path, receipt, verify_only=False, allow_draft=False):
    """Deploy to the retired Vercel site. Drafts are refused: stage them only."""
    if receipt.get("draft") and not allow_draft:
        raise ValueError("Drafts are never deployed; stage them with --prepare-only")
    site = Path(receipt["site_dir"])
    remove_cli_environment(site)
    validate_site(receipt)

    common = ["--scope", receipt["scope"]]

    if verify_only:
        base = receipt.get("base_url") or production_url(receipt, site)
        receipt["base_url"] = base
        url = f"{base.rstrip('/')}/{receipt['review_slug']}/"
        verify_url(url, receipt["content_sha256"])
        receipt.update(
            status="published", url=url,
            published_at=datetime.now(timezone.utc).isoformat(),
        )
        write_json(receipt_path, receipt)
        write_json(Path(receipt["issues_file"]).parent
                   / f"deployment-{receipt['content_sha256'][:12]}.json", receipt)
        return receipt

    vercel_dir = site / ".vercel"
    if not vercel_dir.exists():
        print(
            f"Linking {receipt['scope']}/{receipt['project']}…",
            file=sys.stderr, flush=True,
        )
        try:
            run_vercel(
                ["link", "--yes", "--project", receipt["project"],
                 *common], site,
            )
        finally:
            remove_cli_environment(site)

    validate_site(receipt)

    print("Deploying to Vercel…", file=sys.stderr, flush=True)
    try:
        output = run_vercel(
            ["deploy", "--yes", "--prod", "--json", *common], site,
        )
    finally:
        remove_cli_environment(site)

    receipt.update(status="deployed_unverified",
                   deployment_url=deployment_url_from_output(output))
    write_json(receipt_path, receipt)
    base_url = receipt.get("base_url") or production_url(receipt, site)
    receipt["base_url"] = base_url
    url = f"{base_url.rstrip('/')}/{receipt['review_slug']}/"
    receipt.update(
        url=url, status="deployed_unverified",
        deployment_url=deployment_url_from_output(output),
    )
    write_json(receipt_path, receipt)

    verify_url(url, receipt["content_sha256"])
    receipt.update(
        status="published",
        published_at=datetime.now(timezone.utc).isoformat(),
    )
    write_json(receipt_path, receipt)

    review_record = (
        Path(receipt["issues_file"]).parent
        / f"deployment-{receipt['content_sha256'][:12]}.json"
    )
    write_json(review_record, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issues-file", required=True)
    parser.add_argument("--title", default="Funnel Review")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--draft", action="store_true",
        help="Stage an explicitly labeled draft (requires --prepare-only; never deployed)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--prepare-only", action="store_true",
        help="Stage locally without deploying (then upload with tools/upload_feedback.py)",
    )
    mode.add_argument(
        "--verify-only", action="store_true",
        help="Verify an existing deployment without redeploying",
    )
    args = parser.parse_args()
    if args.draft and not args.prepare_only:
        parser.error("--draft requires --prepare-only: drafts are staged for checking, never deployed")
    # Resolve caller-relative paths before switching to the repository root.
    args.issues_file = str(Path(args.issues_file).resolve())
    args.config = str(Path(args.config).resolve())
    try:
        os.chdir(ROOT)
        if args.verify_only:
            config = json.loads(Path(args.config).read_text())
            slug = review_slug(json.loads(Path(args.issues_file).read_text()).get("meta", {}))
            receipt_dir = ROOT / ".tmp" / "vercel" / config["project"]
            receipt_path = deployment_receipt_path(receipt_dir, slug)
            if not receipt_path.exists():
                # Reviews prepared before per-review receipts used one shared file.
                receipt_path = receipt_dir / "deployment.json"
            receipt = json.loads(receipt_path.read_text())
            if (Path(receipt["issues_file"]).resolve() != Path(args.issues_file).resolve()
                    or receipt["scope"] != config["scope"]):
                raise ValueError("Saved deployment does not match the requested review/team")
        else:
            receipt_path, receipt = prepare(
                args.issues_file, args.title, args.draft, args.config,
            )
        if not args.prepare_only:
            receipt = publish(
                receipt_path, receipt, verify_only=args.verify_only,
            )
        print(json.dumps(
            {**receipt, "receipt_file": str(receipt_path)}, indent=2,
        ))
    except (OSError, ValueError, RuntimeError,
            subprocess.SubprocessError) as error:
        print(f"Publishing failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
