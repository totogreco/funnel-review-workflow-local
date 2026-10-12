"""A finished review must cover both funnel stages on both sides."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.generate_feedback_page import generate, validate_review_coverage
from tools.review_io import file_hash, write_json


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        pages = []
        for side in ("competitor", "ours"):
            for page in ("advertorial", "product"):
                folder = self.root / f"{side}_{page}"
                folder.mkdir()
                url = f"https://{side}.example/{page}"
                manifest = folder / "manifest.json"
                for name in ("full.png", "text.txt", "section.png"):
                    (folder / name).write_text("capture fixture")
                manifest.write_text(json.dumps({"url": url, "full_page": "full.png",
                    "text_file": "text.txt", "sections": [{"file": "section.png"}]}))
                pages.append({"side": side, "page": page, "url": url,
                              "manifest": str(manifest), "status": "reviewed"})
        self.data = {"meta": {"pages": pages}, "issues": []}

    def test_zero_findings_still_allows_a_fully_reviewed_funnel(self):
        validate_review_coverage(self.data)

    def test_discount_math_is_excluded_without_suppressing_actual_price_errors(self):
        for field in ("issues", "decisions"):
            for check in ("discount_calculation", "discount_percentage_calculation", "discount_rounding"):
                self.data[field] = [{"page": "product", "check": check}]
                with self.subTest(field=field, check=check), self.assertRaisesRegex(ValueError, "Discount-percentage"):
                    validate_review_coverage(self.data)
            self.data[field] = [{"page": "product", "check": "pricing_consistency",
                                 "description": "Checkout charges 699 kr for the advertised 565 kr bundle."}]
            validate_review_coverage(self.data)
            self.data[field] = []

    def test_renderer_enforces_indexed_packet_checks(self):
        entry=self.data['meta']['pages'][0];path=Path(entry['manifest'])
        capture=json.loads(path.read_text())
        capture.update(schema_version=2,status='complete',index='text.txt',faq_file='text.txt',
            files={name:file_hash(path.parent/name) for name in ('full.png','text.txt','section.png')},
            required_checks=[{'id':'content_and_visuals'}])
        write_json(path,capture)
        checks_path=path.parent/'checks.json';entry['checks_file']=str(checks_path)
        checks={'manifest_sha256':file_hash(path),'checks':[{'id':'content_and_visuals','status':'pending','reason':'Not reviewed'}]}
        write_json(checks_path,checks)
        with self.assertRaisesRegex(ValueError,'pending, blocked'):validate_review_coverage(self.data)
        checks['checks'][0].update(status='pass',reason='Compared the complete fixture')
        write_json(checks_path,checks)
        with self.assertRaisesRegex(ValueError,'cross_page_checks'):validate_review_coverage(self.data)
        self.data['meta']['cross_page_checks']={name:{'status':'pass','reason':'Compared fixture values'} for name in ('guarantee','pricing')}
        validate_review_coverage(self.data)

    def index_first_page(self, status='issue', refs=None):
        entry=self.data['meta']['pages'][0];path=Path(entry['manifest'])
        capture=json.loads(path.read_text())
        capture.update(schema_version=2,status='complete',index='text.txt',faq_file='text.txt',
            files={name:file_hash(path.parent/name) for name in ('full.png','text.txt','section.png')},
            required_checks=[{'id':'content_and_visuals'}])
        write_json(path,capture)
        checks_path=path.parent/'checks.json';entry['checks_file']=str(checks_path)
        row={'id':'content_and_visuals','status':status,'reason':'Reviewed fixture'}
        if refs is not None:
            row['finding_ids']=refs
        write_json(checks_path,{'manifest_sha256':file_hash(path),'checks':[row]})
        self.data['meta']['cross_page_checks']={name:{'status':'pass','reason':'Compared fixture values'} for name in ('guarantee','pricing')}

    def set_legacy_capture_time(self, value):
        for entry in self.data['meta']['pages']:
            path=Path(entry['manifest']);capture=json.loads(path.read_text())
            capture['captured_at']=value;path.write_text(json.dumps(capture))

    def test_post_cutover_legacy_capture_cannot_back_a_finished_report(self):
        source, output = self.root / "issues.json", self.root / "report.html"
        self.set_legacy_capture_time('2026-10-05T09:00:00+00:00')
        source.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "on/after 2026-10-02"):
            generate(str(source), str(output))
        self.assertFalse(output.exists())
        generate(str(source), str(output), draft=True)  # Diagnostic preview stays possible.
        self.assertIn("DRAFT", output.read_text())
        self.set_legacy_capture_time('2026-10-01T23:59:00+00:00')
        validate_review_coverage(self.data)  # Historical capture: republishing still works.
        self.set_legacy_capture_time('not a date')
        with self.assertRaisesRegex(ValueError, "unreadable captured_at"):
            validate_review_coverage(self.data)

    def test_legacy_capture_cannot_back_a_current_policy_report(self):
        validate_review_coverage(self.data)  # No timestamp, no policy: historical report.
        self.data["meta"]["review_policy_version"] = 3
        with self.assertRaisesRegex(ValueError, "review_policy_version >= 2"):
            validate_review_coverage(self.data)

    def test_legacy_evidence_paths_cannot_escape_the_packet(self):
        (self.root / "outside.png").write_text("not part of this packet")
        path = Path(self.data["meta"]["pages"][2]["manifest"])
        capture = json.loads(path.read_text()); capture["full_page"] = "../outside.png"
        path.write_text(json.dumps(capture))
        with self.assertRaisesRegex(ValueError, "escapes its packet"):
            validate_review_coverage(self.data)

    def test_offer_location_cannot_be_a_blocked_page(self):
        self.data["meta"].update(funnel_type="custom", owner_scope="Owner: custom funnel")
        self.data["meta"]["pages"][1].update(status="blocked", blocker="HTTP 400")
        self.data["meta"]["offer_locations"] = {"competitor": "product", "ours": "product"}
        with self.assertRaisesRegex(ValueError, "blocked page"):
            validate_review_coverage(self.data)
        self.data["meta"]["pages"][1].update(status="reviewed")
        validate_review_coverage(self.data)

    def test_checks_closed_by_owner_decisions_need_real_questions_and_are_reported(self):
        self.index_first_page(refs=['D1'])
        with self.assertRaisesRegex(ValueError, 'existing finding or decision'):
            validate_review_coverage(self.data)  # Unknown decision.
        self.data['decisions'] = [{'id': 'D1', 'page': 'advertorial', 'question': '  '}]
        with self.assertRaisesRegex(ValueError, 'D1 closing check content_and_visuals needs a non-empty question'):
            validate_review_coverage(self.data)
        self.data['decisions'][0]['question'] = 'Keep the original headline?'
        result = validate_review_coverage(self.data)
        self.assertEqual(result['decision_only_checks'],
                         [{'scope': 'competitor/advertorial', 'check': 'content_and_visuals', 'decision_ids': ['D1']}])
        self.data['issues'] = [{'id': 'T1', 'page': 'advertorial'}]
        self.index_first_page(refs=['T1', 'D1'])
        self.assertEqual(validate_review_coverage(self.data)['decision_only_checks'], [])

    def test_advertorial_only_is_rejected_before_writing_report(self):
        self.data["meta"]["pages"] = [p for p in self.data["meta"]["pages"]
                                          if p["page"] == "advertorial"]
        source = self.root / "issues.json"
        output = self.root / "report.html"
        source.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "Incomplete review"):
            generate(str(source), str(output))
        self.assertFalse(output.exists())
        generate(str(source), str(output), draft=True)
        self.assertIn("DRAFT — incomplete or unverified", output.read_text())
        self.assertNotIn("Reviewed: competitor", output.read_text())

    def test_custom_funnel_accepts_blocked_competitor_product_page(self):
        competitor_product = self.data["meta"]["pages"][1]
        self.assertEqual((competitor_product["side"], competitor_product["page"]), ("competitor", "product"))
        competitor_product.update(status="blocked", blocker="Advertorial CTA redirect returned HTTP 400")
        with self.assertRaisesRegex(ValueError, "not reviewed"):
            validate_review_coverage(self.data)
        self.data["meta"]["funnel_type"] = "custom"
        with self.assertRaisesRegex(ValueError, "owner_scope"):
            validate_review_coverage(self.data)
        self.data["meta"]["owner_scope"] = "Owner: custom funnel, PDP reviewed against our advertorial"
        validate_review_coverage(self.data)
        competitor_product["blocker"] = ""
        with self.assertRaisesRegex(ValueError, "blocker"):
            validate_review_coverage(self.data)

    def test_custom_funnel_never_blocks_our_pages(self):
        self.data["meta"].update(funnel_type="custom", owner_scope="Owner: custom funnel")
        self.data["meta"]["pages"][3].update(status="blocked", blocker="Not loaded")
        with self.assertRaisesRegex(ValueError, "not reviewed"):
            validate_review_coverage(self.data)

    def test_report_scope_line_matches_funnel_type(self):
        source, output = self.root / "issues.json", self.root / "report.html"
        source.write_text(json.dumps(self.data))
        generate(str(source), str(output))
        self.assertIn("(4 pages)", output.read_text())
        self.data["meta"].update(funnel_type="custom", owner_scope="Owner: custom funnel")
        self.data["meta"]["pages"][1].update(status="blocked", blocker="HTTP 400")
        source.write_text(json.dumps(self.data))
        generate(str(source), str(output))
        html = output.read_text()
        self.assertNotIn("(4 pages)", html)
        self.assertIn("reviewed against our own advertorial", html)
        self.assertIn("not reachable", html)

    def test_pending_product_capture_is_not_a_review(self):
        self.data["meta"]["pages"][1]["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "not reviewed"):
            validate_review_coverage(self.data)

    def test_missing_capture_evidence_fails(self):
        (self.root / "ours_product" / "section.png").unlink()
        with self.assertRaisesRegex(ValueError, "Missing capture evidence"):
            validate_review_coverage(self.data)

    def test_advertorial_cannot_be_reused_as_product_capture(self):
        pages = self.data["meta"]["pages"]
        pages[1]["manifest"] = pages[0]["manifest"]
        with self.assertRaisesRegex(ValueError, "own capture manifest"):
            validate_review_coverage(self.data)

    def test_mismatched_url_and_unscoped_checkout_issue_are_rejected(self):
        altered = copy.deepcopy(self.data)
        altered["meta"]["pages"][1]["url"] = "https://wrong.example/product"
        with self.assertRaisesRegex(ValueError, "URL does not match"):
            validate_review_coverage(altered)
        self.data["issues"] = [{"page": "checkout"}]
        with self.assertRaisesRegex(ValueError, "prices or offer"):
            validate_review_coverage(self.data)

    def test_complete_report_identifies_scope_and_issue_page(self):
        self.data["issues"] = [{"id": "T5", "page": "product", "description": "Example"}]
        source = self.root / "issues.json"
        output = self.root / "report.html"
        source.write_text(json.dumps(self.data))
        generate(str(source), str(output))
        result = output.read_text()
        self.assertIn("Checkout prices and offers were not reviewed in this run", result)
        self.assertIn("· Product page", result)
        self.assertNotIn("DRAFT", result)

    def test_finding_page_must_match_recorded_target_url(self):
        self.data["issues"] = [{"page": "product", "target_url": "https://ours.example/advertorial"}]
        with self.assertRaisesRegex(ValueError, "target_url does not match"):
            validate_review_coverage(self.data)
        self.data["issues"][0]["page"] = "advertorial"
        validate_review_coverage(self.data)

    def test_off_topic_introduction_requires_actual_replacement(self):
        issue = {"page": "product", "check": "off_topic_introduction"}
        self.data["issues"] = [issue]
        for replacements in ([], [{"find": "Skin-care introduction", "replace": ""}],
                             [{"find": "Same", "replace": "Same"}]):
            issue["replacements"] = replacements
            with self.subTest(replacements=replacements), self.assertRaisesRegex(ValueError, "concrete replacement"):
                validate_review_coverage(self.data)
        issue["replacements"] = [{"find": "Skin-care introduction", "replace": "Relevant product introduction"}]
        validate_review_coverage(self.data)

    def add_checkout(self):
        folder = self.root / "ours_checkout"
        folder.mkdir()
        for name in ("full.png", "text.txt", "section.png"):
            (folder / name).write_text("checkout offer fixture")
        url = "https://ours.example/checkout"
        manifest = folder / "manifest.json"
        manifest.write_text(json.dumps({"url": url, "full_page": "full.png",
            "text_file": "text.txt", "sections": [{"file": "section.png"}]}))
        entry = {"side": "ours", "page": "checkout", "scope": "price_and_offer",
                 "url": url, "manifest": str(manifest), "status": "reviewed"}
        self.data["meta"]["pages"].append(entry)
        self.data["meta"]["offer_locations"] = {"competitor": "product", "ours": "checkout"}
        return entry

    def test_deferred_offer_requires_reviewed_checkout_evidence(self):
        self.data["meta"]["offer_locations"] = {"competitor": "product", "ours": "checkout"}
        with self.assertRaisesRegex(ValueError, "Missing checkout offer review"):
            validate_review_coverage(self.data)
        entry = self.add_checkout()
        validate_review_coverage(self.data)
        entry["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "not reviewed"):
            validate_review_coverage(self.data)

    def test_only_scoped_checkout_findings_are_allowed(self):
        entry = self.add_checkout()
        self.data["issues"] = [{"page": "checkout", "check": "price_and_discount"}]
        validate_review_coverage(self.data)
        self.data["issues"][0]["check"] = "payment_fields"
        with self.assertRaisesRegex(ValueError, "prices or offer"):
            validate_review_coverage(self.data)
        self.data["issues"] = []
        entry["scope"] = "full_checkout"
        with self.assertRaisesRegex(ValueError, "scope must"):
            validate_review_coverage(self.data)

    def test_checkout_does_not_replace_required_product_page(self):
        self.add_checkout()
        self.data["meta"]["pages"] = [p for p in self.data["meta"]["pages"]
                                       if (p["side"], p["page"]) != ("ours", "product")]
        with self.assertRaisesRegex(ValueError, "Incomplete review"):
            validate_review_coverage(self.data)

    def test_checkout_report_describes_only_its_limited_scope(self):
        self.add_checkout()
        self.data["issues"] = [{"id": "T9", "page": "checkout", "check": "offer_presentation"}]
        source, output = self.root / "issues.json", self.root / "report.html"
        source.write_text(json.dumps(self.data))
        generate(str(source), str(output))
        result = output.read_text()
        self.assertIn("Checkout prices and offer presentation reviewed: our funnel", result)
        self.assertIn("Payment flow excluded", result)
        self.assertIn("· Checkout", result)

    def test_review_count_feedback_is_excluded_but_testimonials_remain(self):
        for field in ("issues", "decisions"):
            self.data[field] = [{"page": "product", "check": "review_count"}]
            with self.assertRaisesRegex(ValueError, "Review counts are excluded"):
                validate_review_coverage(self.data)
            self.data[field] = []
        self.data["issues"] = [{"page": "product", "check": "first_testimonial"}]
        validate_review_coverage(self.data)

    def test_footer_email_feedback_is_excluded_but_purchase_buttons_remain(self):
        for field in ("issues", "decisions"):
            self.data[field] = [{"page": "product", "check": "footer_email_link"}]
            with self.assertRaisesRegex(ValueError, "Footer email links are excluded"):
                validate_review_coverage(self.data)
            self.data[field] = []
        self.data["issues"] = [{"page": "product", "check": "purchase_button"}]
        validate_review_coverage(self.data)

    def test_button_text_feedback_is_excluded_but_functional_defects_remain(self):
        for field in ("issues", "decisions"):
            for check in ("button_text", "button_copy", "button_label", "button_translation",
                          "cta_text", "cta_copy", "cta_label", "cta_translation"):
                self.data[field] = [{"page": "product", "check": check}]
                with self.subTest(field=field, check=check), self.assertRaisesRegex(ValueError, "Button text is excluded"):
                    validate_review_coverage(self.data)
            self.data[field] = []
        self.data["issues"] = [{"page": "product", "check": "purchase_button",
            "description": "The footer purchase button opens the wrong product; fix its destination."},
            {"page": "product", "check": "price_and_discount",
             "description": "The offer card total does not match its selected bundle."}]
        validate_review_coverage(self.data)


if __name__ == "__main__":
    unittest.main()
