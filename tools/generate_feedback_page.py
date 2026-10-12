#!/usr/bin/env python3
"""Generate a self-contained HTML feedback page from a structured issues JSON file."""

import argparse
import base64
import json
import html as html_module
import re
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime, timezone
try:
    from .review_coverage import ReviewRefs, validate_packet, validate_cross_page
    from .review_io import child_path
    from .checkout_review import DUTCH_CHECKOUT_SCOPE, CHECKOUT_REVIEW_CHECKS, is_dutch_market, validate_dutch_checkout
    from .checkout_review import is_swedish_market, validate_swedish_offers, SWEDISH_OFFER_CHECKS
except ImportError:
    from review_coverage import ReviewRefs, validate_packet, validate_cross_page
    from review_io import child_path
    from checkout_review import DUTCH_CHECKOUT_SCOPE, CHECKOUT_REVIEW_CHECKS, is_dutch_market, validate_dutch_checkout
    from checkout_review import is_swedish_market, validate_swedish_offers, SWEDISH_OFFER_CHECKS

PAGE_LABELS = {"advertorial": "Advertorial", "product": "Product page",
               "checkout": "Checkout — prices & offer"}
CHECKOUT_CHECKS = {"price_and_discount", "offer_presentation", "pricing_consistency"}
# The indexed capture pipeline replaced legacy captures for finished reports on
# this date. Older legacy manifests keep working so historical reports can be
# republished; newer ones (and any in a current-policy run) are drafts only.
INDEXED_CUTOVER = datetime(2026, 10, 2, tzinfo=timezone.utc)


def validate_legacy_capture(key, capture, current_policy):
    """Finished reports accept legacy (unindexed) manifests only as history."""
    if current_policy:
        raise ValueError(f"Legacy capture for {key} cannot back a review_policy_version >= 2 report; "
                         "recapture with the indexed pipeline or render a --draft")
    captured_at = capture.get("captured_at")
    if captured_at is None:
        return  # Pre-fix legacy manifests recorded no timestamp: historical captures.
    try:
        moment = datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Legacy capture for {key} has an unreadable captured_at") from error
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    if moment >= INDEXED_CUTOVER:
        raise ValueError(f"Legacy capture for {key} was made on/after 2026-10-02; finished reports need "
                         "an indexed capture packet (use --draft for a diagnostic preview)")

# Diff whole lexical units, never individual digits or parts of a word. A numeric
# range is one unit so changing either endpoint still gives a usable price range.
_NUMBER = r"\d+(?:[ \u00a0\u202f]\d{3}(?!\d))*(?:[.,]\d+)*"
_AMOUNT = rf"(?:[€$£¥][ \u00a0\u202f]*)?{_NUMBER}(?:[ \u00a0\u202f]*[€$£¥%])?"
_COPY_TOKEN = re.compile(
    rf"{_AMOUNT}(?:[ \u00a0\u202f]*(?:tot|to|bis|à|[-–—])[ \u00a0\u202f]*{_AMOUNT})?"
    r"|\w+(?:['’\-]\w+)*|\s+|[^\w\s]", re.UNICODE
)
_SHORT_PHRASE = re.compile(r"[\w’'\-]+(?:[ \t]+[\w’'\-]+){1,4}", re.UNICODE)


def is_short_phrase(text: str) -> bool:
    """Keep compact plain-language snippets, not whole sentences or price labels."""
    return (len(text) <= 80 and bool(_SHORT_PHRASE.fullmatch(text))
            and any(char.isalpha() for char in text))


