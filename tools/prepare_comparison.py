#!/usr/bin/env python3
"""Prepare captured facts for agent comparison; never decide semantic equivalence."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

try:
    from .locate_evidence import candidates, load_index, locate_many, merge_lines, normalized
    from .review_io import child_path, digest, file_hash, verify_files, write_json
except ImportError:
    from locate_evidence import candidates, load_index, locate_many, merge_lines, normalized
    from review_io import child_path, digest, file_hash, verify_files, write_json


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def safe_id(value):
    return isinstance(value, str) and value not in ('', '.', '..') and all(
        c.isalnum() or c in '_-' for c in value)


def runs(block):
    """Compact inline styles while retaining source offsets, including plain text."""
    result = []
    for token in block['tokens']:
        key = (token.get('style_id'), token.get('element_path'), token['bold'])
        if result and result[-1]['key'] == key:
            result[-1]['end'] = token['end']
        else:
            result.append({'key': key, 'start': token['start'], 'end': token['end']})
    return [{'start': r['start'], 'end': r['end'], 'text': block['text'][r['start']:r['end']],
             'style_id': r['key'][0], 'element_path': r['key'][1], 'bold': r['key'][2]}
            for r in result]


def load_page(manifest_path, prefix):
    path = Path(manifest_path).resolve()
    manifest = read_json(path)
    page = {'manifest_path': str(path), 'manifest_sha256': file_hash(path),
            'url': manifest['url'], 'states': [], 'sections': [], 'warnings': []}
    if manifest.get('schema_version') != 2:
        # Legacy material remains readable but cannot acquire indexed evidence claims.
        page.update(status='legacy_manual_review', text_path=str(child_path(path.parent,
                    manifest.get('text_file', 'text_content.txt'))),
                    image_path=str(child_path(path.parent, manifest.get('full_page', 'full_page.png'))))
        page['warnings'].append('Legacy capture: no verified block references or visual attributes. Recapture for indexed comparison.')
        return page
    if manifest.get('status') != 'complete':
        raise ValueError(f'Incomplete capture: {path}')
    verify_files(path.parent, manifest['files'])
    for section in manifest.get('sections', []):
        if section['file'] not in manifest['files']:
            raise ValueError('Section image is not bound to the capture manifest')
        page['sections'].append(dict(section, image_path=str(child_path(path.parent, section['file']))))
    states = [{'state_id': 'full_page', 'index': manifest['index']}] + manifest.get('faq_states', [])
    state_ids = set()
    for state in states:
        name = state['state_id']
        if name in state_ids or not safe_id(name):
            raise ValueError('Capture state IDs must be unique safe IDs')
        state_ids.add(name)
        if state['index'] not in manifest['files']:
            raise ValueError('State index is not bound to the capture manifest')
        index_path = child_path(path.parent, state['index'])
        index, image = load_index(index_path)
        if index['state_id'] != name:
            raise ValueError('Capture state/index mismatch')
        blocks = []
        ids = set()
        for position, block in enumerate(index['blocks']):
            if block['id'] in ids:
                raise ValueError('Duplicate block ID in capture')
            ids.add(block['id'])
            # Restrict search to this block: no quadratic whole-page substring scan.
            match = candidates({'snapshot_id': index['snapshot_id'], 'blocks': [block]},
                               {'find': block['text'], 'block_id': block['id']})
            if len(match) != 1:
                raise ValueError('Indexed block has no unique full-text occurrence')
            tiles = [s['image_path'] for s in page['sections'] if name == 'full_page'
                     and s['scroll_y'] < block['rect']['y']+block['rect']['h']
                     and s['scroll_y']+manifest['viewport']['height'] > block['rect']['y']]
            blocks.append({'ref': f'{prefix}/{name}/{block["id"]}', 'position': position,
                'tag': block['tag'], 'heading': block['heading'], 'text': block['text'],
                'screenshot_paths': tiles or [str(image)],
                'rect': block['rect'], 'style_id': block.get('style_id'),
                'container_paths': block.get('container_paths', []), 'inline_runs': runs(block),
                'line_count': len(merge_lines([r for t in block['tokens'] for r in t['rects']])),
                'evidence_query': {'find': block['text'], 'block_id': block['id'],
                                   'occurrence_id': match[0]['occurrence_id']}})
        page['states'].append({'state_id': name, 'index_path': str(index_path),
            'index_sha256': file_hash(index_path), 'snapshot_id': index['snapshot_id'],
            'image_path': str(image), 'image_sha256': index['files'][index['image']],
            'origin': index['origin'], 'device_scale_factor': index['device_scale_factor'],
            'visual_attributes_available': index.get('visual_schema_version') == 1,
            'styles': index.get('styles', {}), 'containers': index.get('containers', {}),
            'images': index.get('images', []), 'controls': index.get('controls', []), 'blocks': blocks})
    page['status'] = 'indexed'
    if any(not s['visual_attributes_available'] for s in page['states']):
        page['warnings'].append('Older index: geometry/bold available; other visual attributes unknown. Inspect screenshots or recapture.')
    return page


def references(packet):
    return {b['ref']: (pair['id'], side, state, b) for pair in packet['pairs']
            for side in ('source', 'target') for state in pair[side]['states'] for b in state['blocks']}


def suggestions(source, target):
    """Exact text or nearby reading positions are candidates, never confirmed matches."""
    exact = defaultdict(list)
    for block in target:
        exact[normalized(block['text'])[0].strip()].append(block['ref'])
    result = []
    for i, block in enumerate(source):
        same = exact[normalized(block['text'])[0].strip()]
        center = round(i * (len(target)-1) / max(1, len(source)-1))
        nearby = target[max(0, center-1):center+2] if target else []
        result.append({'source_ref': block['ref'], 'target_candidates': same or [b['ref'] for b in nearby],
                       'basis': 'exact_text_only' if same else 'relative_reading_position_only',
                       'status': 'unconfirmed'})
    return result


def apply_alignment(packet, alignment):
    if alignment.get('input_fingerprint') != packet['input_fingerprint']:
        raise ValueError('Stale alignment: regenerate against the current comparison inputs')
    refs = references(packet)
    used, ids, confirmed = set(), set(), []
    for mapping in alignment.get('mappings', []):
        if not safe_id(mapping.get('id')) or mapping['id'] in ids:
            raise ValueError('Mapping IDs must be unique safe IDs')
        ids.add(mapping['id'])
        if not isinstance(mapping.get('reason'), str) or not mapping['reason'].strip():
            raise ValueError('Agent-confirmed mappings need a reason, including absent/extra content')
        pair_ids = set()
        for side in ('source', 'target'):
            values = mapping.get(side, [])
            if not isinstance(values, list):
                raise ValueError('Mappings require source/target reference arrays')
            for ref in values:
                if ref not in refs or refs[ref][1] != side or ref in used:
                    raise ValueError('Unknown, wrong-side or reused alignment reference')
                pair_ids.add(refs[ref][0]); used.add(ref)
        if len(pair_ids) != 1:
            raise ValueError('Each mapping must contain content from exactly one page pair')
        # Record measurements without calling differences defects or applying a tolerance.
        facts = {side: [{'ref': ref, 'rect': refs[ref][3]['rect'],
                        'line_count': refs[ref][3]['line_count'],
                        'style': refs[ref][2]['styles'].get(refs[ref][3]['style_id']),
                        'inline_runs': refs[ref][3]['inline_runs']}
                       for ref in mapping.get(side, [])] for side in ('source', 'target')}
        confirmed.append(dict(mapping, pair_id=next(iter(pair_ids)), status='agent_confirmed', visual_facts=facts))
    packet['mappings'] = confirmed
    packet['unmapped_refs'] = [ref for ref in refs if ref not in used]
    for pair in packet['pairs']:
        for component in pair['components']:
            component['mapping_ids'] = [m['id'] for m in confirmed
                if m['pair_id'] == pair['id'] and m.get('role') == component['role']]
            # A role assignment cannot attest quality or even completeness of a component.
            component['status'] = 'pending_review'


def prepare(config, base_dir=Path('.'), alignment=None):
    started = time.monotonic()
    pairs, ids = [], set()
    for spec in config['pairs']:
        if not safe_id(spec.get('id')) or spec['id'] in ids:
            raise ValueError('Page pair IDs must be unique safe IDs')
        ids.add(spec['id'])
        pair = {'id': spec['id'], 'page': spec['page'], 'components': []}
        roles = spec.get('components', [])
        if not isinstance(roles, list) or any(not safe_id(r) for r in roles) or len(roles) != len(set(roles)):
            raise ValueError('Component roles must be unique safe IDs supplied by the agent')
        pair['components'] = [{'role': r, 'status': 'pending_review', 'mapping_ids': []} for r in roles]
        for side in ('source', 'target'):
            pair[side] = load_page(Path(base_dir) / spec[side], f'{spec["id"]}/{side}')
        # States are separate inventories. FAQ ordering/labels may differ across languages.
        source = next((s['blocks'] for s in pair['source']['states'] if s['state_id'] == 'full_page'), [])
        target = next((s['blocks'] for s in pair['target']['states'] if s['state_id'] == 'full_page'), [])
        pair['suggestions'] = suggestions(source, target)
        pairs.append(pair)
    if not pairs:
        raise ValueError('At least one page pair is required')
    packet = {'schema_version': 1, 'context': config.get('context', {}), 'pairs': pairs,
              'status': 'prepared_not_reviewed', 'mappings': [],
              'limitations': ['Suggestions do not establish translated meaning or component roles.',
                  'FAQ states require agent pairing; controls remain untested inventories.',
                  'Screenshots, image text, live interactions and cross-page checks still require review.']}
    packet['input_fingerprint'] = digest({'config': config, 'tool': file_hash(__file__),
        'inputs': [[p[side]['manifest_path'], p[side]['manifest_sha256']]
                   for p in pairs for side in ('source', 'target')]})
    packet['unmapped_refs'] = list(references(packet))
    if alignment is not None:
        apply_alignment(packet, alignment)
    packet['duration_seconds'] = time.monotonic()-started
    return packet


def evidence_plan(packet, selections, evidence_dir):
    """Reuse exact locations chosen during review, verifying saved inputs again."""
    if selections.get('input_fingerprint') != packet['input_fingerprint']:
        raise ValueError('Stale evidence selections')
    refs, groups, ids = references(packet), defaultdict(list), set()
    for selection in selections['items']:
        name, ref = selection.get('id'), selection.get('ref')
        if not safe_id(name) or name in ids or ref not in refs:
            raise ValueError('Selections need unique safe IDs and known block references')
        ids.add(name)
        _, side, state, block = refs[ref]
        query = dict(block['evidence_query'], id=name, color='green' if side == 'source' else 'red',
                     decision_context={'comparison_fingerprint': packet['input_fingerprint'], 'ref': ref})
        # Optional narrower phrase remains pinned to this exact block, with fresh ambiguity checks.
        if 'find' in selection:
            query['find'] = selection['find']; query.pop('occurrence_id')
        groups[(state['index_path'], state['index_sha256'])].append(query)
    jobs = []
    for (index_path, expected), queries in groups.items():
        if file_hash(index_path) != expected:
            raise ValueError('Evidence index changed after comparison preparation')
        jobs.extend(locate_many(index_path, queries, evidence_dir)['jobs'])
    if not jobs:
        raise ValueError('Select at least one evidence reference')
    return {'schema_version': 2, 'jobs': jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, help='Page pairs and agent-supplied component roles')
    parser.add_argument('--output', required=True)
    parser.add_argument('--alignment', help='Agent-confirmed many-to-many block mapping')
    parser.add_argument('--selections', help='Evidence selections made while reviewing')
    parser.add_argument('--plan', help='Output annotation plan for selected evidence')
    parser.add_argument('--evidence-dir', default='.tmp/evidence')
    args = parser.parse_args()
    if bool(args.selections) != bool(args.plan):
        parser.error('--selections and --plan must be supplied together')
    config_path = Path(args.config).resolve()
    packet = prepare(read_json(config_path), config_path.parent,
                     read_json(args.alignment) if args.alignment else None)
    plan = evidence_plan(packet, read_json(args.selections), args.evidence_dir) if args.selections else None
    # Do not overwrite input captures or decision files with generated artifacts.
    protected = {config_path, *(Path(p).resolve() for p in (args.alignment, args.selections) if p)}
    for pair in packet['pairs']:
        for side in ('source', 'target'):
            manifest_path = Path(pair[side]['manifest_path'])
            protected.add(manifest_path)
            protected.update(Path(pair[side][key]) for key in ('image_path', 'text_path') if key in pair[side])
            protected.update(child_path(manifest_path.parent, p) for p in read_json(manifest_path).get('files', {}))
    outputs = [Path(p).resolve() for p in (args.output, args.plan) if p]
    if len(outputs) != len(set(outputs)) or any(p in protected for p in outputs):
        parser.error('Output paths must be distinct and must not overwrite inputs')
    write_json(args.output, packet)
    if plan is not None:
        write_json(args.plan, plan)
    print(json.dumps({'packet': args.output, 'pairs': len(packet['pairs']),
        'blocks': len(references(packet)), 'unmapped_blocks': len(packet['unmapped_refs']),
        'duration_seconds': round(packet['duration_seconds'], 3),
        'warnings': [w for p in packet['pairs'] for side in ('source', 'target') for w in p[side]['warnings']]}))


if __name__ == '__main__':
    main()
