"""Reusable presentation for funnel findings; does not perform review judgments.

The agent supplies feedback_type, concise instructions and verified locations.
Legacy findings remain readable without modifying their saved review evidence.
"""
import base64
import html
import re
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

TEMPLATES = Path(__file__).with_name('templates')
TYPES = {
    'find_replace': ('blue', '⇄', 'Find & replace'),
    'image_edit': ('purple', '▧', 'Edit image / section'),
    'missing_content': ('red', '＋', 'Add missing content'),
    'price_offer': ('orange', '€', 'Price or offer'),
}
LABELS = {'advertorial': 'Advertorial', 'product': 'Product page', 'checkout': 'Checkout'}


def esc(value):
    return html.escape(str(value))


def safe_url(value):
    if not value:
        return ''
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError('Funnel links must be absolute http(s) URLs')
    return value


def feedback_type(issue):
    explicit = issue.get('feedback_type')
    if explicit is not None and explicit not in TYPES:
        raise ValueError(f'Unknown feedback_type: {explicit}')
    # Category denotes the builder's work area, not merely a word like "price".
    # All checkout work belongs together, including images, FAQs and reviews.
    if issue.get('page') == 'checkout' or issue.get('offer_context') in {'product_selection', 'cart', 'checkout'}:
        return 'price_offer'
    if explicit is not None:
        if explicit == 'price_offer' and (issue.get('offer_context') == 'editorial' or issue.get('page') == 'advertorial'):
            return 'find_replace'
        return explicit
    if issue.get('offer_context') == 'editorial':
        return 'find_replace'
    # Backward compatibility only. New reviews set this deliberately.
    replacements = issue.get('replacements') or [{'find': issue.get('wrong_text', ''), 'replace': issue.get('correct_text', '')}]
    if issue.get('check', '').startswith('missing_') or any(not r.get('find') and r.get('replace') for r in replacements):
        return 'missing_content'
    if issue.get('category') == 'visual':
        return 'image_edit'
    if issue.get('page') == 'product' and issue.get('check') in {'price_and_discount', 'offer_presentation', 'pricing_consistency', 'offer_checkout_handoff', 'checkout_offer_price'}:
        return 'price_offer'
    if issue.get('evidence_pairs') and not any(r.get('find') or r.get('replace') for r in replacements):
        return 'missing_content'
    return 'find_replace'


def scopes(item, fallback='advertorial'):
    pages = item.get('pages', [item.get('page', fallback)])
    if not isinstance(pages, list) or any(p not in LABELS for p in pages):
        raise ValueError('Feedback pages must identify advertorial, product or checkout')
    if item.get('page') and item['page'] not in pages:
        pages = [item['page'], *pages]
    # The product selector includes existing checkout price/offer findings.
    return ' '.join(dict.fromkeys('product' if p == 'checkout' else p for p in pages))


def image(path, alt):
    if not path:
        return ''
    file = Path(path)
    mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}.get(file.suffix.lower())
    if not mime:
        raise ValueError(f'Unsupported screenshot format: {file.suffix}')
    encoded = base64.b64encode(file.read_bytes()).decode('ascii')
    return f'<img src="data:{mime};base64,{encoded}" alt="{esc(alt)}">'


def copy_field(label, value, kind):
    return (f'<div class="field {kind}"><div class="field-head">'
            f'{"<span class=label>" + esc(label) + "</span>" if label else ""}'
            f'<button class="copy" aria-label="Copy {kind} text" data-copy="{esc(value)}">COPY</button>'
            f'</div><p class="value">{esc(value)}</p></div>')


