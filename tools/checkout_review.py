"""Market-specific checkout completion contracts; reviewers judge captured facts."""
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from .review_coverage import check_result
    from .review_io import file_hash, verify_files
except ImportError:
    from review_coverage import check_result
    from review_io import file_hash, verify_files

REVIEW_POLICY_VERSION = 3
DUTCH_CHECKOUT_SCOPE = 'dutch_checkout'
CHECKOUT_REVIEW_CHECKS = {
    'checkout_review_language': 'Every review heading, body and review UI is localized',
    'checkout_review_dates': 'Every displayed review date is 0–20 days before capture',
    'checkout_review_names': 'Localized reviewer names fit their apparent age',
    'checkout_faq': 'All FAQ questions and expanded answers match this product',
    'checkout_guarantee': 'All checkout guarantee brands and day counts match our funnel',
    'checkout_ideal': 'iDEAL visibly loaded in the actual payment options',
    'checkout_bancontact': 'Bancontact visibly loaded in the actual payment options',
}
SWEDISH_OFFER_CHECKS = {'offer_checkout_handoff', 'checkout_offer_price'}


SWEDISH_NAMES = {'sweden', 'sverige'}
DUTCH_NAMES = {'netherlands', 'the netherlands', 'nederland', 'holland', 'nl/be', 'netherlands and belgium',
               'nederland en belgie', 'nederland en belgië', 'netherlands & belgium', 'nederland & belgie',
               'nederland & belgië'}
BELGIUM_NAMES = {'belgium', 'belgie', 'belgië', 'belgique', 'belgien'}
DUTCH_LANGUAGES = {'dutch', 'nederlands', 'flemish', 'vlaams'}


def _name(value):
    return ' '.join(str(value or '').casefold().split())


def is_swedish_market(meta):
    country = _name(meta.get('country'))
    return (country.upper() in {'SE', 'SWE'} or country in SWEDISH_NAMES or
            _name(meta.get('target_market')) in SWEDISH_NAMES)


def validate_swedish_offers(meta, finding_ids):
    """Require observed clicks and distinct resulting checkout states for every offer."""
    filename = meta.get('swedish_offer_checks_file')
    if not filename:
        raise ValueError('Swedish reviews require completed swedish_offer_checks_file')
    record = json.loads(Path(filename).read_text(encoding='utf-8'))
    pages = {p['page']: p for p in meta.get('pages', []) if p.get('side') == 'ours' and p.get('page') in {'advertorial', 'product'}}
    bindings = record.get('source_manifest_sha256', {})
    if set(bindings) != set(pages) or any(bindings[name] != file_hash(p['manifest']) for name, p in pages.items()):
        raise ValueError('Swedish offer checks must bind both current source-page manifests')
    inventory = record.get('inventory', {})
    check_result(dict(inventory, id='offer_button_inventory'), finding_ids, scope='swedish_offers')
    rows = record.get('offers', [])
    ids = [r.get('id') for r in rows]
    if (not rows or any(not i for i in ids) or len(set(ids)) != len(ids) or
            set(inventory.get('button_ids', [])) != set(ids)):
        raise ValueError('Every inventoried Swedish offer button/state needs one unique result')
    destinations = set()
    for row in rows:
        check_result(row, finding_ids, scope='swedish_offers')
        if row.get('page') not in pages or not row.get('location') or not row.get('action'):
            raise ValueError('Offer tests require source page, exact location and performed click action')
        source = json.loads(Path(pages[row['page']]['manifest']).read_text())
        verify_files(Path(pages[row['page']]['manifest']).parent, source.get('files'))
        source_files = source.get('files', {})
        evidence = row.get('source_evidence', [])
        if not evidence or any(p not in source_files for p in evidence) or not any(Path(p).suffix.lower() == '.png' for p in evidence):
            raise ValueError('Offer tests require hash-bound source screenshot evidence')
        # A proved dead button is a completed defect, not an invented checkout.
        if row.get('checkout_loaded') is not True:
            if row['status'] != 'issue' or row.get('outcome') not in {'dead_button', 'navigation_error'}:
                raise ValueError('An untested/unloaded checkout cannot pass an offer test')
            continue
        path = Path(row.get('checkout_manifest', ''))
        if not path.is_file() or row.get('checkout_manifest_sha256') != file_hash(path):
            raise ValueError('Each offer needs its own bound checkout-state manifest')
        capture = json.loads(path.read_text())
        if capture.get('status') != 'complete' or capture.get('page') != 'checkout':
            raise ValueError('Offer destination must have a complete checkout capture')
        verify_files(path.parent, capture.get('files'))
        handoff = capture.get('offer_handoff', {})
        if (handoff.get('source_url') != pages[row['page']]['url'] or
                (handoff.get('selectors') or [handoff.get('selector')]) != (row.get('selectors') or [row.get('selector')]) or handoff.get('action') != 'click' or
                handoff.get('source_image') not in capture['files']):
            raise ValueError('Checkout evidence must preserve the actual source-button click')
        if path.resolve() in destinations:
            raise ValueError('Each button/state requires its own clicked checkout capture')
        destinations.add(path.resolve())
        screenshots = row.get('checkout_evidence', [])
        if (not screenshots or any(p not in capture['files'] for p in screenshots) or
                not any(Path(p).suffix.lower() == '.png' for p in screenshots)):
            raise ValueError('Offer tests require captured checkout screenshot evidence')
        if not row.get('actual_url') or row['actual_url'] != capture.get('resolved_url', capture.get('url')):
            raise ValueError('Offer destination URL must match the captured checkout state')
        if row['status'] != 'pass':
            continue
        if row.get('correct_destination') is not True:
            raise ValueError('A wrong checkout destination cannot pass')
        presented, actual = row.get('presented', {}), row.get('checkout', {})
        for values in (presented, actual):
            if (not values.get('product') or not values.get('variant') or values.get('currency') != 'SEK' or
                    type(values.get('quantity')) is not int or values['quantity'] <= 0 or
                    type(values.get('offer_total_minor')) is not int or values['offer_total_minor'] < 0):
                raise ValueError('Offer comparison needs product, variant, quantity, SEK and total in minor units')
        if any(presented[k] != actual[k] for k in ('product', 'variant', 'quantity', 'currency', 'offer_total_minor')):
            raise ValueError('Wrong selected offer or mismatched checkout price cannot pass')
        shipping = actual.get('shipping_minor')
        other = actual.get('other_charges_minor', 0)
        if (type(shipping) is not int or shipping < 0 or
                type(other) is not int or other < 0 or
                type(actual.get('payable_total_minor')) is not int or
                actual['payable_total_minor'] != actual['offer_total_minor'] + shipping + other):
            raise ValueError('Checkout payable total must reconcile with the offer and shipping')
        if 'shipping_minor' in presented and shipping != presented['shipping_minor']:
            raise ValueError('Advertised shipping must match checkout')
        if not row.get('shipping_reason'):
            raise ValueError('Record the displayed shipping terms and how they explain the total')


