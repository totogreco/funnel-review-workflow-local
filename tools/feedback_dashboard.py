"""Render the public feedback directory from staged review receipts."""

import json
import re
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path


BUILDER_COLORS_FILE = Path(__file__).resolve().parents[1] / "config/funnel_builder_colors.json"


def _builder_colors():
    """Sheet dropdown swatches, shared by sidebar and section avatars."""
    colors = json.loads(BUILDER_COLORS_FILE.read_text())
    for palette in colors.values():
        if not all(re.fullmatch(r"#[0-9a-fA-F]{6}", palette.get(key, ""))
                   for key in ("background", "text")):
            raise ValueError("Builder colours must be six-digit hex values")
    return {name.strip().casefold(): palette for name, palette in colors.items()}


# Country flags shared with the dashboard's Check the queue table (tools/dashboard/app.py).
FLAGS = {
    "NL": ("Netherlands", '<path fill="#ae1c28" d="M0 0h30v7H0z"/><path fill="#fff" d="M0 7h30v6H0z"/><path fill="#21468b" d="M0 13h30v7H0z"/>'),
    "BE": ("Belgium", '<path fill="#000" d="M0 0h10v20H0z"/><path fill="#fdda24" d="M10 0h10v20H10z"/><path fill="#ef3340" d="M20 0h10v20H20z"/>'),
    "SE": ("Sweden", '<path fill="#006aa7" d="M0 0h30v20H0z"/><path fill="#fecc00" d="M9 0h4v20H9z"/><path fill="#fecc00" d="M0 8h30v4H0z"/>'),
}


def market_codes(country):
    """NLBE is the Netherlands and Belgium; every other value is one code."""
    return ("NL", "BE") if country == "NLBE" else (country,)


def market_badge(country):
    """Render flags with accessible names and no visible country codes."""
    images = []
    for code in market_codes(country):
        if code in FLAGS:
            name, paths = FLAGS[code]
            images.append(f'<svg class="country-flag" viewBox="0 0 30 20" role="img" aria-label="{name} flag">{paths}</svg>')
        elif re.fullmatch(r"[A-Z]{2}", code):
            flag_code = "GB" if code == "UK" else code
            emoji = "".join(chr(127397 + ord(letter)) for letter in flag_code)
            images.append(f'<span class="flag-emoji" role="img" aria-label="{escape(code)} flag">{emoji}</span>')
    return f'<span class="market"><span class="market-flags">{"".join(images)}</span></span>'


def _date(value):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date.strftime("%d %b %Y"), date.date().isoformat()
    except (ValueError, TypeError, AttributeError):
        return "Not recorded", ""


