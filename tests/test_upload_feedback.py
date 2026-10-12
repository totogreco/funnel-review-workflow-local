"""Upload staged reviews (old Vercel site or a local review) to the Render feedback pages."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import upload_feedback

BASE = "https://dash.example"


def stage(site: Path, slug: str, html: str, **receipt) -> str:
    (site / slug).mkdir(parents=True)
    digest = hashlib.sha256(html.encode()).hexdigest()
    marked = html.replace("<head>", f'<head>\n<meta name="funnel-review-content-sha256" content="{digest}">', 1)
    (site / slug / "index.html").write_text(marked)
    (site / slug / "receipt.json").write_text(json.dumps({"content_sha256": digest, "funnel_builder": "Ali", **receipt}))
    return marked


class Server:
    """In-memory /feedback/ pages; unknown pages answer 404 (None)."""

    def __init__(self, pages=None):
        self.pages, self.sent = dict(pages or {}), []

    def post(self, url, body, token):
        self.sent.append((url, token))
        self.pages[url.replace("/api/feedback/", "/feedback/") + "/"] = body["html"]

    def fetch(self, url):
        return self.pages.get(url)

    def patched(self):
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(upload_feedback, "post", side_effect=self.post))
        stack.enter_context(patch.object(upload_feedback, "fetch", side_effect=self.fetch))
        return stack


class Upload(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)

    def test_uploads_every_review_with_all_and_verifies_the_live_page(self):
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>A</body></html>")
        stage(self.site, "nadia-gutflow-se", "<html><head></head><body>B</body></html>")
        (self.site / "index.html").write_text("overview")  # not a review: skipped
        server = Server()
        with server.patched():
            results = upload_feedback.upload_all(self.site, BASE, "tok")
        self.assertEqual([r["slug"] for r in results], ["ali-flexicore-nlbe", "nadia-gutflow-se"])
        self.assertTrue(all(r["verified"] for r in results))
        self.assertEqual(server.sent[0], (f"{BASE}/api/feedback/ali-flexicore-nlbe", "tok"))

    def test_only_named_slugs_are_uploaded(self):
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>A</body></html>")
        stage(self.site, "nadia-gutflow-se", "<html><head></head><body>B</body></html>")
        server = Server()
        with server.patched():
            results = upload_feedback.upload_all(self.site, BASE, "tok", ["nadia-gutflow-se", "missing-review"])
        self.assertEqual([url for url, _ in server.sent], [f"{BASE}/api/feedback/nadia-gutflow-se"])
        self.assertTrue(results[0]["verified"])
        self.assertEqual((results[1]["status"], results[1]["verified"]), ("refused", False))

    def test_cli_requires_slug_or_all(self):
        with patch("sys.argv", ["upload_feedback.py", "--site-dir", str(self.site)]), \
             patch.dict("os.environ", {"FEEDBACK_UPLOAD_TOKEN": "tok"}), \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
            upload_feedback.main()
        self.assertEqual(stop.exception.code, 2)

    def test_changed_live_page_is_not_verified(self):
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>A</body></html>")
        with patch.object(upload_feedback, "post"), \
             patch.object(upload_feedback, "fetch", side_effect=[None, "<html>other</html>"]):
            [result] = upload_feedback.upload_all(self.site, BASE, "tok", ["ali-flexicore-nlbe"])
        self.assertFalse(result["verified"])

    def test_drafts_are_refused_unless_allowed(self):
        stage(self.site, "flagged", "<html><head></head><body>A</body></html>", draft=True)
        stage(self.site, "banner", '<html><head></head><body><p class="draft-warning"><strong>DRAFT — incomplete '
                                   'or unverified review. Not ready for delivery.</strong></p></body></html>')
        stage(self.site, "finished", "<html><head><style>.draft-warning{color:red}</style></head><body>A</body></html>")
        server = Server()
        with server.patched():
            results = upload_feedback.upload_all(self.site, BASE, "tok", ["flagged", "banner", "finished"])
        self.assertEqual([r["status"] for r in results], ["refused", "refused", "uploaded"])
        self.assertIn("draft", results[0]["reason"])
        with server.patched():
            results = upload_feedback.upload_all(self.site, BASE, "tok", ["flagged"], allow_draft=True)
        self.assertTrue(results[0]["verified"])

    def test_staged_page_must_match_its_receipt_hash(self):
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>A</body></html>")
        page = self.site / "ali-flexicore-nlbe" / "index.html"
        page.write_text(page.read_text().replace("<body>A", "<body>Edited after staging"))
        server = Server()
        with server.patched():
            [result] = upload_feedback.upload_all(self.site, BASE, "tok", ["ali-flexicore-nlbe"])
        self.assertEqual(result["status"], "refused")
        self.assertIn("hash", result["reason"])
        self.assertEqual(server.sent, [])

    def test_newer_or_unknown_age_live_page_is_not_overwritten_without_force(self):
        url = f"{BASE}/feedback/ali-flexicore-nlbe/"
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>Local</body></html>",
              published_at="2026-10-05T10:00:00+00:00")
        newer = '<html><head><meta name="funnel-review-published-at" content="2026-10-06T08:00:00+00:00"></head>Dashboard</html>'
        older = '<html><head><meta name="funnel-review-published-at" content="2026-10-04T08:00:00+00:00"></head>Old</html>'
        overview = ('<article class="review-row" data-search="x" data-product="X" data-date="2026-10-07">'
                    '<a class="open-link" href="/feedback/ali-flexicore-nlbe/">open</a></article>')
        for live, extra, expected in [(newer, {}, "refused"),
                                      ("<html>engine page, no markers</html>", {}, "refused"),
                                      ("<html>engine page</html>", {f"{BASE}/feedback/": overview}, "refused"),
                                      (older, {}, "uploaded"),
                                      (newer, {"force": True}, "uploaded")]:
            server = Server({url: live, **{k: v for k, v in extra.items() if k != "force"}})
            with self.subTest(live=live[:60], extra=list(extra)), server.patched():
                [result] = upload_feedback.upload_all(self.site, BASE, "tok", ["ali-flexicore-nlbe"],
                                                      force=extra.get("force", False))
                self.assertEqual(result["status"], expected, result)
                self.assertEqual(bool(server.sent), expected == "uploaded")

    def test_overview_date_older_than_staged_allows_upload(self):
        url = f"{BASE}/feedback/ali-flexicore-nlbe/"
        stage(self.site, "ali-flexicore-nlbe", "<html><head></head><body>Local</body></html>",
              published_at="2026-10-05T10:00:00+00:00")
        overview = ('<article class="review-row" data-search="x" data-product="X" data-date="2026-10-02">'
                    '<a class="open-link" href="/feedback/ali-flexicore-nlbe/">open</a></article>')
        server = Server({url: "<html>older engine page</html>", f"{BASE}/feedback/": overview})
        with server.patched():
            [result] = upload_feedback.upload_all(self.site, BASE, "tok", ["ali-flexicore-nlbe"])
        self.assertEqual((result["status"], result["verified"]), ("uploaded", True))

    def test_legacy_page_without_hash_marker_is_verified_by_its_exact_page(self):
        folder = self.site / "jonah-gutflow-se"
        folder.mkdir()
        html = "<html><head><title>SE 233 — GutFlow funnel review</title></head><body>Old</body></html>"
        (folder / "index.html").write_text(html)
        (folder / "receipt.json").write_text(json.dumps({"funnel_builder": "Jonah"}))
        server = Server()
        with server.patched():
            [result] = upload_feedback.upload_all(self.site, BASE, "tok", ["jonah-gutflow-se"])
        self.assertTrue(result["verified"])
        self.assertEqual(result["verification"], "verified (legacy page, no hash marker)")


if __name__ == "__main__":
    unittest.main()
