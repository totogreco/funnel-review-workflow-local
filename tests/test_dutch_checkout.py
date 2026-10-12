"""Dutch checkout completion gates and date boundaries; no live payment calls."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.checkout_review import CHECKOUT_REVIEW_CHECKS, is_dutch_market, is_swedish_market, review_date_status, validate_dutch_checkout
from tools.generate_feedback_page import validate_review_coverage, offer_scope_summary
from tools.review_io import file_hash, write_json


def index_page(entry, **extra):
    """Turn a page fixture into a minimal complete indexed packet with a passed check."""
    path = Path(entry['manifest']); folder = path.parent
    capture = json.loads(path.read_text())
    capture.update(schema_version=2, status='complete', index=capture['text_file'], faq_file=capture['text_file'],
                   files={p.name: file_hash(p) for p in folder.iterdir() if p.name != 'manifest.json'},
                   required_checks=[{'id': 'content_and_visuals'}], **extra)
    write_json(path, capture)
    checks = folder.parent / (folder.name + '-checks.json')
    write_json(checks, {'manifest_sha256': file_hash(path), 'checks': [
        {'id': 'content_and_visuals', 'status': 'pass', 'reason': 'Compared the fixture'}]})
    entry['checks_file'] = str(checks)


class DutchCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pages = []
        for side in ['competitor', 'ours']:
            for page in ['advertorial', 'product']:
                folder = self.root / (side + '_' + page); folder.mkdir()
                for name in ['full.png', 'section.png', 'text.txt']:
                    (folder / name).write_text('Fixture')
                url = f'https://{side}.example/{page}'
                manifest = folder / 'manifest.json'
                write_json(manifest, {'url': url, 'full_page': 'full.png', 'text_file': 'text.txt',
                    'sections': [{'file': 'section.png'}]})
                self.pages.append({'side': side, 'page': page, 'url': url, 'manifest': str(manifest), 'status': 'reviewed'})
                index_page(self.pages[-1])  # Current-policy runs cannot use legacy captures.
        folder = self.root / 'checkout'; folder.mkdir()
        for name in ['full.png', 'text.txt', 'index.json', 'faq.json']:
            (folder / name).write_text('Fixture')
        self.capture = {'schema_version': 2, 'review_policy_version': 2, 'status': 'complete',
            'page': 'checkout', 'scope': 'dutch_checkout', 'url': 'https://ours.example/checkout',
            'captured_at': '2026-10-02T09:00:00+00:00', 'full_page': 'full.png',
            'text_file': 'text.txt', 'index': 'index.json', 'faq_file': 'faq.json',
            'sections': [{'file': 'full.png'}],
            'faq_states': [{'state_id': 'faq-1', 'image': 'full.png', 'index': 'index.json'}],
            'required_checks': [{'id': name} for name in CHECKOUT_REVIEW_CHECKS],
            'files': {p.name: file_hash(p) for p in folder.iterdir()}}
        self.manifest = folder / 'manifest.json'; write_json(self.manifest, self.capture)
        self.entry = {'side': 'ours', 'page': 'checkout', 'scope': 'dutch_checkout', 'url': self.capture['url'],
            'manifest': str(self.manifest), 'checks_file': str(folder / 'checks.json'), 'status': 'reviewed'}
        self.rows = {name: {'id': name, 'status': 'pass', 'reason': 'Inspected the fixture',
                           'evidence_files': ['full.png']} for name in CHECKOUT_REVIEW_CHECKS}
        self.rows['checkout_review_dates']['reviews'] = [
            {'id': 'r1', 'displayed_date': '12 september 2026', 'date': '2026-09-12'}]
        for name in ['checkout_review_language', 'checkout_review_names']:
            self.rows[name]['review_ids'] = ['r1']
        self.rows['checkout_faq']['faq_ids'] = ['faq-1']
        self.rows['checkout_guarantee'].update(expected_brand='Example', expected_days=60,
            observations=[{'location': 'badge', 'brand': None, 'days': 60},
                          {'location': 'paragraph', 'brand': 'Example™', 'days': 60}])
        for name in ['checkout_ideal', 'checkout_bancontact']:
            self.rows[name].update(visible=True, loaded=True, location='payment_options')
        self.data = {'meta': {'country': 'NLBE', 'brand_name': 'Example', 'review_policy_version': 2,
            'pages': self.pages + [self.entry], 'cross_page_checks': {name: {'status': 'pass', 'reason': 'Compared fixture'}
                for name in ['guarantee', 'pricing']}}, 'issues': []}
        self.save_checks()

    def save_checks(self):
        write_json(self.entry['checks_file'], {'manifest_sha256': file_hash(self.manifest), 'checks': list(self.rows.values())})

    def validate(self):
        self.save_checks(); validate_review_coverage(self.data)

    def test_market_scope_and_date_boundaries(self):
        for meta in [{'country': 'NL'}, {'country': 'NL/BE'}, {'country': 'BE', 'target_language': 'Dutch'}]:
            self.assertTrue(is_dutch_market(meta))
        for meta in [{'country': 'SE'}, {'country': 'BE', 'target_language': 'French'}]:
            self.assertFalse(is_dutch_market(meta))
        # Country names, any case, are recognised as well as codes.
        for meta in [{'country': 'Netherlands'}, {'country': 'NEDERLAND'}, {'target_market': 'the Netherlands'},
                     {'country': 'Belgium', 'target_language': 'Dutch'}, {'country': 'belgië', 'target_language': 'nl-BE'}]:
            self.assertTrue(is_dutch_market(meta), meta)
        for meta in [{'country': 'Belgium'}, {'country': 'Belgium', 'target_language': 'French'}, {'country': 'Sweden'}]:
            self.assertFalse(is_dutch_market(meta), meta)
        for meta in [{'country': 'Sweden'}, {'country': 'SVERIGE'}, {'country': 'se'}, {'target_market': 'Sverige'}]:
            self.assertTrue(is_swedish_market(meta), meta)
        self.assertFalse(is_swedish_market({'country': 'Netherlands'}))
        for value, status in [('2026-10-02', 'recent'), ('2026-09-12', 'recent'), ('2026-09-11', 'stale'), ('2026-10-03', 'future')]:
            self.assertEqual(review_date_status(value, self.capture['captured_at'])['status'], status)
        self.assertEqual(review_date_status('2026-10-03', '2026-10-02T23:30:00Z')['age_days'], 0)
        with self.assertRaises(ValueError): review_date_status('31 september 2026', self.capture['captured_at'])

    def test_completed_dutch_checkout_allows_delivery_and_accurate_scope(self):
        self.validate()
        self.assertIn('visible iDEAL/Bancontact', offer_scope_summary(self.data))
        self.assertIn('were not tested', offer_scope_summary(self.data))

    def test_new_dutch_run_requires_checkout_even_when_offer_is_on_product(self):
        self.data['meta']['pages'] = self.pages
        self.data['meta']['offer_locations'] = {'ours': 'product', 'competitor': 'product'}
        with self.assertRaisesRegex(ValueError, 'Dutch-market reviews require'):
            self.validate()
        # New capture policy also activates the gate if report metadata forgot it.
        del self.data['meta']['review_policy_version']
        index_page(self.pages[0], review_policy_version=2)
        with self.assertRaisesRegex(ValueError, 'Dutch-market reviews require'):
            self.validate()

    def test_other_markets_and_historical_runs_retain_original_scope(self):
        self.data['meta']['pages'] = self.pages
        self.data['meta']['country'] = 'SE'; self.validate()
        self.data['meta']['country'] = 'NLBE'; del self.data['meta']['review_policy_version']; self.validate()
        self.assertNotIn('reviews, dates', offer_scope_summary(self.data))

    def test_each_new_check_is_mandatory_with_bound_screenshot_evidence(self):
        for name in CHECKOUT_REVIEW_CHECKS:
            row = self.rows[name]
            for status in ['pending', 'blocked', 'not_applicable']:
                row['status'] = status
                with self.subTest(name=name, status=status), self.assertRaisesRegex(ValueError, 'pending, blocked'):
                    self.validate()
            row['status'] = 'pass'; row['evidence_files'] = ['unbound.png']
            with self.assertRaisesRegex(ValueError, 'hash-bound'):
                self.validate()
            row['evidence_files'] = ['full.png']

    def test_old_future_and_unreadable_dates_need_findings(self):
        date_row = self.rows['checkout_review_dates']; review = date_row['reviews'][0]
        for value in ['2026-09-07', '2026-10-03', None]:
            review['date'] = value
            with self.assertRaises(ValueError): self.validate()
        date_row.update(status='issue', finding_ids=['T50'])
        with self.assertRaisesRegex(ValueError, 'existing finding'):
            self.validate()
        self.data['issues'] = [{'id': 'T50', 'page': 'checkout', 'check': 'checkout_review_dates'}]
        self.validate()

    def test_payment_footer_icons_cannot_pass_and_each_provider_is_independent(self):
        row = self.rows['checkout_bancontact']
        for key, value in [('visible', False), ('loaded', False), ('location', 'footer_badges')]:
            previous = row[key]; row[key] = value
            with self.assertRaisesRegex(ValueError, 'visible, loaded actual'):
                self.validate()
            row[key] = previous

    def test_guarantee_mismatch_and_missing_faq_or_review_inventory_cannot_pass(self):
        guarantee = self.rows['checkout_guarantee']['observations'][1]
        guarantee['brand'] = 'Other product'
        with self.assertRaisesRegex(ValueError, 'mismatched checkout guarantee'): self.validate()
        guarantee['brand'] = 'Example'; guarantee['days'] = 30
        with self.assertRaisesRegex(ValueError, 'mismatched checkout guarantee'): self.validate()
        guarantee['days'] = 60; self.rows['checkout_faq']['faq_ids'] = []
        with self.assertRaisesRegex(ValueError, 'every expanded'): self.validate()
        self.rows['checkout_faq']['faq_ids'] = ['faq-1']; self.rows['checkout_review_names']['review_ids'] = []
        with self.assertRaisesRegex(ValueError, 'every review ID'): self.validate()

    def test_checks_file_rows_need_known_unique_ids(self):
        rows = list(self.rows.values())
        for bad, message in [(rows + [{'status': 'pass', 'reason': 'No id'}], 'needs an id'),
                             (rows + [{'id': 'invented_row', 'status': 'pass', 'reason': 'x'}], 'Unknown Dutch checkout check id: invented_row'),
                             (rows + [dict(rows[0])], 'Duplicate Dutch checkout check id: checkout_review_language')]:
            write_json(self.entry['checks_file'], {'manifest_sha256': file_hash(self.manifest), 'checks': bad})
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                validate_dutch_checkout(self.entry, self.capture, self.manifest, set(), self.data['meta'])
        write_json(self.entry['checks_file'], {'manifest_sha256': file_hash(self.manifest), 'checks': rows[1:] + [{'status': 'pass'}]})
        with self.assertRaisesRegex(ValueError, 'needs an id'):
            validate_review_coverage(self.data)  # A clear error, never a KeyError.

    def test_new_finding_types_require_actual_dutch_scope(self):
        self.data['issues'] = [{'id': 'T51', 'page': 'checkout', 'check': 'checkout_review_language'}]
        self.validate()
        self.entry['scope'] = 'price_and_offer'; self.data['meta']['country'] = 'SE'
        with self.assertRaisesRegex(ValueError, 'prices or offer'):
            self.validate()


if __name__ == '__main__': unittest.main()