def copy_fields(replacements, kind, show_legacy_locations=True):
    result = []
    for r in replacements:
        old, new = r.get('find', ''), r.get('replace', '')
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError('Replacement find/replace values must be strings')
        if old == new:
            continue
        # New cards already have a location heading and an optional precise note.
        # Preserve legacy location hints only when that presentation is absent.
        location = f'<p class="note">{esc(r["location"])}</p>' if show_legacy_locations and r.get('location') else ''
        if not old:
            result.append(location + '<div class="comparison-copy">' + copy_field('', new, 'addition') + '</div>')
        else:
            find_label = 'Text in the image' if kind == 'image_edit' else '1. Find this'
            replace_label = 'New image text' if kind == 'image_edit' else '2. Replace with this'
            replacement = copy_field(replace_label, new, 'replace') if new else '<p class="delete-note">Delete this text.</p>'
            result.append(location + '<div class="replacement-pair">' + copy_field(find_label, old, 'find') + replacement + '</div>')
    return ''.join(result)


def page_text(meta, page):
    entry = next((p for p in meta.get('pages', []) if p.get('side') == 'ours' and p.get('page') == page), {})
    if not entry.get('manifest'):
        return ''
    import json
    manifest_path = Path(entry['manifest'])
    manifest = json.loads(manifest_path.read_text())
    text_path = manifest_path.parent / manifest.get('text_file', '')
    return re.sub(r'\s+', ' ', text_path.read_text()) if text_path.is_file() else ''


def location_link(issue, pair, replacements, meta, texts):
    page = pair.get('page', issue.get('page', 'advertorial'))
    entry = next((p for p in meta.get('pages', []) if p.get('side') == 'ours' and p.get('page') == page), {})
    url = pair.get('target_url') or (issue.get('target_url') if page == issue.get('page') else '') or entry.get('url')
    if not url and page == 'advertorial':
        url = meta.get('our_url', '')
    if pair.get('target_url') and entry.get('url') and pair['target_url'] != entry['url']:
        raise ValueError('Evidence target_url does not match its declared page')
    safe_url(url)
    if not url:
        return '', ''
    # Never invent a DOM selector or fragment from a section number. An explicit
    # anchor is author-verified; fallback FIND must occur uniquely in capture text.
    anchor = pair.get('target_anchor', '')
    if anchor and not isinstance(anchor, str):
        raise ValueError('target_anchor must be an exact observed text string')
    text = texts.setdefault(page, page_text(meta, page)) if page not in texts else texts[page]
    if not anchor and replacements:
        candidate = replacements[0].get('find', '')
        normalized = re.sub(r'\s+', ' ', candidate)
        if normalized and text.count(normalized) == 1:
            anchor = candidate
    normalized = re.sub(r'\s+', ' ', anchor)
    if anchor and (not text or text.count(normalized) == 1):
        parsed = urlsplit(url)
        fragment = ':~:text=' + quote(anchor, safe='').replace('-', '%2D')
        url = urlunsplit(parsed._replace(fragment=fragment))
        hint = pair.get('open_hint') or 'Open this text in the live funnel. Expand the FAQ or select the matching offer if needed; loading content can shift the position.'
    else:
        hint = 'Open the funnel; use the marked screenshot to locate this change.'
    return url, hint


def link(url, label, css='open', hint=''):
    return (f'<a class="{css}" href="{esc(safe_url(url))}" title="{esc(hint)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)} ↗</a>') if url else ''


def default_identifier(index, taken, prefix='T'):
    """T{n} for a finding without an explicit id, never colliding with an explicit one."""
    candidate, n = f'{prefix}{index}', 2
    while candidate in taken:
        candidate, n = f'{prefix}{index}-{n}', n + 1
    taken.add(candidate)
    return candidate