def is_dutch_market(meta):
    """Codes or country names (any case); Belgium counts only with Dutch as target language."""
    country = str(meta.get('country', '')).upper().replace('/', '').replace('-', '').replace(' ', '')
    names = {_name(meta.get('country')), _name(meta.get('target_market'))}
    language = _name(meta.get('target_language')).replace('_', '-')
    dutch_language = language in DUTCH_LANGUAGES or language.split('-')[0] == 'nl'
    return (country in {'NL', 'NLBE', 'BENL', 'NLD'} or bool(names & DUTCH_NAMES) or
            ((country in {'BE', 'BEL'} or bool(names & BELGIUM_NAMES)) and dutch_language))


def check_template_fields(name):
    """Pending observation scaffolding; none of these defaults constitutes a pass."""
    if name not in CHECKOUT_REVIEW_CHECKS:
        return {}
    fields = {'evidence_files': []}
    if name == 'checkout_review_dates':
        fields['reviews'] = []
    elif name in {'checkout_review_language', 'checkout_review_names'}:
        fields['review_ids'] = []
    elif name == 'checkout_faq':
        fields['faq_ids'] = []
    elif name == 'checkout_guarantee':
        fields.update(expected_brand=None, expected_days=None, observations=[])
    else:
        fields.update(visible=None, loaded=None, location='payment_options')
    return fields


def review_date_status(value, captured_at):
    """Compare normalized source dates with the Dutch calendar date of capture."""
    try:
        captured = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
        if captured.tzinfo is None:
            raise ValueError('Capture timestamp must include its timezone')
        observed = date.fromisoformat(value)
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError('Review dates need YYYY-MM-DD and a timezone-aware captured_at') from error
    age = (captured.astimezone(ZoneInfo('Europe/Amsterdam')).date() - observed).days
    return {'age_days': age, 'status': 'future' if age < 0 else 'stale' if age > 20 else 'recent'}


