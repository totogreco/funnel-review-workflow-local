"""Comparison preparation must preserve omissions, role distinctions and evidence identity."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from tools.prepare_comparison import prepare, references, evidence_plan
from tools.locate_evidence import locate_many
from tools.annotate_screenshot import annotate_batch
from tools.review_io import file_hash, write_json


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.capture('source', ['Source first review', 'Repeated', 'Repeated', 'Last paragraph'])
        self.target = self.capture('target', ['Wrong first review', 'Repeated', 'Source first review', 'Extra paragraph'])
        self.config = {'context': {'template': 'owner-confirmed Swedish beauty'}, 'pairs': [
            {'id': 'product', 'page': 'product', 'source': str(self.source), 'target': str(self.target),
             'components': ['first_testimonial', 'doctor_verified', 'offer_cards']}]}

    def capture(self, name, texts, visual=True):
        folder = self.root/name; folder.mkdir()
        image = folder/'full.png'; Image.new('RGB', (780, 2400), 'white').save(image)
        blocks = []
        for i, text in enumerate(texts):
            rect = {'x': 20, 'y': 100+i*80, 'w': 300, 'h': 22}
            blocks.append({'id': f'b{i}', 'tag': 'p', 'text': text, 'heading': '', 'rect': rect,
                'style_id': 's0', 'tokens': [{'start': 0, 'end': len(text), 'rects': [rect],
                                            'bold': False, 'style_id': 's0'}]})
        index = {'schema_version': 2, 'state_id': 'full_page', 'snapshot_id': name,
            'image': 'full.png', 'image_size': [780, 2400], 'device_scale_factor': 2,
            'origin': {'x': 0, 'y': 0}, 'files': {'full.png': file_hash(image)}, 'blocks': blocks,
            'styles': {'s0': {'fontSize': '18px', 'fontWeight': '400'}}}
        if visual:
            index['visual_schema_version'] = 1
        write_json(folder/'index.json', index)
        write_json(folder/'manifest.json', {'schema_version': 2, 'status': 'complete',
            'url': 'https://example.com/'+name, 'index': 'index.json', 'faq_states': [],
            'files': {p.name: file_hash(p) for p in (image, folder/'index.json')}})
        return folder/'manifest.json'

    def mapping(self, packet):
        return {'input_fingerprint': packet['input_fingerprint'], 'mappings': [
            {'id': 'first', 'source': ['product/source/full_page/b0'],
             'target': ['product/target/full_page/b0'], 'role': 'first_testimonial',
             'reason': 'Match actual first visible slots, not the duplicate quote lower down.'},
            {'id': 'doctor', 'source': [], 'target': ['product/target/full_page/b2'],
             'role': 'doctor_verified', 'reason': 'Customer quote currently occupies target template doctor block.'}]}

    def test_candidates_never_confirm_or_hide_unmatched_content(self):
        packet = prepare(self.config)
        self.assertEqual(len(packet['unmapped_refs']), 8)
        pair = packet['pairs'][0]
        # Exact text suggests the wrong slot; no automated semantic approval is granted.
        self.assertEqual(pair['suggestions'][0]['target_candidates'], ['product/target/full_page/b2'])
        self.assertTrue(all(s['status'] == 'unconfirmed' for s in pair['suggestions']))
        self.assertEqual(packet['mappings'], [])
        self.assertTrue(all(c['status'] == 'pending_review' for c in pair['components']))

    def test_role_mapping_overrides_suggestion_without_passing_review(self):
        initial = prepare(self.config)
        packet = prepare(self.config, alignment=self.mapping(initial))
        self.assertEqual(len(packet['unmapped_refs']), 5)
        self.assertIn('product/source/full_page/b3', packet['unmapped_refs'])
        components = packet['pairs'][0]['components']
        self.assertEqual(components[0]['mapping_ids'], ['first'])
        self.assertEqual(components[1]['mapping_ids'], ['doctor'])
        self.assertEqual(components[2]['mapping_ids'], [])
        self.assertTrue(all(c['status'] == 'pending_review' for c in components))
        self.assertEqual(packet['mappings'][0]['visual_facts']['target'][0]['style']['fontSize'], '18px')

    def test_split_paragraphs_and_one_sided_content_are_supported(self):
        packet = prepare(self.config)
        alignment = {'input_fingerprint': packet['input_fingerprint'], 'mappings': [
            {'id': 'split', 'source': ['product/source/full_page/b1'],
             'target': ['product/target/full_page/b1', 'product/target/full_page/b2'], 'reason': 'Split paragraphs'},
            {'id': 'missing', 'source': ['product/source/full_page/b3'], 'target': [], 'reason': 'Absent after complete review'}]}
        result = prepare(self.config, alignment=alignment)
        self.assertEqual(len(result['unmapped_refs']), 4)

    def test_stale_alignment_unknown_wrong_side_and_reused_refs_rejected(self):
        packet = prepare(self.config)
        alignment = self.mapping(packet)
        for value in ('missing', 'product/source/full_page/b1', 'product/target/full_page/b0'):
            bad = copy.deepcopy(alignment); bad['mappings'][1]['target'] = [value]
            with self.assertRaises(ValueError): prepare(self.config, alignment=bad)
        changed = copy.deepcopy(self.config); changed['context']['template'] = 'different template'
        with self.assertRaisesRegex(ValueError, 'Stale'): prepare(changed, alignment=alignment)
        changed = copy.deepcopy(alignment); changed['mappings'][0]['reason'] = ''
        with self.assertRaisesRegex(ValueError, 'reason'): prepare(self.config, alignment=changed)

    def test_duplicate_text_evidence_is_pinned_and_batched(self):
        packet = prepare(self.config)
        selected = {'input_fingerprint': packet['input_fingerprint'], 'items': [
            {'id': 'a', 'ref': 'product/source/full_page/b1'},
            {'id': 'b', 'ref': 'product/source/full_page/b2'},
            {'id': 'c', 'ref': 'product/target/full_page/b0'}]}
        with patch('tools.prepare_comparison.locate_many', wraps=locate_many) as locate:
            plan = evidence_plan(packet, selected, self.root/'evidence')
            self.assertEqual(locate.call_count, 2)  # Once per distinct index, not per issue.
        self.assertNotEqual(plan['jobs'][0]['occurrence_id'], plan['jobs'][1]['occurrence_id'])
        self.assertNotEqual(plan['jobs'][0]['highlights'], plan['jobs'][1]['highlights'])
        self.assertEqual([j['color'] for j in plan['jobs']], ['green', 'green', 'red'])
        receipt = annotate_batch(plan, self.root/'receipt.json')
        self.assertEqual(receipt['status'], 'complete')

    def test_modified_index_or_image_cannot_reuse_packet_evidence(self):
        packet = prepare(self.config)
        selected = {'input_fingerprint': packet['input_fingerprint'],
                    'items': [{'id': 'a', 'ref': 'product/source/full_page/b0'}]}
        image = self.source.parent/'full.png'; image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed'): evidence_plan(packet, selected, self.root)
        with self.assertRaisesRegex(ValueError, 'changed'): prepare(self.config)

    def test_modified_index_is_rejected_before_evidence_resolution(self):
        packet = prepare(self.config)
        selected = {'input_fingerprint': packet['input_fingerprint'],
                    'items': [{'id': 'a', 'ref': 'product/source/full_page/b0'}]}
        with (self.source.parent/'index.json').open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'index changed'):
            evidence_plan(packet, selected, self.root)

    def test_blocks_link_all_intersecting_section_screenshots(self):
        import json
        manifest = json.loads(self.source.read_text())
        manifest['viewport'] = {'height': 110}
        manifest['sections'] = [{'file': 'full.png', 'scroll_y': 0},
                                {'file': 'full.png', 'scroll_y': 110}]
        write_json(self.source, manifest)
        block = references(prepare(self.config))['product/source/full_page/b0'][3]
        self.assertEqual(len(block['screenshot_paths']), 2)

    def test_legacy_and_old_indexes_explicitly_report_missing_facts(self):
        legacy = self.root/'legacy.json'; write_json(legacy, {'url': 'https://example.com/legacy'})
        self.config['pairs'][0]['target'] = str(legacy)
        packet = prepare(self.config)
        self.assertEqual(packet['pairs'][0]['target']['status'], 'legacy_manual_review')
        self.assertEqual(len(references(packet)), 4)
        old = self.capture('old', ['Old capture'], visual=False)
        self.config['pairs'][0]['target'] = str(old)
        page = prepare(self.config)['pairs'][0]['target']
        self.assertFalse(page['states'][0]['visual_attributes_available'])
        self.assertIn('unknown', page['warnings'][0])

    def test_expanded_faqs_keep_separate_state_refs(self):
        import json
        index_path = self.source.parent/'index.json'
        index = json.loads(index_path.read_text()); index['state_id'] = 'faq_001'
        index['snapshot_id'] = 'expanded'; write_json(self.source.parent/'faq.index.json', index)
        manifest = json.loads(self.source.read_text())
        manifest['files']['faq.index.json'] = file_hash(self.source.parent/'faq.index.json')
        manifest['faq_states'] = [{'state_id': 'faq_001', 'index': 'faq.index.json'}]
        write_json(self.source, manifest)
        packet = prepare(self.config)
        self.assertEqual(len(references(packet)), 12)
        self.assertIn('product/source/faq_001/b0', packet['unmapped_refs'])
        self.assertEqual(len(packet['pairs'][0]['suggestions']), 4)


if __name__ == '__main__':
    unittest.main()
