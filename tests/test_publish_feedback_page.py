import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.publish_feedback_page import deployment_url_from_output, prepare, publish, review_slug, verify_url


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "hosting.json"
        self.config.write_text(json.dumps({"provider": "vercel", "scope": "test-team",
                                           "project": "funnel-reviews"}))
        self.issues = self.root / "issues.json"
        self.issues.write_text(json.dumps({"meta": {"run_id": "test-run", "funnel_builder": "Alex", "brand_name": "GutFlow™", "country": "SE"}, "issues": []}))
        (self.root / ".env").write_text("SECRET=never-upload\n")

    def prepare_draft(self, title="Test"):
        return prepare(self.issues, title, True, self.config, self.root / "staging")

    def test_naming_uses_builder_product_and_country_over_ids(self):
        self.assertEqual(review_slug({"funnel_builder": "José van Dijk",
            "brand_name": "CalmSoothe™", "country": "NLBE",
            "funnel_id": "NLBE 210", "run_id": "random-id"}),
            "jose-van-dijk-calmsoothe-nlbe")

    def test_naming_requires_all_three_fields(self):
        meta = {"funnel_builder": "Alex", "brand_name": "GutFlow", "country": "SE"}
        for field in meta:
            for value in (None, "", " "):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(ValueError, field):
                        review_slug({**meta, field: value, "run_id": "no-fallback"})

    def test_only_report_and_hosting_configuration_are_staged(self):
        _, receipt = self.prepare_draft()
        site = Path(receipt["site_dir"])
        self.assertEqual({p.name for p in site.iterdir()}, {"index.html", "vercel.json", ".vercelignore", "alex-gutflow-se"})
        self.assertIn("**/receipt.json", (site / ".vercelignore").read_text())
        html = (site / "alex-gutflow-se" / "index.html").read_text()
        self.assertIn("DRAFT — incomplete or unverified", html)
        self.assertNotIn("never-upload", html)
        self.assertIn(receipt["content_sha256"], html)

    def test_incomplete_review_cannot_be_published_as_complete(self):
        with self.assertRaisesRegex(ValueError, "Incomplete review"):
            prepare(self.issues, config_file=self.config, output_root=self.root / "staging")

    def test_publishing_preserves_approved_full_sentence_copy(self):
        data = json.loads(self.issues.read_text())
        data["issues"] = [{"wrong_text": "Deze behandeling kost €3.731,52 in de particuliere zorg.",
                           "correct_text": "Deze behandeling kost €2.500 in de particuliere zorg."}]
        source = json.dumps(data)
        self.issues.write_text(source)
        _, receipt = self.prepare_draft()
        html = (Path(receipt["site_dir"]) / "alex-gutflow-se" / "index.html").read_text()
        self.assertIn('data-copy="Deze behandeling kost €3.731,52 in de particuliere zorg."', html)
        self.assertIn('data-copy="Deze behandeling kost €2.500 in de particuliere zorg."', html)
        self.assertNotIn('data-copy="€3.731,52"', html)
        self.assertEqual(self.issues.read_text(), source)

    def test_revision_keeps_project_and_slug(self):
        _, first = self.prepare_draft()
        _, same = self.prepare_draft()
        _, revised = self.prepare_draft("New title")
        self.assertEqual(first["project"], same["project"])
        self.assertEqual(first["project"], revised["project"])
        self.assertEqual(first["review_slug"], revised["review_slug"])
        self.assertNotEqual(first["content_sha256"], revised["content_sha256"])

    def test_two_reviews_accumulate_and_revision_preserves_other_review(self):
        _, first = self.prepare_draft("First <report>")
        site = Path(first["site_dir"])
        original = (site / "alex-gutflow-se" / "index.html").read_bytes()
        self.issues.write_text(json.dumps({"meta": {"funnel_id": "SE 195", "funnel_builder": "Sam", "brand_name": "Manvra", "country": "SE"}, "issues": []}))
        _, second = self.prepare_draft("Sweden")
        self.prepare_draft("Sweden revised")
        self.assertEqual(second["review_slug"], "sam-manvra-se")
        self.assertEqual((site / "alex-gutflow-se" / "index.html").read_bytes(), original)
        index = (site / "index.html").read_text()
        self.assertIn('/alex-gutflow-se/', index)
        self.assertIn('/sam-manvra-se/', index)
        self.assertIn('class="open-link" href="/alex-gutflow-se/"', index)
        self.assertIn('class="open-link" href="/sam-manvra-se/"', index)

    def test_each_review_keeps_its_own_deployment_receipt(self):
        first_path, first = self.prepare_draft()
        self.issues.write_text(json.dumps({"meta": {"funnel_builder": "Sam", "brand_name": "Manvra", "country": "SE"}, "issues": []}))
        second_path, _ = self.prepare_draft()
        self.assertEqual(first_path.name, "alex-gutflow-se.json")
        self.assertEqual(second_path.name, "sam-manvra-se.json")
        self.assertNotEqual(first_path, second_path)
        self.assertEqual(json.loads(first_path.read_text())["content_sha256"], first["content_sha256"])

    def test_tampered_report_is_rejected_before_vercel_call(self):
        path, receipt = self.prepare_draft()
        (Path(receipt["site_dir"]) / "alex-gutflow-se" / "index.html").write_text("different report")
        with patch("tools.publish_feedback_page.run_vercel") as cli:
            with self.assertRaisesRegex(ValueError, "report changed"):
                publish(path, receipt, allow_draft=True)
            cli.assert_not_called()

    def test_unexpected_file_blocks_upload(self):
        path, receipt = self.prepare_draft()
        (Path(receipt["site_dir"]) / ".env").write_text("SECRET=value")
        with patch("tools.publish_feedback_page.run_vercel") as cli:
            with self.assertRaisesRegex(ValueError, "Unexpected file"):
                publish(path, receipt, allow_draft=True)
            cli.assert_not_called()

    def test_draft_is_never_deployed(self):
        path, receipt = self.prepare_draft()
        with patch("tools.publish_feedback_page.run_vercel") as cli:
            with self.assertRaisesRegex(ValueError, "Drafts are never deployed"):
                publish(path, receipt)
            cli.assert_not_called()

    def test_cli_refuses_draft_without_prepare_only_and_keeps_caller_relative_paths(self):
        import contextlib
        import io
        import os
        from tools import publish_feedback_page
        argv = ["publish_feedback_page.py", "--issues-file", "issues.json", "--draft"]
        with patch("sys.argv", argv), patch("tools.publish_feedback_page.publish") as deploy:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                publish_feedback_page.main()
            deploy.assert_not_called()
        previous = os.getcwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(self.root)
        seen = {}

        def fake_prepare(issues_file, title, draft, config_file):
            seen.update(issues_file=issues_file, config=config_file)
            raise ValueError("stop after argument resolution")

        argv = ["publish_feedback_page.py", "--issues-file", "issues.json", "--config", "hosting.json",
                "--draft", "--prepare-only"]
        with patch("sys.argv", argv), patch("tools.publish_feedback_page.prepare", side_effect=fake_prepare):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(publish_feedback_page.main(), 1)
        self.assertEqual(Path(seen["issues_file"]), self.issues.resolve())
        self.assertEqual(Path(seen["config"]), self.config.resolve())

    def test_production_url_is_verified_and_saved(self):
        path, receipt = self.prepare_draft()
        responses = ["", "https://example-build.vercel.app", json.dumps({"projects": [
            {"name": receipt["project"], "latestProductionUrl": "https://example.vercel.app"}
        ]})]
        with patch("tools.publish_feedback_page.run_vercel", side_effect=responses) as cli:
            with patch("tools.publish_feedback_page.verify_url") as verify:
                result = publish(path, receipt, allow_draft=True)
                verify.assert_called_once_with("https://example.vercel.app/alex-gutflow-se/", receipt["content_sha256"])
            self.assertEqual(cli.call_count, 3)
        self.assertEqual(result["status"], "published")
        self.assertEqual(json.loads(path.read_text())["url"], "https://example.vercel.app/alex-gutflow-se/")
        with patch("tools.publish_feedback_page.run_vercel") as cli:
            with patch("tools.publish_feedback_page.verify_url"):
                publish(path, result, verify_only=True, allow_draft=True)
            cli.assert_not_called()

    def test_custom_domain_is_used_for_delivery(self):
        config = json.loads(self.config.read_text())
        config["base_url"] = "https://funnel.example.com/"
        self.config.write_text(json.dumps(config))
        path, receipt = self.prepare_draft()
        with patch("tools.publish_feedback_page.run_vercel", side_effect=["", "https://build.vercel.app"]) as cli:
            with patch("tools.publish_feedback_page.verify_url") as verify:
                result = publish(path, receipt, allow_draft=True)
        self.assertEqual(cli.call_count, 2)
        self.assertEqual(result["url"], "https://funnel.example.com/alex-gutflow-se/")
        verify.assert_called_once_with(result["url"], receipt["content_sha256"])

    def test_login_page_does_not_count_as_verified_report(self):
        with patch("tools.publish_feedback_page.urlopen") as opening:
            opening.return_value.__enter__.return_value.read.return_value = b"<html>Log in to Vercel</html>"
            with self.assertRaisesRegex(RuntimeError, "did not return this report"):
                verify_url("https://example.vercel.app", "digest")

    def test_plain_json_and_agent_cli_responses(self):
        for value in ("https://example.vercel.app\n", '{"url":"example.vercel.app"}',
                      '{"status":"ok","deployment":{"url":"https://example.vercel.app"}}'):
            self.assertEqual(deployment_url_from_output(value), "https://example.vercel.app")
        with self.assertRaises(RuntimeError):
            deployment_url_from_output("https://vercel.com/dashboard")

    def test_recover_existing_deployment_without_upload(self):
        path, receipt = self.prepare_draft()
        cli_env = Path(receipt["site_dir"]) / ".env.local"
        cli_env.write_text("VERCEL_OIDC_TOKEN=temporary-cli-fixture")
        responses = [json.dumps({"projects": [{"name": receipt["project"],
                      "latestProductionUrl": "https://example.vercel.app"}]}),
                     '{"readyState":"READY","url":"example-build.vercel.app"}']
        with patch("tools.publish_feedback_page.run_vercel", side_effect=responses) as cli:
            with patch("tools.publish_feedback_page.verify_url"):
                result = publish(path, receipt, verify_only=True, allow_draft=True)
        self.assertEqual([call.args[0][0] for call in cli.call_args_list], ["project"])
        self.assertEqual(result["status"], "published")
        self.assertFalse(cli_env.exists())

    def test_failed_verification_preserves_deployment_for_retry(self):
        path, receipt = self.prepare_draft()
        responses = ["", "https://example-build.vercel.app", json.dumps({"projects": [
            {"name": receipt["project"], "latestProductionUrl": "https://example.vercel.app"}
        ]})]
        with patch("tools.publish_feedback_page.run_vercel", side_effect=responses):
            with patch("tools.publish_feedback_page.verify_url", side_effect=RuntimeError("Protected")):
                with self.assertRaisesRegex(RuntimeError, "Protected"):
                    publish(path, receipt, allow_draft=True)
        saved = json.loads(path.read_text())
        self.assertEqual(saved["status"], "deployed_unverified")
        self.assertEqual(saved["url"], "https://example.vercel.app/alex-gutflow-se/")

    def test_lookup_failure_still_preserves_deployment_url(self):
        path, receipt = self.prepare_draft()
        with patch("tools.publish_feedback_page.run_vercel", side_effect=["", "https://build.vercel.app", RuntimeError("Lookup failed")]):
            with self.assertRaisesRegex(RuntimeError, "Lookup failed"):
                publish(path, receipt, allow_draft=True)
        saved = json.loads(path.read_text())
        self.assertEqual(saved["status"], "deployed_unverified")
        self.assertEqual(saved["deployment_url"], "https://build.vercel.app")

    def test_wrong_linked_project_blocks_deployment(self):
        path, receipt = self.prepare_draft()
        link = Path(receipt["site_dir"]) / ".vercel"
        link.mkdir()
        (link / "project.json").write_text(json.dumps({"projectName": "wrong-project"}))
        with patch("tools.publish_feedback_page.run_vercel") as cli:
            with self.assertRaisesRegex(ValueError, "different Vercel project"):
                publish(path, receipt, allow_draft=True)
        cli.assert_not_called()


if __name__ == "__main__":
    unittest.main()