def concise_replacements(find: str, replace: str, copy_scope: str = "auto",
                         copy_scope_reason: str = "") -> list:
    """Return exact, independently applicable edits with offsets into the input.

    Source strings stay immutable. Offsets and reconstruction guard against a
    misleading diff; occurrence context is rendered outside the copy buttons.
    """
    if not isinstance(find, str) or not isinstance(replace, str):
        raise ValueError("Replacement find/replace values must be strings")
    if copy_scope not in ("auto", "phrase", "full"):
        raise ValueError("copy_scope must be auto, phrase or full")
    if copy_scope in ("phrase", "full") and not str(copy_scope_reason or "").strip():
        raise ValueError("An explicit phrase or full rewrite requires copy_scope_reason")
    if copy_scope == "phrase" and any(
            len(text) > 120 or len(text.split()) > 12 or "\n" in text or "\r" in text
            for text in (find, replace)):
        raise ValueError("Phrase scope is limited to one short phrase (120 characters / 12 words)")
    if find == replace:
        return []
    if (copy_scope in ("phrase", "full") or not find or not replace
            or (is_short_phrase(find) and is_short_phrase(replace))):
        return [{"find": find, "replace": replace, "start": 0, "end": len(find)}]

    old = list(_COPY_TOKEN.finditer(find))
    new = list(_COPY_TOKEN.finditer(replace))
    old_tokens = [m.group() for m in old]
    new_tokens = [m.group() for m in new]
    opcodes = SequenceMatcher(None, old_tokens, new_tokens, autojunk=False).get_opcodes()
    spans = []
    for index, (tag, a, b, c, d) in enumerate(opcodes):
        if tag == "equal":
            continue
        # An insertion inside existing copy needs a FIND anchor. Whitespace-only
        # edits also need a visible anchor. Reuse only adjacent equal tokens.
        if not "".join(old_tokens[a:b]).strip():
            if index + 1 < len(opcodes):
                _, _, right_end, _, _ = opcodes[index + 1]
                for pos in range(b, right_end):
                    if old_tokens[pos].strip():
                        d += pos + 1 - b
                        b = pos + 1
                        break
            if not "".join(old_tokens[a:b]).strip() and index:
                _, left_start, _, _, _ = opcodes[index - 1]
                for pos in range(a - 1, left_start - 1, -1):
                    if old_tokens[pos].strip():
                        c -= a - pos
                        a = pos
                        break
        if spans and a <= spans[-1][1] and c <= spans[-1][3]:
            previous = spans[-1]
            spans[-1] = (previous[0], max(previous[1], b), previous[2], max(previous[3], d))
        else:
            spans.append((a, b, c, d))

    def offset(matches, index, text):
        return matches[index].start() if index < len(matches) else len(text)

    result = []
    for a, b, c, d in spans:
        start, end = offset(old, a, find), offset(old, b, find)
        replacement = replace[offset(new, c, replace):offset(new, d, replace)]
        # Anchoring may include an unchanged space on both sides of the edit.
        # Remove that space, but keep any whitespace that actually changes.
        while start < end and replacement and find[start].isspace() and find[start] == replacement[0]:
            start += 1
            replacement = replacement[1:]
        while start < end and replacement and find[end - 1].isspace() and find[end - 1] == replacement[-1]:
            end -= 1
            replacement = replacement[:-1]
        result.append({"find": find[start:end], "replace": replacement,
                       "start": start, "end": end})
    reconstructed = find
    for edit in reversed(result):
        reconstructed = reconstructed[:edit["start"]] + edit["replace"] + reconstructed[edit["end"]:]
    if reconstructed != replace:
        raise ValueError("Concise replacements do not reconstruct the intended correction")
    return result