def validate_dutch_checkout(entry, capture, manifest_path, finding_ids, meta=None):
    """Require specific observed results, without granting an automatic visual pass."""
    if not entry.get('checks_file'):
        raise ValueError('Dutch checkout requires a completed checks_file')
    record = json.loads(Path(entry['checks_file']).read_text(encoding='utf-8'))
    if record.get('manifest_sha256') != file_hash(manifest_path):
        raise ValueError('Dutch checkout checks belong to a different capture manifest')
    rows = record.get('checks', [])
    if not isinstance(rows, list) or any(not isinstance(c, dict) for c in rows):
        raise ValueError('Dutch checkout checks must be a list of check rows')
    capture_ids = {c.get('id') for c in capture.get('required_checks', [])} | set(CHECKOUT_REVIEW_CHECKS)
    checks = {}
    for row in rows:
        identifier = row.get('id')
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('Every Dutch checkout check row needs an id')
        if identifier not in capture_ids:
            raise ValueError(f'Unknown Dutch checkout check id: {identifier}')
        if identifier in checks:
            raise ValueError(f'Duplicate Dutch checkout check id: {identifier}')
        checks[identifier] = row
    if not CHECKOUT_REVIEW_CHECKS.keys() <= checks.keys():
        raise ValueError('Dutch checkout requires all seven checks exactly once')
    for name in CHECKOUT_REVIEW_CHECKS:
        check = checks[name]
        check_result(check, finding_ids, scope='ours/checkout')
        # Evidence must belong to this packet, including payment-option frames.
        evidence = check.get('evidence_files', [])
        if not evidence or any(p not in capture.get('files', {}) for p in evidence):
            raise ValueError(f'{name} requires hash-bound evidence_files from its capture')
        if not any(Path(p).suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} for p in evidence):
            raise ValueError(f'{name} requires visible screenshot evidence')
    dates = checks['checkout_review_dates']
    reviews = dates.get('reviews')
    if not isinstance(reviews, list):
        raise ValueError('Dutch checkout needs a dated review inventory, or an evidenced missing-review finding')
    if not reviews and not (dates.get('reviews_absent') is True and dates['status'] == 'issue'):
        raise ValueError('An empty review inventory requires an evidenced missing-review finding')
    seen = set()
    for review in reviews:
        identifier = review.get('id')
        if not identifier or identifier in seen or not review.get('displayed_date'):
            raise ValueError('Review inventory needs unique IDs and the literal displayed_date')
        seen.add(identifier)
        if review.get('date') is None:
            if dates['status'] != 'issue':
                raise ValueError('Missing/unreadable review date needs an evidenced issue')
        elif review_date_status(review['date'], capture.get('captured_at', ''))['status'] != 'recent' and dates['status'] != 'issue':
            raise ValueError('Stale or future review dates cannot pass the 20-day check')
    for name in ('checkout_review_language', 'checkout_review_names'):
        if set(checks[name].get('review_ids', [])) != seen:
            raise ValueError(f'{name} must cover every review ID in the date inventory')
        if not seen and checks[name]['status'] != 'issue':
            raise ValueError('Missing reviews cannot pass language or name checks')
    faq = checks['checkout_faq']
    captured_faqs = {s['state_id'] for s in capture.get('faq_states', [])}
    if set(faq.get('faq_ids', [])) != captured_faqs:
        raise ValueError('Checkout FAQ check must cover every expanded captured answer')
    if not captured_faqs and faq['status'] == 'pass':
        raise ValueError('An uncaptured checkout FAQ cannot pass')
    guarantee = checks['checkout_guarantee']
    if guarantee['status'] == 'pass':
        expected_days = guarantee.get('expected_days')
        expected_brand = guarantee.get('expected_brand')
        observations = guarantee.get('observations', [])
        if not isinstance(expected_days, int) or isinstance(expected_days, bool) or expected_days <= 0 or not expected_brand or not observations:
            raise ValueError('Guarantee pass needs the funnel reference brand/days and every observed checkout occurrence')
        normalize = lambda s: str(s).casefold().replace('™', '').replace('®', '').strip()
        if meta and meta.get('brand_name') and normalize(expected_brand) != normalize(meta['brand_name']):
            raise ValueError('Guarantee reference brand must match the funnel brand')
        for observed in observations:
            if (not observed.get('location') or not (observed.get('brand') or observed.get('days')) or
                    (observed.get('days') is not None and observed['days'] != expected_days) or
                    (observed.get('brand') and normalize(observed['brand']) != normalize(expected_brand))):
                raise ValueError('A mismatched checkout guarantee cannot pass')
    for name in ('checkout_ideal', 'checkout_bancontact'):
        result = checks[name]
        if result['status'] == 'pass' and (result.get('visible') is not True or result.get('loaded') is not True or result.get('location') != 'payment_options'):
            raise ValueError(f'{name} pass requires visible, loaded actual payment_options')
