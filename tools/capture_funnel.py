#!/usr/bin/env python3
"""Capture a funnel page as scrolling viewport screenshots + text extraction."""

import argparse
import json
import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

MOBILE_WIDTH = 390
MOBILE_HEIGHT = 844
DESKTOP_WIDTH = 1440
DESKTOP_HEIGHT = 900

def capture_legacy(url: str, name: str, run_id: str, desktop: bool = False) -> dict:
    vw = DESKTOP_WIDTH if desktop else MOBILE_WIDTH
    vh = DESKTOP_HEIGHT if desktop else MOBILE_HEIGHT

    out_dir = Path(".tmp") / "captures" / run_id / name
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": vw, "height": vh},
            device_scale_factor=2,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ) if not desktop else None,
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        full_path = str(out_dir / "full_page.png")
        page.screenshot(path=full_path, full_page=True)

        total_height = page.evaluate("document.body.scrollHeight")
        sections = []
        y = 0
        idx = 1
        while y < total_height:
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(300)
            fname = f"section_{idx:03d}.png"
            fpath = str(out_dir / fname)
            page.screenshot(path=fpath, full_page=False)
            sections.append({"index": idx, "file": fname, "scroll_y": y})
            y += vh
            idx += 1

        text = page.evaluate("document.body.innerText")
        text_path = str(out_dir / "text_content.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        browser.close()

    result = {
        # No schema_version: legacy manifests have no hashes, checks or status.
        # The finished-report gate uses this timestamp to refuse post-cutover
        # legacy captures; only drafts and historical reports may use them.
        "capture_mode": "legacy",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "name": name,
        "url": url,
        "viewport": {"width": vw, "height": vh},
        "output_dir": str(out_dir),
        "full_page": "full_page.png",
        "sections": sections,
        "text_file": "text_content.txt",
        "total_height": total_height,
    }

    manifest_path = str(out_dir / "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def capture(url: str, name: str, run_id: str, desktop: bool = False, **options) -> dict:
    """Compatible single-page entry point backed by the indexed capture packet."""
    try:
        from .capture_packet import capture_many
    except ImportError:
        from capture_packet import capture_many
    job={'url':url,'name':name}
    for key in ('page','scope','offer_handoff','faq_selector','faq_toggle_selector','faq_open_class','faq_answer_selector','radio_selections','freeze_selectors'):
        if key in options:
            job[key]=options.pop(key)
    result=asyncio.run(capture_many([job],run_id,desktop=desktop,**options))
    if result['status']!='complete':
        raise RuntimeError(result['jobs'][0]['error'])
    return json.loads(Path(result['jobs'][0]['manifest']).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description="Capture a funnel page as screenshots")
    parser.add_argument("--url", help="URL to capture")
    parser.add_argument("--name", help="Funnel name (e.g. 'competitor' or 'ours')")
    parser.add_argument("--page", choices=('advertorial','product','checkout'), help="Actual funnel stage")
    parser.add_argument("--scope", choices=('price_and_offer','dutch_checkout'), help="Checkout review scope")
    parser.add_argument("--jobs", help="JSON array of independent capture jobs; at most two run concurrently")
    parser.add_argument("--resume", action="store_true", help="Reuse intact same-run snapshots, at most 30 minutes old")
    parser.add_argument("--concurrency", type=int, choices=(1,2), default=2)
    parser.add_argument("--budget", type=float, default=120, help="Per-page capture budget in seconds")
    parser.add_argument("--faq-selector", help="Observed FAQ row selector; default: native details")
    parser.add_argument("--faq-toggle-selector", help="Toggle within each FAQ row")
    parser.add_argument("--faq-open-class", help="Explicit expanded-state class, when aria-expanded is absent")
    parser.add_argument("--faq-answer-selector", help="Row-scoped answer element whose visibility is the expanded state")
    parser.add_argument("--freeze-selector", dest="freeze_selectors", action="append",
                        help="Observed countdown/timer selector to freeze for a stable capture; repeat for several")
    parser.add_argument("--legacy", action="store_true",
                        help="Original viewport capture fallback for diagnosis; no index or resume. "
                             "Finished reports refuse legacy captures made on/after 2026-10-02 (drafts only)")
    parser.add_argument("--run-id", default=None, help="Run ID for grouping captures (auto-generated if omitted)")
    parser.add_argument("--desktop", action="store_true", help="Use desktop viewport instead of mobile")
    args = parser.parse_args()

    run_id = args.run_id or uuid.uuid4().hex[:8]
    if args.jobs:
        if (args.url or args.name or args.page or args.scope or args.legacy or args.faq_selector or args.faq_toggle_selector
                or args.faq_open_class or args.faq_answer_selector or args.freeze_selectors):
            parser.error('Use --jobs with per-job FAQ settings, or --url and --name')
        try:
            from .capture_packet import capture_many
        except ImportError:
            from capture_packet import capture_many
        jobs=json.loads(Path(args.jobs).read_text(encoding='utf-8'))
        result=asyncio.run(capture_many(jobs,run_id,desktop=args.desktop,resume=args.resume,
                                      concurrency=args.concurrency,budget=args.budget))
    else:
        if not args.url or not args.name:
            parser.error('--url and --name are required for a single capture')
        if args.legacy:
            if args.resume or args.faq_selector or args.faq_answer_selector or args.freeze_selectors:
                parser.error('--legacy does not support resume, automatic FAQ capture or freezing')
            result=capture_legacy(args.url,args.name,run_id,args.desktop)
        else:
            options={k:getattr(args,k) for k in ('page','scope','faq_selector','faq_toggle_selector','faq_open_class',
                                                 'faq_answer_selector','freeze_selectors') if getattr(args,k)}
            result=capture(args.url,args.name,run_id,args.desktop,resume=args.resume,budget=args.budget,**options)

    print(json.dumps(result, indent=2))
    if result.get('status')=='incomplete':
        raise SystemExit(1)


if __name__ == "__main__":
    main()