def build_replacement_blocks(issue: dict) -> str:
    """Normalize both supported schemas before building visible and copied text."""
    replacements = issue.get("replacements") or [{
        "find": issue.get("wrong_text", ""), "replace": issue.get("correct_text", ""),
        "copy_scope": issue.get("copy_scope", "auto"),
        "copy_scope_reason": issue.get("copy_scope_reason", ""),
    }]
    blocks = []
    escape = html_module.escape
    for replacement in replacements:
        original = replacement.get("find", "")
        corrected = replacement.get("replace", "")
        edits = concise_replacements(original, corrected, replacement.get("copy_scope", "auto"),
                                     replacement.get("copy_scope_reason", ""))
        narrowed = len(edits) > 1 or bool(edits and edits[0]["find"] != original)
        for number, edit in enumerate(edits, 1):
            find_text, replace_text = escape(edit["find"]), escape(edit["replace"])
            marker = escape(str(replacement.get("marker", "")))
            scope_note = "Replace only this fragment; keep surrounding text and formatting."
            if replacement.get("copy_scope") == "full":
                scope_note = "Replace this complete passage; retain the intended formatting."
            elif replacement.get("copy_scope") == "phrase":
                scope_note = "Replace this short phrase; keep surrounding text and formatting."
            if not find_text:
                scope_note = "Insert this text at the indicated location."
            elif not replace_text:
                scope_note = "Delete only this text at the indicated location."
            action = scope_note if narrowed else replacement.get("action", scope_note)
            part = f" (change {number} of {len(edits)})" if len(edits) > 1 else ""
            context = ""
            if narrowed:
                start, end = edit["start"], edit["end"]
                before = ("…" if start > 70 else "") + original[max(0, start - 70):start]
                after = original[end:end + 70] + ("…" if len(original) > end + 70 else "")
                context = (f'<p class="replacement-context">At this occurrence: '
                           f'{escape(before)}<mark>{find_text}</mark>{escape(after)}</p>')
            if replacement.get("location"):
                context = f'<p class="replacement-context">{escape(replacement["location"])}</p>' + context
            find_block = (f'<div class="text-block wrong"><div class="text-header"><span class="text-label">Find this exact text</span><button class="copy-btn" data-copy="{find_text}">Copy</button></div><pre class="text-content">{find_text}</pre></div>'
                          if find_text else '')
            if replace_text:
                label = "Copy & paste this replacement" if find_text else "Copy & paste this addition"
                replacement_block = f'<div class="text-block correct"><div class="text-header"><span class="text-label">{label}</span><button class="copy-btn" data-copy="{replace_text}">Copy</button></div><pre class="text-content">{replace_text}</pre></div>'
            else:
                replacement_block = '<p class="replacement-context">Delete the text above; no replacement text.</p>'
            blocks.append(f'<div class="replacement"><p><strong>{marker}</strong>{part} {escape(action)}</p>{context}{find_block}{replacement_block}</div>')
    return '<div class="replacements">' + ''.join(blocks) + '</div>' if blocks else ''


