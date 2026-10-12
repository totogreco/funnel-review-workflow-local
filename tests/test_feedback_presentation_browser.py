"""Opt-in real-browser controls: RUN_BROWSER_TESTS=1 python -m unittest this module."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from tools.generate_feedback_page import generate


@unittest.skipUnless(os.environ.get('RUN_BROWSER_TESTS') == '1', 'Set RUN_BROWSER_TESTS=1 for Chromium fixtures')
class PresentationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        shot = cls.root / 'shot.png'
        Image.new('RGB', (390, 844), 'white').save(shot)
        cls.data = {'meta': {'brand_name': 'Sample', 'country': 'NL',
                            'our_url': 'https://ours.example/', 'competitor_url': 'https://source.example/'}, 'issues': []}
        for n, kind in enumerate(['find_replace', 'missing_content', 'image_edit', 'price_offer'], 1):
            cls.data['issues'].append({'id': f'T{n}', 'page': 'advertorial' if n == 1 else 'product',
                'feedback_type': kind, 'description': 'Apply the marked correction.',
                'evidence_pairs': [{'id': 'B', 'marker': 'B', 'location': 'A short location',
                    'target_screenshot': str(shot), 'source_screenshot': str(shot)}],
                'replacements': [{'find': '' if n == 2 else 'Complete original sentence.', 'replace': 'Complete corrected sentence.'}]})
        cross = {'id': 'T5', 'page': 'advertorial', 'pages': ['advertorial', 'product'], 'feedback_type': 'find_replace',
            'description': 'Correct both locations.', 'evidence_pairs': [
                {'id': p, 'page': p, 'marker': m, 'target_screenshot': str(shot), 'location': p}
                for p, m in [('advertorial', 'A'), ('product', 'C')]],
            'replacements': [{'find': 'original', 'replace': 'corrected', 'evidence_ids': ['advertorial', 'product']}]}
        cls.data['issues'].append(cross)
        cls.data['issues'].append({'id': 'T6é', 'page': 'product', 'feedback_type': 'find_replace',
            'description': 'Encoded hash target.', 'evidence_pairs': [{'id': 'A', 'marker': 'A', 'location': 'Hash',
                'target_screenshot': str(shot)}], 'replacements': [{'find': 'old', 'replace': 'new'}]})
        cls.data['issues'][2]['important_note'] = "NOTE: IF THIS IS A MOVING PRODUCT INSIDE A VIDEO YOU CAN'T EDIT - THEN SKIP THIS FEEDBACK"
        cls.data['decisions'] = [{'id': 'D1', 'page': 'product', 'question': 'Which version should be used?'}]
        (cls.root / 'issues.json').write_text(json.dumps(cls.data))
        generate(str(cls.root / 'issues.json'), str(cls.root / 'review.html'), draft=True)
        (cls.root / 'empty.json').write_text(json.dumps({'issues': []}))
        generate(str(cls.root / 'empty.json'), str(cls.root / 'empty.html'), draft=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop(); cls.temp.cleanup()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1200, 'height': 900})
        self.addCleanup(self.page.close)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto((self.root / 'review.html').as_uri())

    def test_copy_success_reset_failure_and_done_roundtrip(self):
        page = self.page
        page.evaluate("Object.defineProperty(navigator, 'clipboard', {configurable:true,value:{writeText:async text=>{window.copiedText=text}}})")
        card = page.locator('#panel-T1 .card')
        button = card.locator('.copy').first
        self.assertEqual(button.evaluate('(b)=>getComputedStyle(b).backgroundColor'), 'rgb(255, 255, 255)')
        button.click(); self.assertEqual(button.inner_text(), 'Copied ✓')
        self.assertEqual(page.evaluate('window.copiedText'), 'Complete original sentence.')
        page.wait_for_function("document.querySelector('#panel-T1 .copy').textContent === 'COPY'")
        card.locator('.done input').check()
        self.assertEqual(card.locator('.number').inner_text(), '✓')
        self.assertEqual(card.locator('.number').evaluate('(n)=>getComputedStyle(n).backgroundColor'), 'rgb(41, 128, 94)')
        self.assertEqual(page.locator('#panel-T1 .track').get_attribute('aria-valuenow'), '1')
        card.locator('.done input').uncheck()
        self.assertEqual(card.locator('.number').inner_text(), 'B')
        page.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw Error('denied')}}});document.execCommand=()=>false")
        button.click(); self.assertEqual(button.inner_text(), 'COPY')
        self.assertIn('Ctrl+C', page.locator('.toast').inner_text())
        self.assertEqual(self.errors, [])

    def test_filters_combine_and_cross_page_cards_hide_individually(self):
        page = self.page
        self.assertEqual(page.locator('.page-option[aria-pressed=true]').inner_text(), 'Both pages')
        self.assertEqual(page.locator('.tab[aria-selected=true]').inner_text(), 'All Feedback')
        self.assertEqual(page.locator('#owner-decisions, .decision, #panel-D1').count(), 0)
        self.assertNotIn('Which version should be used?', page.content())
        page.locator('[data-page=advertorial]').click()
        self.assertEqual(page.locator('.panel:visible').count(), 2)
        self.assertEqual(page.locator('#panel-T5 .card:visible .number').inner_text(), 'A')
        self.assertTrue(page.locator('.tab[data-color=orange]').is_disabled())
        page.locator('[data-page=product]').click()
        self.assertEqual(page.locator('#panel-T5 .card:visible .number').inner_text(), 'C')
        page.locator('.tab[data-color=orange]').click()
        self.assertEqual(page.locator('.panel:visible').count(), 1)
        self.assertTrue(page.locator('#panel-T4').is_visible())
        page.locator('[data-page=advertorial]').click()
        self.assertEqual(page.locator('.tab[aria-selected=true]').inner_text(), 'All Feedback')
        self.assertEqual(self.errors, [])

    def test_comparisons_addition_alignment_preview_and_responsive_widths(self):
        page = self.page
        self.assertEqual(page.locator('#panel-T2 .comparison img:visible').count(), 2)
        self.assertEqual(page.locator('#panel-T2 .preview').count(), 0)
        self.assertEqual(page.locator('#panel-T2 .comparison-copy .label').count(), 0)
        field = page.locator('#panel-T2 .comparison-copy .field')
        centers = field.evaluate('(f)=>[...f.children].map(c=>{const r=c.getBoundingClientRect();return r.y+r.height/2})')
        self.assertLess(abs(centers[0] - centers[1]), 1)
        page.locator('#panel-T1 .preview').click()
        self.assertTrue(page.locator('dialog').is_visible())
        page.locator('.close').click(); self.assertFalse(page.locator('dialog').is_visible())
        for width in (320, 390, 736, 1024):
            page.set_viewport_size({'width': width, 'height': 844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width)
            note = page.locator('#panel-T3 .important-note')
            self.assertTrue(note.is_visible())
            self.assertLessEqual(note.bounding_box()['y'] + note.bounding_box()['height'],
                                 page.locator('#panel-T3 .intro').bounding_box()['y'])
        self.assertEqual(self.errors, [])

    def test_progress_counts_only_cards_visible_under_the_page_filter(self):
        page = self.page
        count = page.locator('#panel-T5 .count')
        self.assertEqual(count.inner_text(), '0 / 2 done')
        page.locator('[data-page=advertorial]').click()
        self.assertEqual(count.inner_text(), '0 / 1 done')
        page.locator('#panel-T5 .card:visible .done input').check()
        self.assertEqual(count.inner_text(), 'All done! 🎉')
        page.locator('[data-page=both]').click()
        self.assertEqual(count.inner_text(), '1 / 2 done')
        self.assertEqual(self.errors, [])

    def test_percent_encoded_hash_opens_its_panel(self):
        self.page.locator('[data-page=advertorial]').click()
        self.assertFalse(self.page.locator('#panel-T6é').is_visible())
        self.page.evaluate("location.hash = 'panel-T6%C3%A9'")  # hashchange, no reload
        self.page.wait_for_function("document.getElementById('panel-T6é').offsetParent !== null")
        self.assertEqual(self.page.locator('.page-option[aria-pressed=true]').inner_text(), 'Both pages')
        self.assertEqual(self.errors, [])

    def test_empty_review_and_hash_link_work_without_javascript_errors(self):
        self.page.goto((self.root / 'empty.html').as_uri())
        self.assertTrue(self.page.locator('#empty').is_visible())
        self.page.goto((self.root / 'review.html').as_uri() + '#panel-T4')
        self.assertTrue(self.page.locator('#panel-T4').is_visible())
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