def render_dashboard(site_dir, link_prefix=""):
    """Only expose presentation metadata; receipts remain private."""
    reviews = []
    for directory in sorted(Path(site_dir).iterdir()):
        if (not directory.is_dir() or directory.name.startswith(".")
                or not (directory / "index.html").is_file()):
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", directory.name):
            raise ValueError("Invalid review directory name")
        receipt = directory / "receipt.json"
        info = json.loads(receipt.read_text()) if receipt.exists() else {}
        display_date, sort_date = _date(info.get("published_at", ""))
        count = info.get("issue_count")
        reviews.append({
            "slug": directory.name,
            "builder": str(info.get("funnel_builder") or "Unassigned").strip() or "Unassigned",
            "product": str(info.get("brand_name") or info.get("title") or directory.name),
            "country": str(info.get("country") or "—").upper(),
            "funnel_id": str(info.get("funnel_id") or ""),
            "count": count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None,
            "date": display_date, "sort_date": sort_date,
            "draft": bool(info.get("draft", False)),
        })
    groups = defaultdict(list)
    for review in reviews:
        groups[review["builder"]].append(review)
    builders = sorted(groups, key=str.casefold)
    colors = _builder_colors()
    nav = []
    sections = []
    for i, builder in enumerate(builders):
        key = f"builder-{i}"
        name = escape(builder)
        initial = escape("".join(word[0] for word in builder.split()[:2]).upper())
        palette = colors.get(builder.casefold())
        avatar_style = (f' style="background:{palette["background"]};color:{palette["text"]}"'
                        if palette else "")
        panel_style = (f' style="--builder-color:{palette["background"]}"' if palette else "")
        nav.append(f'<button class="builder-filter"{panel_style} data-builder="{key}" aria-pressed="false">'
                   f'<span class="avatar small"{avatar_style}>{initial}</span><span class="builder-name">{name}</span>'
                   f'<span class="nav-count">{len(groups[builder])}</span></button>')
        rows = []
        for review in sorted(groups[builder], key=lambda r: (r["sort_date"], r["slug"]), reverse=True):
            slug = review["slug"]
            product = escape(review["product"])
            country = escape(review["country"])
            query = escape(" ".join(str(review[k]) for k in ("product", "builder", "country", "slug", "funnel_id")), quote=True)
            findings = "Not recorded" if review["count"] is None else f'{review["count"]} finding' + ("" if review["count"] == 1 else "s")
            badge = '<span class="draft">Draft</span>' if review["draft"] else ""
            rows.append(f'''<article class="review-row" data-search="{query}" data-product="{product}" data-date="{review['sort_date']}">
              <div class="product-cell"><div class="product-info">
                <div class="product-name">{product}{badge}</div></div></div>
              <div class="market-cell">{market_badge(review['country'])}</div>
              <div class="finding-cell">{findings}</div>
              <time class="date-cell" datetime="{review['sort_date']}">{review['date']}</time>
              <a class="open-link" href="{link_prefix}/{slug}/" aria-label="Click here to open the feedback for {product}, {country}, by {name}">Click here to open the feedback <span aria-hidden="true">→</span></a>
            </article>''')
        sections.append(f'''<section class="builder-group"{panel_style} data-builder="{key}" aria-labelledby="{key}-heading">
          <div class="group-heading"><span class="avatar"{avatar_style}>{initial}</span><h2 id="{key}-heading">{name}</h2>
          <span class="group-count">{len(rows)} review{'s' if len(rows) != 1 else ''}</span></div>
          <div class="column-headings" aria-hidden="true"><span>Funnel / product</span><span>Country</span><span>Feedback</span><span>Published</span><span></span></div>
          <div class="review-list">{''.join(rows)}</div></section>''')
    countries = {r["country"] for r in reviews if r["country"] != "—"}
    values = {
        "__STYLES__": (Path(__file__).parent / "templates/feedback_dashboard.css").read_text(encoding="utf-8"),
        "__TOTAL__": str(len(reviews)),
        "__BUILDERS__": str(len(builders)),
        "__COUNTRIES__": str(len(countries)),
        "__BUILDER_NAV__": "".join(nav),
        "__GROUPS__": "".join(sections),
        "__INITIAL_EMPTY__": "" if not reviews else "hidden",
    }
    # A single substitution prevents user text containing a placeholder from
    # being interpreted as template instructions on a subsequent pass.
    return re.sub(r"__[A-Z_]+__", lambda m: values.get(m.group(), m.group()), TEMPLATE)


TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>Funnel feedback — Review dashboard</title>
<style>
__STYLES__
</style>
</head>
<body>
<a href="#main" class="skip">Skip to feedback</a>
<main id="main" class="content">
    <header class="page-heading"><div><h1>Funnel feedback</h1><p class="subtitle">Find a funnel. Open its feedback. Know what to fix.</p></div>
      <div class="summary" aria-label="Library totals"><div><strong>__TOTAL__</strong>Reviews</div><div><strong>__BUILDERS__</strong>Builders</div><div><strong>__COUNTRIES__</strong>Markets</div></div>
    </header>
    <p class="workspace-label" id="builders-label">Funnel builders</p>
    <nav class="builder-filters" aria-labelledby="builders-label">
      <button class="builder-filter" data-builder="all" aria-pressed="true"><span class="all-icon" aria-hidden="true">▦</span><span class="builder-name">All builders</span><span class="nav-count">__TOTAL__</span></button>
      __BUILDER_NAV__
    </nav>
    <div class="toolbar">
      <div class="search"><label class="sr-only" for="search">Search funnels, builders, countries or IDs</label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><input id="search" type="search" placeholder="Search funnels, builders, countries…" autocomplete="off"></div>
      <label class="sort" for="sort">Sort by <select id="sort"><option value="latest">Newest first</option><option value="name">Product A–Z</option><option value="oldest">Oldest first</option></select></label>
    </div>
    <div class="results-line"><span id="results" role="status" aria-live="polite">Showing <strong>__TOTAL__</strong> of __TOTAL__ reviews</span><button class="reset" id="reset" hidden>Clear filters</button></div>
    <div id="groups">__GROUPS__</div>
    <div class="empty" id="empty" __INITIAL_EMPTY__><div class="empty-icon" aria-hidden="true">⌕</div><h2 id="empty-title">No feedback published yet</h2><p id="empty-description">Published funnel reviews will appear here.</p><button id="empty-reset" hidden>Clear filters</button></div>
    <p class="footer">New reviews appear here when published.</p>
</main>
<script>
(() => {
  const buttons = [...document.querySelectorAll('.builder-filter')];
  const groups = [...document.querySelectorAll('.builder-group')];
  const search = document.getElementById('search');
  const total = document.querySelectorAll('.review-row').length;
  let selected = 'all';
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  function filter() {
    const terms = normalize(search.value).split(/\s+/).filter(Boolean);
    let visible = 0;
    groups.forEach(group => {
      let count = 0;
      group.querySelectorAll('.review-row').forEach(row => {
        const matches = (selected === 'all' || group.dataset.builder === selected) && terms.every(term => normalize(row.dataset.search).includes(term));
        row.hidden = !matches;
        if (matches) count++;
      });
      group.hidden = count === 0;
      group.querySelector('.group-count').textContent = `${count} review${count === 1 ? '' : 's'}`;
      visible += count;
    });
    document.getElementById('results').textContent = `Showing ${visible} of ${total} reviews`;
    document.getElementById('empty').hidden = visible !== 0;
    const filtered = selected !== 'all' || terms.length > 0;
    document.getElementById('reset').hidden = !filtered;
    document.getElementById('empty-reset').hidden = !filtered;
    document.getElementById('empty-title').textContent = total ? 'No matching reviews' : 'No feedback published yet';
    document.getElementById('empty-description').textContent = total ? 'Try another product, builder or country.' : 'Published funnel reviews will appear here.';
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.builder === selected)));
  }
  buttons.forEach(button => button.addEventListener('click', () => { selected = button.dataset.builder; filter(); }));
  search.addEventListener('input', filter);
  function reset() { selected = 'all'; search.value = ''; filter(); document.querySelector('.builder-filters').scrollLeft = 0; search.focus(); }
  document.getElementById('reset').addEventListener('click', reset);
  document.getElementById('empty-reset').addEventListener('click', reset);
  document.getElementById('sort').addEventListener('change', event => {
    groups.forEach(group => {
      const list = group.querySelector('.review-list');
      [...list.children].sort((a, b) => {
        if (event.target.value === 'name') return a.dataset.product.localeCompare(b.dataset.product);
        const dateOrder = a.dataset.date.localeCompare(b.dataset.date);
        return (event.target.value === 'oldest' ? dateOrder : -dateOrder) || a.dataset.product.localeCompare(b.dataset.product);
      }).forEach(row => list.appendChild(row));
    });
  });
  filter();
})();
</script>
</body>
</html>
'''