def validate_review_coverage(data: dict) -> None:
    """Require evidence and reviewer completion for both stages on both sides."""
    expected = {(side, page) for side in ("competitor", "ours")
                for page in ("advertorial", "product")}
    seen = set()
    blocked = set()
    manifests = set()
    legacy = []
    indexed = False
    meta = data.get('meta', {})
    current_policy = meta.get('review_policy_version', 1) >= 2
    swedish_policy = meta.get('review_policy_version', 1) >= 3
    dutch_checkout = None
    custom = is_custom_funnel(meta)
    # Owner decisions may close a check (questions go to chat), but must be real
    # decisions with a question; decision-only checks are reported back.
    finding_ids = ReviewRefs(data.get('issues', []), data.get('decisions', []))
    for entry in data.get("meta", {}).get("pages", []):
        key = (entry.get("side"), entry.get("page"))
        checkout = key[0] in ("competitor", "ours") and key[1] == "checkout"
        if (key not in expected and not checkout) or key in seen:
            raise ValueError(f"Unexpected or duplicate review page: {key}")
        if checkout and entry.get("scope") not in {"price_and_offer", DUTCH_CHECKOUT_SCOPE}:
            raise ValueError("Checkout capture scope must be price_and_offer or dutch_checkout")
        if entry.get('scope') == DUTCH_CHECKOUT_SCOPE and (key != ('ours', 'checkout') or not is_dutch_market(meta)):
            raise ValueError('Dutch checkout scope applies only to our Dutch-market checkout')
        seen.add(key)
        # Custom funnels review our product page against our own advertorial, so an
        # unreachable competitor second URL is recorded context, not a review gap.
        if custom and key == ("competitor", "product") and entry.get("status") == "blocked":
            if not str(entry.get("blocker", "")).strip():
                raise ValueError("A blocked competitor product page needs a recorded blocker")
            blocked.add(key)
            continue
        if entry.get("status") != "reviewed":
            raise ValueError(f"Page is not reviewed: {key}")
        if not entry.get("url") or not entry.get("manifest"):
            raise ValueError(f"Missing URL or capture manifest: {key}")
        path = Path(entry["manifest"])
        if path.resolve() in manifests:
            raise ValueError("Each review page must have its own capture manifest")
        manifests.add(path.resolve())
        capture = json.loads(path.read_text(encoding="utf-8"))
        current_policy = current_policy or capture.get('review_policy_version', 1) >= 2
        swedish_policy = swedish_policy or capture.get('review_policy_version', 1) >= 3
        if capture.get('schema_version') == 2:
            indexed = True
            validate_packet(entry, capture, path, finding_ids)
        else:
            legacy.append((key, capture))
        capture_url = (capture.get("resolved_url", capture.get("url")) if checkout and capture.get("offer_handoff")
                       else capture.get("url"))
        if capture_url != entry["url"]:
            raise ValueError(f"Capture URL does not match review page: {key}")
        sections = capture.get("sections", [])
        if not sections:
            raise ValueError(f"Capture has no section screenshots: {key}")
        files = [capture.get("full_page"), capture.get("text_file")]
        files.extend(section.get("file") for section in sections)
        for name in files:
            if not name or not child_path(path.parent, name).is_file():
                raise ValueError(f"Missing capture evidence for {key}: {name}")
        if checkout and entry.get('scope') == DUTCH_CHECKOUT_SCOPE:
            if capture.get('schema_version') != 2 or capture.get('scope') != DUTCH_CHECKOUT_SCOPE or capture.get('page') != 'checkout':
                raise ValueError('Dutch checkout requires a fresh indexed dutch_checkout packet')
            validate_dutch_checkout(entry, capture, path, finding_ids, meta)
            dutch_checkout = entry
    for key, capture in legacy:
        validate_legacy_capture(key, capture, current_policy)
    if not expected.issubset(seen):
        missing = sorted(expected - seen)
        raise ValueError(f"Incomplete review: missing pages {missing}. Review both advertorials and both product pages.")
    if indexed:
        validate_cross_page(data.get('meta', {}), finding_ids)
    if current_policy and is_dutch_market(meta) and dutch_checkout is None:
        raise ValueError('Dutch-market reviews require our completed dutch_checkout review, even when offers are on the product page')
    if is_swedish_market(meta) and (swedish_policy or meta.get('swedish_offer_checks_file')):
        validate_swedish_offers(meta, finding_ids)
    locations = data.get("meta", {}).get("offer_locations")
    if locations is not None:
        if (not isinstance(locations, dict) or set(locations) != {"competitor", "ours"}
                or any(page not in ("product", "checkout") for page in locations.values())):
            raise ValueError("offer_locations must identify product or checkout for both sides")
        for side, page in locations.items():
            if (side, page) not in seen:
                raise ValueError(f"Missing checkout offer review for {side}")
            if (side, page) in blocked:
                raise ValueError(f"Offer location for {side} is a blocked page; offers need a reviewed page")
    for issue in data.get("issues", []):
        if issue.get("page") not in PAGE_LABELS:
            raise ValueError("Every issue must identify its page as advertorial, product or checkout")
        if issue.get("target_url"):
            matching_page = next((p for p in data["meta"]["pages"]
                                  if p["side"] == issue.get("side", "ours")
                                  and p["page"] == issue["page"]), None)
            if not matching_page or matching_page["url"] != issue["target_url"]:
                raise ValueError("Finding target_url does not match its declared page")
        if issue.get("check") == "off_topic_introduction":
            replacements = issue.get("replacements") or [{
                "find": issue.get("wrong_text", ""), "replace": issue.get("correct_text", "")}]
            if not any(r.get("find", "").strip() and r.get("replace", "").strip()
                       and r["find"] != r["replace"] for r in replacements):
                raise ValueError("Off-topic introductions require concrete replacement copy, not removal-only feedback")
        if issue.get("page") == "checkout":
            extra = CHECKOUT_REVIEW_CHECKS if dutch_checkout and issue.get('side', 'ours') == 'ours' else {}
            if is_swedish_market(meta) and meta.get('swedish_offer_checks_file') and issue.get('side', 'ours') == 'ours':
                extra = SWEDISH_OFFER_CHECKS
            if issue.get("check") not in CHECKOUT_CHECKS and issue.get('check') not in extra:
                raise ValueError("Checkout findings must concern prices or offer presentation")
            if (issue.get("side", "ours"), "checkout") not in seen:
                raise ValueError("Checkout findings require a reviewed checkout capture")
    for item in data.get("issues", []) + data.get("decisions", []):
        if item.get("check") in {"discount_calculation", "discount_percentage_calculation", "discount_rounding"}:
            raise ValueError("Discount-percentage calculations are excluded from findings and owner decisions")
        if item.get("check") == "review_count":
            raise ValueError("Review counts are excluded from findings and owner decisions")
        if item.get("check") == "footer_email_link":
            raise ValueError("Footer email links are excluded from findings and owner decisions")
        if item.get("check") in {
                "button_text", "button_copy", "button_label", "button_translation",
                "cta_text", "cta_copy", "cta_label", "cta_translation"}:
            raise ValueError("Button text is excluded from findings and owner decisions")
    return {"decision_only_checks": finding_ids.decision_only_checks}


