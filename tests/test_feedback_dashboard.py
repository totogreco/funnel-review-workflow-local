import json
import tempfile
import unittest
from pathlib import Path

from tools.feedback_dashboard import render_dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)

    def review(self, slug, **metadata):
        directory = self.site / slug
        directory.mkdir()
        (directory / "index.html").write_text("Existing feedback")
        (directory / "receipt.json").write_text(json.dumps(metadata))

    def test_groups_all_existing_reviews_by_builder(self):
        self.review("ali-calmsoothe-nlbe", funnel_builder="Ali", brand_name="CalmSoothe", country="NLBE", issue_count=48)
        self.review("jonah-gutflow-se", funnel_builder="Jonah", brand_name="GutFlow", country="SE", issue_count=23)
        self.review("ali-another-se", funnel_builder="Ali", brand_name="Another", country="SE", issue_count=0)
        html = render_dashboard(self.site)
        self.assertEqual(html.count('class="builder-group"'), 2)
        self.assertEqual(html.count('class="review-row"'), 3)
        self.assertIn('48 findings', html)
        self.assertIn('0 findings', html)
        self.assertIn('href="/jonah-gutflow-se/"', html)
        self.assertIn('2 reviews</span>', html)

    def test_metadata_is_escaped_and_private_fields_are_not_exported(self):
        self.review("safe-product-se", funnel_builder='</script><img src=x onerror=alert(1)>',
                    brand_name='" onmouseover="bad', country="SE",
                    issues_file="/private/captures/secret.json", content_sha256="private-hash")
        html = render_dashboard(self.site)
        self.assertNotIn('</script><img', html)
        self.assertIn('&lt;/script&gt;', html)
        self.assertNotIn('/private/captures', html)
        self.assertNotIn('private-hash', html)
        self.assertIn('&quot; onmouseover=&quot;bad', html)

    def test_missing_metadata_is_not_inferred_from_a_slug(self):
        self.review("mystery-product-se", title="Historical report", issue_count=None)
        html = render_dashboard(self.site)
        self.assertIn('Unassigned', html)
        self.assertIn('Not recorded', html)
        self.assertNotIn('0 findings', html)

    def test_drafts_and_bad_dates_are_labeled(self):
        self.review("ali-example-se", funnel_builder="Ali", brand_name="Example", country="SE",
                    draft=True, published_at="yesterday")
        html = render_dashboard(self.site)
        self.assertIn('<span class="draft">Draft</span>', html)
        self.assertIn('Not recorded', html)

    def test_empty_and_nonreview_directories(self):
        (self.site / ".vercel").mkdir()
        (self.site / "unfinished").mkdir()
        html = render_dashboard(self.site)
        self.assertNotIn('class="review-row"', html)
        self.assertIn('id="empty" >', html)
        self.assertIn('No feedback published yet', html)


if __name__ == "__main__":
    unittest.main()