def render_issue(issue, index, meta, group_replacements, texts, decision=False, taken=None):
    important_note = issue.get('important_note', '')
    if not isinstance(important_note, str):
        raise ValueError('Important note must be a string')
    notice = f'<p class="important-note"><strong>{esc(important_note)}</strong></p>' if important_note.strip() else ''
    kind = feedback_type(issue)
    color = 'all' if decision else TYPES[kind][0]
    identifier = str(issue.get('id') or default_identifier(index, set() if taken is None else taken, 'D' if decision else 'T'))
    page = issue.get('page', 'advertorial')
    pairs = issue.get('evidence_pairs')
    if pairs:
        groups = group_replacements(issue)
    else:
        pairs = [{'id': 'A', 'marker': 'A', 'target_screenshot': issue.get('screenshot'),
                  'source_screenshot': issue.get('source_screenshot'), 'location': issue.get('location', '')}]
        normalized = {**issue, 'evidence_pairs': pairs}
        groups = group_replacements(normalized)
    # A finding is shown wherever its own page or any of its evidence is. A
    # single-page finding keeps all its cards together under that union, so the
    # panel and its cards never appear under different page filters. Genuinely
    # cross-page findings keep each card on its own declared page.
    own_pages = scopes(issue)
    cross_page = len(own_pages.split()) > 1
    pair_scopes = [scopes(pair, page) for pair in pairs]
    pages = ' '.join(dict.fromkeys(own_pages.split() + [p for scope in pair_scopes for p in scope.split()]))
    gallery = (issue.get('check') == 'missing_comments' and len(pairs) > 1
               and all(p.get('source_screenshot') and not p.get('target_screenshot') for p in pairs))
    cards, first_url = [], ''
    for n, (pair, replacements) in enumerate(zip(pairs, groups)):
        if issue.get('evidence_pairs') and not (pair.get('source_screenshot') or pair.get('target_screenshot')):
            raise ValueError('Each evidence group requires a source or target screenshot')
        marker_parts = str(pair.get('marker') or '').split(' · ', 1)
        marker = marker_parts[0] or chr(65 + n)
        location = pair.get('location') or (marker_parts[1] if len(marker_parts) > 1 else '') or pair.get('target_caption') or pair.get('source_caption') or LABELS[page]
        instruction = pair.get('instruction', '')
        if not isinstance(instruction, str):
            raise ValueError('Evidence instruction must be a string')
        note = pair.get('note') or instruction
        url, hint = location_link(issue, pair, replacements, meta, texts)
        first_url = first_url or url
        done = '' if decision else f'<label class="done"><input type="checkbox" aria-label="Mark {esc(location)} done"><span>Done</span></label>'
        header = f'<div class="card-head"><div class="place"><span class="number" data-marker="{esc(marker)}">{esc(marker)}</span><h3>{esc(location)}</h3></div><div class="card-actions">{link(url, "Open here", "open-here", hint)}{done}</div></div>'
        copies = copy_fields(replacements, kind, show_legacy_locations=not pair.get('location'))
        target = image(pair.get('target_screenshot'), f'{identifier} {marker}: {pair.get("target_caption") or "Our funnel — " + location}')
        # Hide irrelevant competitor-language imagery for literal replacements.
        comparison = decision or kind == 'missing_content' or pair.get('display') == 'comparison' or not target
        if gallery:
            source = image(pair['source_screenshot'], f'{identifier} {marker}: {location}')
            content = f'<figure class="shot">{source}<button class="preview">Click here to preview</button></figure>'
        elif comparison:
            source = image(pair.get('source_screenshot'), f'{identifier} {marker}: {pair.get("source_caption") or "Competitor — " + location}')
            figures = (f'<figure class="competitor"><figcaption>{esc(pair.get("source_label") or ("FIRST LOCATION" if decision else "COMPETITOR"))}</figcaption>{source}</figure>' if source else '')
            figures += (f'<figure class="ours"><figcaption>{esc(pair.get("target_label") or ("SECOND LOCATION" if decision else "OUR FUNNEL"))}</figcaption>{target}</figure>' if target else '')
            content = copies + (f'<div class="comparison{" single" if not source or not target else ""}">{figures}</div>' if figures else '')
        else:
            shot = f'<figure class="shot">{target}<button class="preview" aria-label="Click here to preview: {esc(location)}">Click here to preview</button></figure>' if target else ''
            content = f'<div class="work"><div class="fields">{copies}</div>{shot}</div>' if copies else f'<div class="image-only">{shot}</div>'
        # Pair scope is mandatory for genuinely cross-page evidence; never show
        # one page's edits on another. Single-page findings use the panel scope.
        pair_scope = pair_scopes[n] if cross_page else pages
        cards.append(f'<section class="card" data-pages="{pair_scope}" data-evidence-id="{esc(pair.get("id", marker))}">{header}'
                     f'{"<p class=note>" + esc(note) + "</p>" if note and note != issue.get("description") else ""}{content}</section>')
    if cross_page and any(not p.get('page') for p in pairs):
        raise ValueError('Cross-page findings require a page on every evidence pair')
    title = issue.get('question', '') if decision else issue.get('feedback', issue.get('description', ''))
    label = 'Owner decision' if decision else ' + '.join(LABELS[p] for p in issue.get('pages', [page]))
    progress = '' if decision else f'<div class="progress-row"><div class="track" role="progressbar" aria-label="Completed edits" aria-valuemin="0" aria-valuemax="{len(cards)}" aria-valuenow="0"><div class="fill"></div></div><span class="count" aria-live="polite">0 / {len(cards)} done</span></div>'
    return (f'<section class="panel {color}{" decision" if decision else ""}" data-color="{color}" data-pages="{pages}" id="panel-{esc(identifier)}">'
            f'{notice}<div class="intro"><div><span class="meta">{esc(identifier)} · {esc(label)}</span><h2>{esc(title)}</h2></div>'
            f'{link(first_url, "Open " + LABELS[page].lower())}</div>{progress}<div class="cards{" gallery" if gallery else ""}">{"".join(cards)}</div></section>')