def is_custom_funnel(meta: dict) -> bool:
    """Owner-declared custom funnel: our product page is built from our advertorial."""
    funnel_type = meta.get("funnel_type", "standard")
    if funnel_type not in ("standard", "custom"):
        raise ValueError("funnel_type must be standard or custom")
    if funnel_type == "custom" and not str(meta.get("owner_scope", "")).strip():
        raise ValueError("Custom funnel reviews require the owner's instruction in meta.owner_scope")
    return funnel_type == "custom"


def page_scope_summary(data: dict) -> str:
    """State which pages were actually reviewed; custom mode is not a 4-page comparison."""
    meta = data.get("meta", {})
    if not is_custom_funnel(meta):
        return "Reviewed: competitor and our advertorials + product pages (4 pages)."
    competitor = next((p for p in meta.get("pages", [])
                       if p.get("side") == "competitor" and p.get("page") == "product"), {})
    reference = ("competitor product page used as offer context only"
                 if competitor.get("status") == "reviewed"
                 else "competitor product page not reachable")
    return ("Custom funnel: advertorials compared with the competitor; our product page "
            f"reviewed against our own advertorial ({reference}).")


def offer_scope_summary(data: dict) -> str:
    """Describe recorded evidence without granting historical runs new coverage."""
    if is_swedish_market(data.get('meta', {})) and data.get('meta', {}).get('swedish_offer_checks_file'):
        return 'Swedish offer buttons, selected checkout bundles and presented-versus-checkout prices reviewed. No order was submitted.'
    dutch = any(p.get('side') == 'ours' and p.get('page') == 'checkout' and
                p.get('scope') == DUTCH_CHECKOUT_SCOPE and p.get('status') == 'reviewed'
                for p in data.get('meta', {}).get('pages', []))
    if dutch:
        return ('Dutch checkout reviews, dates, names, FAQs, guarantee and visible iDEAL/Bancontact options reviewed. '
                'Payment submission and transaction processing were not tested.')
    reviewed = [p["side"] for p in data.get("meta", {}).get("pages", [])
                if p.get("page") == "checkout" and p.get("scope") == "price_and_offer"
                and p.get("status") == "reviewed"]
    if reviewed:
        sides = ", ".join("our funnel" if side == "ours" else "competitor" for side in reviewed)
        return f"Checkout prices and offer presentation reviewed: {sides}. Payment flow excluded."
    if data.get("meta", {}).get("offer_locations") == {"competitor": "product", "ours": "product"}:
        return "Offers reviewed on both product pages. Checkout payment flow excluded."
    return "Checkout prices and offers were not reviewed in this run."


