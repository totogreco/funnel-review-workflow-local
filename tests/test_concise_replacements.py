"""Copy payloads must contain minimal usable edits, preserving the intended result."""

import unittest
from html.parser import HTMLParser

from tools.generate_feedback_page import build_card, concise_replacements


class CopyPayloads(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "button" and "data-copy" in attrs:
            self.values.append(attrs["data-copy"])


class ConciseReplacementTests(unittest.TestCase):
    def check_edits(self, original, corrected, expected):
        edits = concise_replacements(original, corrected)
        self.assertEqual([(e["find"], e["replace"]) for e in edits], expected)
        reconstructed = original
        for edit in reversed(edits):
            self.assertEqual(original[edit["start"]:edit["end"]], edit["find"])
            reconstructed = reconstructed[:edit["start"]] + edit["replace"] + reconstructed[edit["end"]:]
        self.assertEqual(reconstructed, corrected)

    def test_full_sentence_becomes_whole_price_range_in_both_schemas(self):
        old = "€12.827,10 tot €20.984,80"
        new = "€11.000 tot €18.000"
        before = "Een mislukte operatie voor een darmresectie wanneer de situatie echt wanhopig wordt: "
        after = " in de particuliere zorg, met een niet te verwaarlozen complicatiepercentage."
        original, corrected = before + old + after, before + new + after
        self.check_edits(original, corrected, [(old, new)])
        for issue in ({"wrong_text": original, "correct_text": corrected},
                      {"replacements": [{"marker": "C2", "find": original, "replace": corrected,
                                          "action": "Replace this complete line."}]}):
            with self.subTest(issue=issue):
                card = build_card(issue, 1)
                self.assertEqual(CopyPayloads(card).values, [old, new])
                self.assertNotIn("Replace this complete line.", card)
                self.assertIn("At this occurrence:", card)

    def test_price_formats_and_range_endpoints_stay_intact(self):
        for old, new in [("€3.731,52", "€2.500"), ("$3,731.52", "$2,500"),
                         ("12\u202f827,10 €", "11\u202f000 €"), ("60", "90"),
                         ("20%", "30%"), ("€10–€20", "€10–€30")]:
            with self.subTest(old=old):
                self.check_edits(f"Prijs: {old} vandaag.", f"Prijs: {new} vandaag.", [(old, new)])

    def test_separated_changes_get_separate_pairs(self):
        self.check_edits("Het kost €52,47 per maand, dus €629,69 per jaar.",
                         "Het kost €45 per maand, dus €540 per jaar.",
                         [("€52,47", "€45"), ("€629,69", "€540")])

    def test_repeated_text_changes_only_the_identified_occurrence(self):
        old = "mensen zoals Marieke en Marieke in de steek laat"
        new = "mensen zoals Marieke en Anneke in de steek laat"
        edits = concise_replacements(old, new)
        self.check_edits(old, new, [("Marieke", "Anneke")])
        self.assertEqual(edits[0]["start"], old.rindex("Marieke"))
        card = build_card({"replacements": [{"marker": "C", "find": old, "replace": new}]}, 1)
        self.assertIn("mensen zoals Marieke en <mark>Marieke</mark>", card)

    def test_word_change_and_escaped_copy_are_literal(self):
        self.check_edits("In februari vloog ik naar Amsterdam.",
                         "In februari reisde ik naar Amsterdam.", [("vloog", "reisde")])
        card = build_card({"wrong_text": 'Say "word" & <here>', "correct_text": 'Say "word" > <here>'}, 1)
        self.assertEqual(CopyPayloads(card).values, ["&", ">"])
        self.assertIn('data-copy="&amp;"', card)
        self.assertIn('data-copy="&gt;"', card)

    def test_explicit_full_rewrite_preserves_list_structure(self):
        old, new = "✓ Old benefit\n✓ Second benefit", "✓ New benefit\n✓ Second benefit\n✓ Third benefit"
        for issue in ({"wrong_text": old, "correct_text": new, "copy_scope": "full",
                       "copy_scope_reason": "The reordered list must be pasted as one unit."},
                      {"replacements": [{"find": old, "replace": new, "copy_scope": "full",
                                         "copy_scope_reason": "The list structure changes."}]}):
            self.assertEqual(CopyPayloads(build_card(issue, 1)).values, [old, new])
        with self.assertRaisesRegex(ValueError, "copy_scope_reason"):
            concise_replacements(old, new, "full")
        with self.assertRaisesRegex(ValueError, "copy_scope must"):
            concise_replacements(old, new, "unknown")

    def test_insertion_and_whitespace_edits_have_exact_visible_anchors(self):
        self.check_edits("a day", "a good day", [("a day", "a good day")])
        self.check_edits("Headline", "Headline\n\nQuestion?", [("Headline", "Headline\n\nQuestion?")])
        self.check_edits("a  day", "a day", [("a  day", "a day")])
        self.check_edits("Text: a b c.", "Text: a new b other c.", [("b c", "new b other c")])

    def test_addition_deletion_and_noop_do_not_create_empty_copy_buttons(self):
        for issue in ({"wrong_text": "", "correct_text": "Missing heading"},
                      {"replacements": [{"find": "", "replace": "Missing heading"}]}):
            card = build_card(issue, 1)
            self.assertEqual(CopyPayloads(card).values, ["Missing heading"])
            self.assertIn("Copy & paste this addition", card)
        self.check_edits("Today was a bad day for everyone.", "Today was a day for everyone.", [(" bad", "")])
        card = build_card({"wrong_text": "Today was a bad day for everyone.",
                           "correct_text": "Today was a day for everyone."}, 1)
        self.assertEqual(CopyPayloads(card).values, [" bad"])
        self.assertIn("Delete the text above", card)
        self.assertEqual(CopyPayloads(build_card({"wrong_text": "same", "correct_text": "same"}, 1)).values, [])

    def test_split_changes_keep_marker_location_and_leave_input_untouched(self):
        issue = {"replacements": [{"marker": "B8", "find": "€10 a month, €120 a year.",
                                    "replace": "€20 a month, €240 a year.",
                                    "location": "Offer below the testimonial"}]}
        card = build_card(issue, 1)
        self.assertEqual(card.count("<strong>B8</strong>"), 2)
        self.assertIn("change 1 of 2", card)
        self.assertIn("Offer below the testimonial", card)
        self.assertEqual(issue["replacements"][0]["find"], "€10 a month, €120 a year.")

    def test_short_age_phrase_stays_together_in_both_schemas(self):
        old, new = "Marieke is 68", "Marieke is 61"
        self.check_edits(old, new, [(old, new)])
        for issue in ({"wrong_text": old, "correct_text": new},
                      {"replacements": [{"marker": "A", "find": old, "replace": new}]}):
            card = build_card(issue, 1)
            self.assertEqual(CopyPayloads(card).values, [old, new])
            self.assertNotIn("change 1 of", card)
            self.assertNotIn('data-copy="68"', card)
            self.assertNotIn("Anneke", card)

    def test_two_changes_inside_one_short_phrase_are_not_split(self):
        self.check_edits("Marieke is 68", "Anneke is 61", [("Marieke is 68", "Anneke is 61")])

    def test_grouping_preserves_all_related_name_corrections(self):
        pairs = [("Marieke is 68", "Anneke is 61"),
                 ("bij Marieke testte", "bij Anneke testte"),
                 ("Marieke en Marieke", "Marieke en Anneke")]
        card = build_card({"id": "T04", "replacements": [
            {"marker": marker, "find": old, "replace": new}
            for marker, (old, new) in zip(("A", "B", "C"), pairs)]}, 4)
        self.assertEqual(CopyPayloads(card).values, [text for pair in pairs for text in pair])
        for marker in ("A", "B", "C"):
            self.assertEqual(card.count(f"<strong>{marker}</strong>"), 1)
        self.assertNotIn("change 1 of", card)

    def test_explicit_phrase_scope_preserves_context_but_cannot_hide_a_paragraph(self):
        old, new = "Marieke de Vries is 68 jaar", "Marieke de Vries is 61 jaar"
        for issue in ({"wrong_text": old, "correct_text": new, "copy_scope": "phrase",
                       "copy_scope_reason": "Identify the person whose age changes."},
                      {"replacements": [{"find": old, "replace": new, "copy_scope": "phrase",
                                         "copy_scope_reason": "Keep the name and age together."}]}):
            self.assertEqual(CopyPayloads(build_card(issue, 1)).values, [old, new])
        with self.assertRaisesRegex(ValueError, "copy_scope_reason"):
            concise_replacements(old, new, "phrase")
        with self.assertRaisesRegex(ValueError, "one short phrase"):
            concise_replacements("word " * 30, "new " * 30, "phrase", "Too broad")


if __name__ == "__main__":
    unittest.main()
