"""The standard generation path preserves findings in the approved design."""
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

from tools.feedback_presentation import feedback_type, location_link
from tools.generate_feedback_page import CHECKOUT_CHECKS, generate


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def matching(self, tag, css=None):
        return [attrs for name, attrs in self.tags if name == tag and (css is None or css in attrs.get('class', '').split())]


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.shot = self.root / 'evidence.png'
        Image.new('RGB', (390, 600), 'white').save(self.shot)
        self.data = {'meta': {'brand_name': 'Example', 'country': 'SE',
                             'competitor_url': 'https://source.example/', 'our_url': 'https://target.example/'}, 'issues': []}

    def issue(self, **kwargs):
        result = {'id': 'T7', 'page': 'advertorial', 'feedback_type': 'find_replace',
                  'description': 'Use this complete sentence.',
                  'evidence_pairs': [{'id': 'B', 'marker': 'B', 'location': 'Author introduction',
                                      'source_screenshot': str(self.shot), 'target_screenshot': str(self.shot)}],
                  'replacements': [{'find': 'A long original sentence with two wrong things.',
                                    'replace': 'A long corrected sentence with two right things.', 'evidence_ids': ['B']}]}
        return {**result, **kwargs}

    def render(self):
        source, output = self.root / 'issues.json', self.root / 'review.html'
        original = json.dumps(self.data)
        source.write_text(original)
        generate(str(source), str(output), draft=True)
        self.assertEqual(source.read_text(), original)
        return output.read_text()

    def test_standard_path_keeps_sentence_and_only_target_preview(self):
        self.data['issues'] = [self.issue()]
        result = self.render()
        tags = Elements(result)
        self.assertEqual([b['data-copy'] for b in tags.matching('button', 'copy')],
                         [r[k] for r in self.data['issues'][0]['replacements'] for k in ('find', 'replace')])
        self.assertEqual(len(tags.matching('img')), 2)  # target + empty dialog image
        self.assertEqual(len(tags.matching('button', 'preview')), 1)
        self.assertIn('data-marker="B">B', result)
        self.assertIn('Example · SE · 1 fixes to be done', result)
        self.assertNotIn('CalmSoothe', result)

    def test_important_note_precedes_instruction_and_is_explicit_escaped_text(self):
        note = "NOTE: IF THIS IS A MOVING PRODUCT INSIDE A VIDEO YOU CAN'T EDIT - THEN SKIP THIS FEEDBACK"
        self.data['issues'] = [self.issue(important_note=note)]
        result = self.render()
        self.assertEqual(len(Elements(result).matching('p', 'important-note')), 1)
        self.assertLess(result.index('<p class="important-note">'), result.index('<div class="intro">'))
        self.assertIn('CAN&#x27;T EDIT - THEN SKIP THIS FEEDBACK', result)
        self.data['issues'][0]['important_note'] = '<script>unsafe()</script>'
        result = self.render()
        self.assertIn('&lt;script&gt;unsafe()&lt;/script&gt;', result)
        self.assertNotIn('<script>unsafe()', result)
        self.data['issues'] = [self.issue(id='V09', feedback_type='image_edit', description='Replace branding in a GIF.')]
        self.assertEqual(Elements(self.render()).matching('p', 'important-note'), [])
        self.data['issues'][0]['important_note'] = ['invalid']
        with self.assertRaisesRegex(ValueError, 'Important note must be a string'):
            self.render()

    def test_missing_content_is_expanded_and_addition_has_no_label(self):
        self.data['issues'] = [self.issue(feedback_type='missing_content', replacements=[{'find': '', 'replace': 'Complete new paragraph.'}])]
        result = self.render(); tags = Elements(result)
        self.assertEqual(len(tags.matching('figure')), 2)
        self.assertEqual(len(tags.matching('button', 'preview')), 0)
        self.assertIn('<figcaption>COMPETITOR</figcaption>', result)
        self.assertIn('<figcaption>OUR FUNNEL</figcaption>', result)
        self.assertNotIn('Add this text', result)
        self.assertEqual([b['data-copy'] for b in tags.matching('button', 'copy')], ['Complete new paragraph.'])

    def test_multiple_edits_follow_their_evidence_without_reordering_markers(self):
        item = self.issue()
        item['evidence_pairs'].append({**item['evidence_pairs'][0], 'id': 'D', 'marker': 'D'})
        item['replacements'] += [{'find': 'second old', 'replace': 'second new', 'evidence_ids': ['B']},
                                 {'find': 'shared old', 'replace': 'shared new', 'evidence_ids': ['B', 'D']}]
        self.data['issues'] = [item]
        result = self.render(); tags = Elements(result)
        self.assertEqual([c['data-evidence-id'] for c in tags.matching('section', 'card')], ['B', 'D'])
        self.assertEqual(len(tags.matching('button', 'copy')), 8)
        item['replacements'][0]['evidence_ids'] = ['absent']
        with self.assertRaisesRegex(ValueError, 'evidence_ids'):
                self.render()

    def test_our_offer_checkout_comparison_is_not_labeled_competitor(self):
        issue = self.issue(feedback_type='price_offer')
        issue['evidence_pairs'][0].update(display='comparison', source_label='OUR OFFER', target_label='OUR CHECKOUT')
        self.data['issues'] = [issue]
        result = self.render()
        self.assertIn('<figcaption>OUR OFFER</figcaption>', result)
        self.assertIn('<figcaption>OUR CHECKOUT</figcaption>', result)
        self.assertNotIn('<figcaption>COMPETITOR</figcaption>', result)

    def test_cross_page_scopes_preserved_and_owner_decisions_not_rendered(self):
        item = self.issue(pages=['advertorial', 'product'])
        item['evidence_pairs'][0]['page'] = 'advertorial'
        item['evidence_pairs'].append({**item['evidence_pairs'][0], 'id': 'C', 'marker': 'C', 'page': 'product'})
        self.data['issues'] = [item]
        self.data['decisions'] = [{'id': 'D1', 'page': 'product', 'question': 'Which version should we use?'}]
        result = self.render(); tags = Elements(result)
        self.assertEqual([p['data-pages'] for p in tags.matching('section', 'panel')], ['advertorial product'])
        self.assertEqual(len(tags.matching('input')), 2)
        self.assertIn('1 fixes to be done', result)
        self.assertNotIn('Owner decisions', result)
        self.assertNotIn('Which version should we use?', result)
        self.assertNotIn('panel-D1', result)
        del item['evidence_pairs'][0]['page']
        with self.assertRaisesRegex(ValueError, 'Cross-page'):
            self.render()

    def test_single_page_finding_and_its_evidence_share_one_page_scope(self):
        item = self.issue()  # Finding on the advertorial, evidence captured on the product page.
        item['evidence_pairs'][0]['page'] = 'product'
        self.data['issues'] = [item]
        tags = Elements(self.render())
        self.assertEqual([p['data-pages'] for p in tags.matching('section', 'panel')], ['advertorial product'])
        self.assertEqual([c['data-pages'] for c in tags.matching('section', 'card')], ['advertorial product'])

    def test_default_ids_never_collide_with_explicit_ids(self):
        explicit = self.issue(id='T2')
        default = self.issue()
        del default['id']
        self.data['issues'] = [explicit, default]
        panels = [p['id'] for p in Elements(self.render()).matching('section', 'panel')]
        self.assertEqual(len(panels), len(set(panels)))
        self.assertEqual(panels, ['panel-T2', 'panel-T2-2'])

    def test_private_decision_evidence_is_not_loaded_and_confirmed_d_ids_render(self):
        self.data['decisions'] = [{'id': 'D1', 'page': 'product',
            'question': 'Private shipping decision',
            'evidence_pairs': [{'id': 'A', 'target_screenshot': '/missing/private-decision.png'}]}]
        result = self.render()
        self.assertIn('0 fixes to be done', result)
        self.assertNotIn('Private shipping decision', result)
        self.assertNotIn('private-decision.png', result)
        self.assertEqual(Elements(result).matching('section', 'panel'), [])
        self.data['issues'] = [self.issue(id='D2', description='Apply the owner-approved correction.')]
        result = self.render()
        self.assertIn('panel-D2', result)
        self.assertIn('Apply the owner-approved correction.', result)
        self.data['issues'][0]['id'] = 'D1'
        with self.assertRaisesRegex(ValueError, 'IDs must be unique'):
            self.render()

    def test_source_only_comments_keep_compact_gallery_and_image_only_needs_no_copy(self):
        self.data['issues'] = [self.issue(check='missing_comments', feedback_type='missing_content', replacements=[],
            evidence_pairs=[{'id': x, 'marker': x, 'source_screenshot': str(self.shot)} for x in ['A', 'B']])]
        result = self.render(); tags = Elements(result)
        self.assertIn('class="cards gallery"', result)
        self.assertEqual(len(tags.matching('button', 'preview')), 2)
        self.assertEqual(len(tags.matching('button', 'copy')), 0)
        self.data['issues'] = [self.issue(feedback_type='image_edit', replacements=[])]
        self.assertEqual(len(Elements(self.render()).matching('button', 'copy')), 0)

    def test_category_is_explicit_and_not_derived_from_issue_number(self):
        self.assertEqual(feedback_type({'id': 'V99', 'feedback_type': 'price_offer'}), 'price_offer')
        self.assertEqual(feedback_type({'id': 'T99', 'feedback_type': 'image_edit', 'check': 'offer_presentation'}), 'image_edit')
        self.assertEqual(feedback_type({'page': 'product', 'check': 'price_and_discount'}), 'price_offer')
        self.assertEqual(feedback_type({'correct_text': 'Add this'}), 'missing_content')
        with self.assertRaisesRegex(ValueError, 'feedback_type'):
            feedback_type({'feedback_type': 'invalid'})
        self.assertEqual(CHECKOUT_CHECKS, {'price_and_discount', 'offer_presentation', 'pricing_consistency'})

    def test_orange_is_for_selection_and_checkout_not_editorial_money(self):
        self.assertEqual(feedback_type({'page': 'advertorial', 'feedback_type': 'price_offer'}), 'find_replace')
        self.assertEqual(feedback_type({'page': 'product', 'offer_context': 'editorial', 'check': 'pricing_consistency'}), 'find_replace')
        for kind in ['find_replace', 'image_edit', 'missing_content', 'price_offer']:
            self.assertEqual(feedback_type({'page': 'checkout', 'feedback_type': kind}), 'price_offer')
        self.assertEqual(feedback_type({'page': 'advertorial', 'offer_context': 'product_selection', 'feedback_type': 'image_edit'}), 'price_offer')

    def test_html_is_escaped_and_links_require_safe_verified_locations(self):
        self.data['issues'] = [self.issue(description='<script>alert(1)</script>', replacements=[{
            'find': '" & < >\nline two', 'replace': '</script><script>bad()</script>'}])]
        result = self.render()
        self.assertNotIn('<script>alert(1)', result)
        self.assertIn('&lt;/script&gt;', result)
        self.assertEqual(Elements(result).matching('button', 'copy')[0]['data-copy'], '" & < >\nline two')
        self.data['meta']['our_url'] = 'javascript:alert(1)'
        with self.assertRaisesRegex(ValueError, 'http'):
            self.render()
        meta = {'our_url': 'https://example.org/a#old'}
        pair = {'target_anchor': 'Question: 60–90 days?'}
        url, _ = location_link({'page': 'advertorial'}, pair, [], meta, {})
        self.assertEqual(url, 'https://example.org/a#:~:text=Question%3A%2060%E2%80%9390%20days%3F')
        url, _ = location_link({'page': 'advertorial'}, {}, [{'find': 'duplicate'}], meta, {'advertorial': 'duplicate duplicate'})
        self.assertEqual(url, meta['our_url'])

    def test_legacy_fields_deletions_and_empty_reviews(self):
        self.data['issues'] = [{'id': 'T1', 'page': 'product', 'wrong_text': 'Delete me', 'correct_text': ''}]
        result = self.render(); tags = Elements(result)
        self.assertEqual([b['data-copy'] for b in tags.matching('button', 'copy')], ['Delete me'])
        self.assertIn('Delete this text.', result)
        self.data['issues'] = []
        self.assertIn('0 fixes to be done', self.render())


if __name__ == '__main__':
    unittest.main()