def img_to_base64(path: str) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def replacements_by_evidence(issue: dict) -> list:
    """Attach edits to their evidence; reject ambiguity instead of guessing order."""
    pairs = issue.get("evidence_pairs", [])
    groups = [[] for _ in pairs]
    replacements = issue.get("replacements") or []
    if not replacements and (issue.get("wrong_text") or issue.get("correct_text")):
        replacements = [{"find": issue.get("wrong_text", ""),
                         "replace": issue.get("correct_text", ""),
                         "copy_scope": issue.get("copy_scope", "auto"),
                         "copy_scope_reason": issue.get("copy_scope_reason", "")}]
    keys = [str(p.get("id") or p.get("marker", "")).split(" · ")[0].strip() for p in pairs]
    nonempty = [key for key in keys if key]
    if len(nonempty) != len(set(nonempty)):
        raise ValueError("Evidence IDs/markers must be unique within a finding")
    for replacement in replacements:
        refs = replacement.get("evidence_ids")
        if refs is None:
            if len(pairs) == 1:
                groups[0].append(replacement)
                continue
            refs = [str(replacement.get("marker", ""))]
        if (not isinstance(refs, list) or not refs or
                any(not isinstance(ref, str) or not ref or ref not in keys for ref in refs)
                or len(refs) != len(set(refs))):
            raise ValueError(f"{issue.get('id', 'Finding')}: every replacement needs valid evidence_ids matching its screenshot(s)")
        for ref in refs:
            groups[keys.index(ref)].append(replacement)
    return groups


def feedback_pages(item: dict) -> str:
    """Explicit multi-page scope supplements the finding's primary page label."""
    pages = item.get("pages", [item.get("page")])
    if not isinstance(pages, list) or any(page not in PAGE_LABELS for page in pages):
        return item.get("page") if item.get("page") in PAGE_LABELS else ""
    return " ".join(dict.fromkeys(pages))


