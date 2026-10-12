"""Per-button checkout evidence and offered-versus-payable price checks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from tools.checkout_review import validate_swedish_offers
from tools.generate_feedback_page import validate_review_coverage
from tools.review_io import file_hash, write_json


def index_page(entry, **extra):
    """Turn a page fixture into a minimal complete indexed packet with a passed check."""
    path = Path(entry['manifest']); folder = path.parent
    capture = json.loads(path.read_text())
    capture.update(schema_version=2, status='complete', index=capture['full_page'], faq_file=capture['full_page'],
                   files={p.name: file_hash(p) for p in folder.iterdir() if p.name != 'manifest.json'},
                   required_checks=[{'id': 'content_and_visuals'}], **extra)
    write_json(path, capture)
    checks = folder.parent / (folder.name + '-checks.json')
    write_json(checks, {'manifest_sha256': file_hash(path), 'checks': [
        {'id': 'content_and_visuals', 'status': 'pass', 'reason': 'Compared the fixture'}]})
    entry['checks_file'] = str(checks)


class SwedishOfferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.pages = []
        for side in ['ours', 'competitor']:
            for page in ['advertorial', 'product']:
                folder = self.root / f'{side}-{page}'; folder.mkdir()
                (folder / 'shot.png').write_bytes(b'fixture'); (folder / 'text.txt').write_text('Fixture')
                m = {'url': f'https://{side}.example/{page}', 'full_page': 'shot.png', 'text_file': 'text.txt',
                     'sections': [{'file': 'shot.png'}], 'files': {p.name: file_hash(p) for p in folder.iterdir()}}
                write_json(folder / 'manifest.json', m)
                self.pages.append({'side': side, 'page': page, 'url': m['url'], 'status': 'reviewed', 'manifest': str(folder / 'manifest.json')})
                index_page(self.pages[-1])  # Current-policy runs cannot use legacy captures.
        checkout = self.root / 'checkout'; checkout.mkdir()
        (checkout / 'shot.png').write_bytes(b'checkout'); (checkout / 'source.png').write_bytes(b'clicked offer')
        self.capture = {'status': 'complete', 'page': 'checkout', 'url': 'https://ours.example/checkout?offer=three',
            'files': {p.name: file_hash(p) for p in checkout.iterdir()},
            'offer_handoff': {'source_url': 'https://ours.example/product', 'selector': '#three',
                              'action': 'click', 'source_image': 'source.png'}}
        self.manifest = checkout / 'manifest.json'; write_json(self.manifest, self.capture)
        offer = {'product': 'Example', 'variant': 'standard', 'quantity': 3, 'currency': 'SEK', 'offer_total_minor': 59900}
        self.row = {'id': 'three-top', 'page': 'product', 'location': 'Three-bottle offer', 'selector': '#three',
            'action': 'Clicked three-bottle offer', 'status': 'pass', 'reason': 'Correct selected bundle and total',
            'source_evidence': ['shot.png'], 'checkout_loaded': True, 'correct_destination': True,
            'actual_url': self.capture['url'], 'checkout_manifest': str(self.manifest),
            'checkout_manifest_sha256': file_hash(self.manifest), 'checkout_evidence': ['shot.png'],
            'presented': copy.deepcopy(offer), 'checkout': {**offer, 'shipping_minor': 3900, 'payable_total_minor': 63800},
            'shipping_reason': '39 kr shipping, displayed separately.'}
        self.record = {'source_manifest_sha256': {p['page']: file_hash(p['manifest']) for p in self.pages if p['side'] == 'ours'},
            'inventory': {'status': 'pass', 'reason': 'Inspected both pages; one offer button.', 'button_ids': ['three-top']},
            'offers': [self.row]}
        self.meta = {'country': 'SE', 'review_policy_version': 3, 'pages': self.pages,
                     'swedish_offer_checks_file': str(self.root / 'checks.json'),
                     'cross_page_checks': {name: {'status': 'pass', 'reason': 'Compared fixture'} for name in ('guarantee', 'pricing')}}

    def validate(self):
        write_json(self.meta['swedish_offer_checks_file'], self.record)
        validate_swedish_offers(self.meta, {'T1'})

    def test_complete_clicked_offer_and_explained_shipping_pass(self):
        self.validate()
        validate_review_coverage({'meta': self.meta, 'issues': []})

    def test_checkout_page_binds_observed_handoff_destination(self):
        self.capture.update(url='https://ours.example/product',
                            resolved_url=self.row['actual_url'],
                            full_page='shot.png', text_file='source.png',
                            sections=[{'file': 'shot.png'}])
        write_json(self.manifest, self.capture)
        entry = {'side': 'ours', 'page': 'checkout', 'scope': 'price_and_offer',
                 'status': 'reviewed', 'url': self.row['actual_url'],
                 'manifest': str(self.manifest)}
        index_page(entry)
        self.row['checkout_manifest_sha256'] = file_hash(self.manifest)
        self.pages.append(entry)
        self.validate()
        validate_review_coverage({'meta': self.meta, 'issues': []})
        entry['url'] = self.capture['url']
        with self.assertRaisesRegex(ValueError, 'Capture URL'):
            validate_review_coverage({'meta': self.meta, 'issues': []})

    def test_new_swedish_run_cannot_skip_checkout_checks(self):
        del self.meta['swedish_offer_checks_file']
        with self.assertRaisesRegex(ValueError, 'swedish_offer_checks_file'):
            validate_review_coverage({'meta': self.meta})
        self.meta['review_policy_version'] = 2
        validate_review_coverage({'meta': self.meta})  # Historical policy retained.
        index_page(self.pages[0], review_policy_version=3)
        with self.assertRaisesRegex(ValueError, 'swedish_offer_checks_file'):
            validate_review_coverage({'meta': self.meta})

    def test_wrong_product_bundle_price_or_destination_cannot_pass(self):
        for key, value in [('product', 'Other product'), ('quantity', 1), ('variant', 'subscription'), ('offer_total_minor', 69900)]:
            before = self.row['checkout'][key]; self.row['checkout'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'selected offer or mismatched'):
                self.validate()
            self.row['checkout'][key] = before
        self.row['correct_destination'] = False
        with self.assertRaisesRegex(ValueError, 'wrong checkout'): self.validate()

    def test_price_comparison_distinguishes_shipping_and_total(self):
        self.row['presented']['shipping_minor'] = 0
        with self.assertRaisesRegex(ValueError, 'Advertised shipping'): self.validate()
        del self.row['presented']['shipping_minor']; self.row['checkout']['payable_total_minor'] = 99900
        with self.assertRaisesRegex(ValueError, 'payable total'): self.validate()

    def test_each_inventoried_button_requires_its_own_checked_capture(self):
        self.record['inventory']['button_ids'].append('three-bottom')
        with self.assertRaisesRegex(ValueError, 'inventoried'): self.validate()
        self.record['offers'].append({**self.row, 'id': 'three-bottom'})
        with self.assertRaisesRegex(ValueError, 'own clicked checkout'): self.validate()

    def test_untested_checks_and_generic_checkout_cannot_pass(self):
        self.row['status'] = 'blocked'
        with self.assertRaisesRegex(ValueError, 'pending, blocked'): self.validate()
        self.row['status'] = 'pass'; self.row['checkout_loaded'] = False
        with self.assertRaisesRegex(ValueError, 'untested/unloaded'): self.validate()
        self.row['checkout_loaded'] = True
        del self.capture['offer_handoff']; write_json(self.manifest, self.capture)
        self.row['checkout_manifest_sha256'] = file_hash(self.manifest)
        with self.assertRaisesRegex(ValueError, 'actual source-button click'): self.validate()

    def test_confirmed_failures_reference_findings_without_inventing_checkout(self):
        self.row.update(status='issue', finding_ids=['T1'], checkout_loaded=False, outcome='dead_button', reason='Click leaves the page unchanged.')
        self.validate()
        self.row['finding_ids'] = ['unknown']
        with self.assertRaisesRegex(ValueError, 'existing finding'): self.validate()


if __name__ == '__main__': unittest.main()
