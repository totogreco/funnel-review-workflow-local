"""Regression checks for context crops and exact internal highlight geometry."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.annotate_screenshot import COLORS, annotate
from tools.generate_feedback_page import build_card


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source.png"
        self.output = Path(self.temp.name) / "nested" / "issue.png"
        Image.new("RGB", (780, 1688), "white").save(self.source)

    def test_auto_context_retains_pixels_and_marks_only_issue(self):
        annotate(self.source, self.output, highlights=[[20, 700, 740, 180]])
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (780, 1170))
            self.assertEqual(image.getpixel((100, 495)), COLORS["red"])
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(image.getpixel((100, 350)), (255, 255, 255))

    def test_explicit_crop_translates_multiple_original_coordinates(self):
        annotate(self.source, self.output, region=[10, 400, 760, 1200],
                 highlights=[[20, 700, 740, 100], [20, 900, 740, 100]])
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (760, 1200))
            self.assertEqual(image.getpixel((100, 300)), COLORS["red"])
            self.assertEqual(image.getpixel((100, 500)), COLORS["red"])

    def test_page_edge_clamps_context_without_clipping_highlight(self):
        annotate(self.source, self.output, highlights=[[20, 10, 740, 100]])
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (780, 1170))
            self.assertEqual(image.getpixel((100, 10)), COLORS["red"])

    def test_invalid_or_misleading_geometry_is_rejected(self):
        cases = [
            {},
            {"highlights": [[20, 1700, 100, 50]]},
            {"highlights": [[20, 700, 740, 100]], "region": [0, 0, 780, 750]},
            {"highlights": [[0, 500, 780, 500]], "region": [0, 500, 780, 500]},
            {"highlights": [[20, 700, -10, 100]]},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                annotate(self.source, self.output, **kwargs)
        self.assertFalse(self.output.exists())

    def test_source_is_preserved(self):
        with self.assertRaises(ValueError):
            annotate(self.source, self.source, highlights=[[20, 700, 740, 100]])

    def test_overlapping_or_touching_highlights_are_rejected(self):
        for second in [[20,740,600,60],[20,760,600,60],[30,710,100,30]]:
            with self.subTest(second=second), self.assertRaisesRegex(ValueError,'overlap or touch'):
                annotate(self.source,self.output,highlights=[[20,700,650,60],second])

    def test_small_padding_cannot_produce_a_contextless_strip(self):
        annotate(self.source, self.output, highlights=[[20, 700, 740, 100]], context_padding=100)
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (780, 1170))
        with self.assertRaisesRegex(ValueError, "too tight"):
            annotate(self.source, self.output, region=[0, 600, 780, 300], highlights=[[20, 700, 740, 100]])

    def test_missing_content_uses_a_line_without_boxing_adjacent_text(self):
        annotate(self.source, self.output, region=[0, 400, 780, 1200], insertion_lines=[[30, 720, 690]])
        with Image.open(self.output) as image:
            self.assertEqual(image.getpixel((30, 320)), COLORS["red"])
            self.assertEqual(image.getpixel((719, 325)), COLORS["red"])
            self.assertEqual(image.getpixel((30, 326)), (255, 255, 255))
            self.assertEqual(image.getpixel((30, 400)), (255, 255, 255))
        for line in ([10, 20], [10, 1685, 100], [10, 20, -5], [10, 20, 900]):
            with self.subTest(line=line), self.assertRaises(ValueError):
                annotate(self.source, self.output, insertion_lines=[line])
        with self.assertRaisesRegex(ValueError, "cuts off"):
            annotate(self.source, self.output, region=[0, 400, 780, 1200], insertion_lines=[[30, 200, 690]])

    def test_short_source_retains_all_available_context(self):
        Image.new("RGB", (780, 500), "white").save(self.source)
        annotate(self.source, self.output, insertion_lines=[[30, 100, 690]])
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (780, 500))

    def test_evidence_captions_explain_missing_content_marker(self):
        card = build_card({"id": "T06", "evidence_pairs": [{"marker": "A",
                           "source_screenshot": str(self.source), "target_screenshot": str(self.source),
                           "source_caption": "Source: existing subheadline",
                           "target_caption": "Target: insert <here> at red line"}]}, 1)
        self.assertIn("<figcaption>Source: existing subheadline</figcaption>", card)
        self.assertIn("<figcaption>Target: insert &lt;here&gt; at red line</figcaption>", card)

    def test_corrected_card_keeps_id_and_exact_copy(self):
        card = build_card({"id": "T5", "wrong_text": 'Text with "quotes" & <tags>',
                           "correct_text": "Replacement", "screenshot": str(self.source)}, 1)
        self.assertIn('class="badge">T5<', card)
        self.assertIn('data-copy="Text with &quot;quotes&quot; &amp; &lt;tags&gt;"', card)
        self.assertIn('alt="T5:', card)

    def test_each_evidence_pair_is_followed_by_its_own_edits(self):
        pairs = [{"id": key, "marker": key + " · Screenshot",
                  "source_screenshot": str(self.source), "target_screenshot": str(self.source)}
                 for key in ("A", "B")]
        card = build_card({"evidence_pairs": pairs, "replacements": [
            {"marker": "B", "find": "old second", "replace": "new second", "evidence_ids": ["B"]},
            {"marker": "A", "find": "old first", "replace": "new first", "evidence_ids": ["A"]},
            {"marker": "A2", "find": "old extra", "replace": "new extra", "evidence_ids": ["A"]},
        ]}, 1)
        self.assertLess(card.index('alt="T1 A'), card.index('data-copy="new first"'))
        self.assertLess(card.index('data-copy="new extra"'), card.index('alt="T1 B'))
        self.assertLess(card.index('alt="T1 B'), card.index('data-copy="new second"'))
        self.assertEqual(card.count('data-copy="new first"'), 1)

    def test_repeated_edit_is_shown_under_each_applicable_screenshot(self):
        pairs = [{"marker": key + " · Rows", "source_screenshot": str(self.source),
                  "target_screenshot": str(self.source)} for key in ("A", "B")]
        card = build_card({"evidence_pairs": pairs, "replacements": [
            {"find": "Comment", "replace": "Kommentera", "evidence_ids": ["A", "B"]}]}, 1)
        self.assertEqual(card.count('data-copy="Kommentera"'), 2)
        self.assertLess(card.index('data-copy="Kommentera"'), card.index('alt="T1 B'))

    def test_ambiguous_or_invalid_evidence_mapping_fails(self):
        pairs = [{"id": key, "source_screenshot": str(self.source),
                  "target_screenshot": str(self.source)} for key in ("A", "B")]
        for refs in (None, [], ["missing"], "A", ["A", "A"]):
            replacement = {"find": "old", "replace": "new"}
            if refs is not None:
                replacement["evidence_ids"] = refs
            with self.subTest(refs=refs), self.assertRaisesRegex(ValueError, "evidence_ids"):
                build_card({"evidence_pairs": pairs, "replacements": [replacement]}, 1)

    def test_legacy_marker_matching_and_single_pair_copy_are_preserved(self):
        pairs = [{"marker": key + " · Location", "source_screenshot": str(self.source),
                  "target_screenshot": str(self.source)} for key in ("A", "B")]
        card = build_card({"evidence_pairs": pairs, "replacements": [
            {"marker": "B", "find": "second", "replace": "corrected"}]}, 1)
        self.assertLess(card.index('alt="T1 B'), card.index('data-copy="corrected"'))
        card = build_card({"evidence_pairs": pairs[:1], "wrong_text": "old", "correct_text": "new"}, 1)
        self.assertEqual(card.count('data-copy="new"'), 1)

    def test_target_only_evidence_keeps_its_instructions(self):
        card = build_card({"id": "V05", "category": "visual", "evidence_pairs": [
            {"id": "A", "target_screenshot": str(self.source), "target_caption": "Existing specialty"}],
            "replacements": [{"evidence_ids": ["A"], "find": "dermatolog",
                              "replace": "specialist i gastroenterologi"}]}, 1)
        self.assertIn('evidence-single', card)
        self.assertNotIn('Source reference', card)
        self.assertLess(card.index('<img'), card.index('data-copy="dermatolog"'))

    def test_instruction_only_testimonial_feedback_follows_its_evidence(self):
        pairs = [{"id": key, "marker": key, "source_screenshot": str(self.source),
                  "target_screenshot": str(self.source),
                  "instruction": f'Replace review {key} with a translation of the source <quote> & retain its meaning.'}
                 for key in ("A", "B")]
        card = build_card({"id": "T17", "evidence_pairs": pairs}, 17)
        self.assertLess(card.index('alt="T17 A: Dutch target"'), card.index('Replace review A'))
        self.assertLess(card.index('Replace review A'), card.index('alt="T17 B:'))
        self.assertLess(card.index('alt="T17 B: Dutch target"'), card.index('Replace review B'))
        self.assertIn('&lt;quote&gt; &amp; retain', card)
        self.assertNotIn('data-copy=', card)
        self.assertNotIn('class="replacements"', card)
        with self.assertRaisesRegex(ValueError, "instruction must be a string"):
            build_card({"evidence_pairs": [{**pairs[0], "instruction": {"text": "invalid"}}]}, 1)

    def test_missing_comments_can_use_source_screenshots_without_copy_blocks(self):
        card = build_card({"id": "D04", "description": "These comments are missing. Add them to our funnel.",
            "evidence_pairs": [{"id": key, "source_screenshot": str(self.source),
                                "source_caption": f"Missing comments {key}"} for key in ("A", "B")]}, 1)
        self.assertEqual(card.count('<img '), 2)
        self.assertEqual(card.count('evidence-single'), 2)
        self.assertNotIn('Dutch target', card)
        self.assertNotIn('data-copy=', card)
        self.assertIn('Add them to our funnel.', card)
        with self.assertRaisesRegex(ValueError, "requires a source or target screenshot"):
            build_card({"evidence_pairs": [{"id": "A"}]}, 1)

    def test_fragment_replacement_copies_the_complete_price_range_only(self):
        card = build_card({"replacements": [{"marker": "C2",
            "find": "€12.827,10 tot €20.984,80", "replace": "€11.000 tot €18.000"}]}, 1)
        self.assertIn('data-copy="€12.827,10 tot €20.984,80"', card)
        self.assertIn('data-copy="€11.000 tot €18.000"', card)

    def test_addition_has_no_empty_find_block(self):
        card = build_card({"replacements": [{"marker": "A", "find": "",
            "replace": "Missing subheadline", "action": "Insert below the headline."}]}, 1)
        self.assertNotIn('class="text-block wrong"', card)
        self.assertNotIn('data-copy=""', card)
        self.assertIn('Copy & paste this addition', card)
        self.assertIn('data-copy="Missing subheadline"', card)


if __name__ == "__main__":
    unittest.main()