def build_card(issue: dict, index: int) -> str:
    """Legacy fragment API; finished reports use feedback_presentation.render_report."""
    cat = issue.get("category", "translation")
    label = "T" if cat == "translation" else "V"
    type_label = "Translation" if cat == "translation" else "Visual"
    issue_id = html_module.escape(str(issue.get("id", f"{label}{index}")))
    page_label = " + ".join(PAGE_LABELS[page] for page in feedback_pages(issue).split())
    location_html = f'<span class="type-label"> · {html_module.escape(page_label)}</span>' if page_label else ""

    desc = html_module.escape(issue.get("description", ""))

    screenshot_html = ""
    text_html = ""
    if issue.get("evidence_pairs"):
        panels = []
        groups = replacements_by_evidence(issue)
        compact_gallery = (issue.get("check") == "missing_comments"
                           and len(issue["evidence_pairs"]) > 1
                           and all(pair.get("source_screenshot") and not pair.get("target_screenshot")
                                   for pair in issue["evidence_pairs"]))
        for pair, replacements in zip(issue["evidence_pairs"], groups):
            marker = html_module.escape(pair.get("marker", ""))
            source_caption = html_module.escape(pair.get("source_caption", "Source reference"))
            target_caption = html_module.escape(pair.get("target_caption", "Dutch target"))
            source_panel = ""
            if pair.get("source_screenshot"):
                source_b64 = img_to_base64(pair["source_screenshot"])
                source_image = f'<img src="data:image/png;base64,{source_b64}" alt="{issue_id} {marker}: {source_caption}">'
                if compact_gallery:
                    source_image = f'<button type="button" class="evidence-zoom" aria-label="Enlarge {marker}">{source_image}</button>'
                source_panel = f'<figure><figcaption>{source_caption}</figcaption>{source_image}</figure>'
            target_panel = ""
            if pair.get("target_screenshot"):
                target_b64 = img_to_base64(pair["target_screenshot"])
                target_panel = f'<figure><figcaption>{target_caption}</figcaption><img src="data:image/png;base64,{target_b64}" alt="{issue_id} {marker}: {target_caption}"></figure>'
            if not source_panel and not target_panel:
                raise ValueError("Each evidence group requires a source or target screenshot")
            panel_class = "evidence-panels" if source_panel and target_panel else "evidence-panels evidence-single"
            instruction = pair.get("instruction", "")
            if not isinstance(instruction, str):
                raise ValueError("Evidence instruction must be a string")
            instruction_html = (f'<div class="evidence-instruction">{html_module.escape(instruction)}</div>'
                                if instruction.strip() else "")
            panels.append(f'''<div class="evidence-pair" data-pages="{feedback_pages(pair)}"><div class="evidence-marker">{marker}</div>
                <div class="{panel_class}">
                {source_panel}
                {target_panel}
                </div>{instruction_html}{build_replacement_blocks({"replacements": replacements})}</div>''')
        screenshot_html = ''.join(panels)
        if compact_gallery:
            screenshot_html = '<p class="gallery-hint">Select a screenshot to enlarge it.</p><div class="evidence-gallery">' + screenshot_html + '</div>'
    elif issue.get("source_screenshot") and issue.get("screenshot"):
        source_b64 = img_to_base64(issue["source_screenshot"])
        target_b64 = img_to_base64(issue["screenshot"])
        screenshot_html = f'''<div class="evidence-panels">
            <figure><figcaption>Source reference</figcaption><img src="data:image/png;base64,{source_b64}" alt="{issue_id}: source reference outlined in green"></figure>
            <figure><figcaption>Dutch target</figcaption><img src="data:image/png;base64,{target_b64}" alt="{issue_id}: target issue outlined in red"></figure>
        </div>'''
    elif issue.get("screenshot"):
        b64 = img_to_base64(issue["screenshot"])
        screenshot_html = f'<img src="data:image/png;base64,{b64}" alt="{issue_id}: funnel context with the issue outlined in red">'

    if not issue.get("evidence_pairs"):
        text_html = build_replacement_blocks(issue)

    return f"""
    <div class="card" data-pages="{feedback_pages(issue)}">
        <div class="explanation">
            <span class="badge">{issue_id}</span>
            <span class="type-label">{type_label}</span>
            {location_html}
            <p>{desc}</p>
        </div>
        {screenshot_html}
        {text_html}
    </div>"""


def generate(issues_file: str, output: str, title: str = "Funnel Review", draft: bool = False) -> str:
    """Generate the approved interactive design through the standard publish path."""
    try:
        from .feedback_presentation import render_report
    except ImportError:
        from feedback_presentation import render_report
    data = json.loads(Path(issues_file).read_text(encoding="utf-8"))
    if not draft:
        validate_review_coverage(data)
    page_html = render_report(data, title, draft, replacements_by_evidence,
                              page_scope_summary(data) + " " + offer_scope_summary(data))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(page_html, encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description="Generate HTML feedback page from issues JSON")
    parser.add_argument("--issues-file", required=True, help="Path to the issues JSON file")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--title", default="Funnel Review", help="Page title")
    parser.add_argument("--draft", action="store_true",
                        help="Render a clearly labeled incomplete preview; never deliver as a finished review")
    args = parser.parse_args()

    result = generate(args.issues_file, args.output, args.title, draft=args.draft)
    print(json.dumps({"output": result}))


if __name__ == "__main__":
    main()