def render_report(data, title, draft, group_replacements, scope_summary):
    meta, texts = data.get('meta', {}), {}
    issues, decisions = data.get('issues', []), data.get('decisions', [])
    ids = [i.get('id') for i in issues + decisions if i.get('id')]
    if len(ids) != len(set(ids)):
        raise ValueError('Finding and decision IDs must be unique')
    taken = set(ids)
    cards = ''.join(render_issue(i, n, meta, group_replacements, texts, taken=taken) for n, i in enumerate(issues, 1))
    # Decisions remain in private review records for coverage and chat delivery.
    # Never render them into the builder report, including hidden content.
    heading = f'{meta.get("brand_name") or "Funnel"} · {meta.get("country") or meta.get("target_market") or "Market not specified"} · {len(issues)} fixes to be done'
    tabs = '<button class="tab all" data-color="all" role="tab" aria-selected="true" tabindex="0">All Feedback</button>'
    for color, icon, label in TYPES.values():
        tabs += f'<button class="tab {color}" data-color="{color}" role="tab" aria-selected="false" tabindex="-1"><span class="icon" aria-hidden="true">{icon}</span>{label}</button>'
    draft_notice = '<p class="draft-warning"><strong>DRAFT — incomplete or unverified review. Not ready for delivery.</strong></p>' if draft else ''
    coverage = '' if draft else scope_summary
    return f'''<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{(TEMPLATES / 'funnel_review.css').read_text()}</style></head>
<body><main>{draft_notice}<header><h1>{esc(heading)}</h1></header>
<nav class="funnel-links" aria-label="Open funnels">{link(meta.get('competitor_url'), 'Competitor funnel')}{link(meta.get('our_url'), 'Our funnel')}</nav>
<div class="page-selector" role="group" aria-label="Funnel page"><button class="page-option" data-page="both" aria-pressed="true">Both pages</button><button class="page-option" data-page="advertorial" aria-pressed="false">Advertorial</button><button class="page-option" data-page="product" aria-pressed="false">Product page</button></div>
<nav class="tabs" role="tablist" aria-label="Feedback categories">{tabs}</nav><div id="panels">{cards}</div><p class="empty" id="empty" hidden>No feedback in this view.</p><p class="scope">{esc(coverage)}</p></main>
<div class="toast" role="status" aria-live="polite"></div><dialog aria-label="Screenshot preview"><div class="dialog-head"><strong id="zoom-title"></strong><button class="close">Close ✕</button></div><img id="zoom" alt=""></dialog>
<script>{(TEMPLATES / 'funnel_review.js').read_text()}</script></body></html>'''
