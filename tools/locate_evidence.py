#!/usr/bin/env python3
"""Resolve exact occurrences from a verified capture index into annotation jobs."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image
try:
    from .review_io import child_path, digest, file_hash, verify_files, write_json
except ImportError:
    from review_io import child_path, digest, file_hash, verify_files, write_json


def normalized(text):
    """Whitespace/typographic equivalence with offsets into immutable raw text."""
    chars, offsets = [], []
    for i, char in enumerate(text):
        if char in '\u200b\ufeff':
            continue
        char = {"’": "'", "‘": "'", "–": "-", "\u00a0": " "}.get(char, char)
        if char.isspace():
            char = ' '
            if chars and chars[-1] == ' ':
                continue
        chars.append(char)
        offsets.append(i)
    return ''.join(chars), offsets


def load_index(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 2:
        raise ValueError('A version 2 capture index is required')
    verify_files(path.parent, data['files'])
    image = child_path(path.parent, data['image'])
    if data['image'] not in data['files']:
        raise ValueError('Index image must be hash verified')
    with Image.open(image) as source:
        if list(source.size) != data['image_size'] or data['device_scale_factor'] <= 0:
            raise ValueError('Index image dimensions or scale are invalid')
    return data, image


def candidates(index, query):
    needle, _ = normalized(query.get('find', ''))
    if not needle.strip():
        raise ValueError('Supply find text, or an explicit insertion anchor')
    result = []
    for block in index['blocks']:
        if query.get('block_id') and query['block_id'] != block['id']:
            continue
        if query.get('heading') and normalized(query['heading'])[0] not in normalized(block['heading'])[0]:
            continue
        text, offsets = normalized(block['text'])
        start = 0
        while True:
            pos = text.find(needle, start)
            if pos < 0:
                break
            raw_start, raw_end = offsets[pos], offsets[pos+len(needle)-1]+1
            # Context is checked on this block; it is never used to select a nearby block.
            if not query.get('context') or normalized(query['context'])[0] in text:
                token_rects = [r for token in block['tokens']
                               if token['end'] > raw_start and token['start'] < raw_end
                               for r in token['rects']]
                result.append({'block_id': block['id'], 'heading': block['heading'],
                    'start': raw_start, 'end': raw_end, 'text': block['text'][raw_start:raw_end],
                    'context': block['text'], 'rects': token_rects, 'block_rect': block['rect'],
                    'occurrence_id': digest([index['snapshot_id'], block['id'], raw_start, raw_end])[:24]})
            start = pos + max(1, len(needle))
    return result


def merge_lines(rects):
    lines = []
    for r in sorted(rects, key=lambda r: (round(r['y'], 1), r['x'])):
        line = next((v for v in lines if abs(v['y']-r['y']) < 2 and abs(v['h']-r['h']) < 3
                     and r['x'] <= v['x']+v['w']+12), None)
        if line:
            right = max(line['x']+line['w'], r['x']+r['w'])
            line['x'] = min(line['x'], r['x']); line['w'] = right-line['x']
            line['h'] = max(line['h'], r['h'])
        else:
            lines.append(dict(r))
    return lines


def text_regions(rects):
    """Frame a continuous passage once, before adding stroke clearance.

    Wrapped lines share a frame; columns and passages separated by a paragraph
    gap remain separate. The saved occurrence still identifies the exact text.
    """
    groups = []
    for line in merge_lines(rects):
        group = next((g for g in reversed(groups)
                      if min(g[-1]['x'] + g[-1]['w'], line['x'] + line['w'])
                         > max(g[-1]['x'], line['x'])
                      and line['y'] > g[-1]['y'] + 2
                      and line['y'] - (g[-1]['y'] + g[-1]['h'])
                         <= max(3, min(g[-1]['h'], line['h']) * .8)), None)
        if group is None:
            groups.append([line])
        else:
            group.append(line)
    regions = []
    for group in groups:
        left = min(r['x'] for r in group); top = min(r['y'] for r in group)
        right = max(r['x'] + r['w'] for r in group)
        bottom = max(r['y'] + r['h'] for r in group)
        regions.append({'x': left, 'y': top, 'w': right-left, 'h': bottom-top})
    return regions


def locate(index_path, query, output_path, _loaded=None, _index_hash=None):
    index, image = _loaded if _loaded is not None else load_index(index_path)
    q = dict(query)
    insertion = q.get('insert')
    if insertion:
        if insertion not in ('before', 'after') or not q.get('anchor') or q.get('find'):
            raise ValueError('Insertions require before/after, a full block anchor, and empty find')
        q['find'] = q['anchor']
    matches = candidates(index, q)
    if q.get('occurrence_id'):
        matches = [m for m in matches if m['occurrence_id'] == q['occurrence_id']]
    if len(matches) != 1:
        raise ValueError(f'Expected one occurrence, found {len(matches)}; choose a block_id or occurrence_id')
    match = matches[0]
    if not match['rects']:
        raise ValueError('Text has no visible geometry')
    origin = index['origin']; scale = index['device_scale_factor']
    width, height = index['image_size']; marks = []
    if insertion:
        # Never interpret a match in the first line as the end of an entire paragraph.
        if normalized(q['anchor'])[0].strip() != normalized(match['context'])[0].strip():
            raise ValueError('Insertion anchor must be the complete indexed block text')
        r = match['block_rect']; x = max(0, math.floor((r['x']-origin['x'])*scale))
        y = round((r['y']+(r['h'] if insertion=='after' else 0)-origin['y'])*scale)
        y += 8 if insertion=='after' else -8
        mark = [x, y, min(width-x, math.ceil(r['w']*scale))]
        if y < 0 or y+6 > height:
            raise ValueError('Insertion falls outside captured context; recapture with more context')
        marks.append(mark)
    else:
        for r in text_regions(match['rects']):
            # Slight padding keeps the stroke off the characters, without clipping evidence.
            x = max(0, math.floor((r['x']-origin['x'])*scale)-10)
            y = max(0, math.floor((r['y']-origin['y'])*scale)-10)
            right = min(width, math.ceil((r['x']+r['w']-origin['x'])*scale)+10)
            bottom = min(height, math.ceil((r['y']+r['h']-origin['y'])*scale)+10)
            if (r['x'] < origin['x']-1 or r['y'] < origin['y']-1 or
                    (r['x']+r['w']-origin['x'])*scale > width+2 or
                    (r['y']+r['h']-origin['y'])*scale > height+2 or right-x <= 12 or bottom-y <= 12):
                raise ValueError('Match is outside captured context or too small; use a wider meaningful phrase')
            marks.append([x,y,right-x,bottom-y])
    job = {'id':q['id'], 'image_path':str(image), 'output_path':str(Path(output_path).resolve()),
        'source_sha256':index['files'][index['image']], 'index_path':str(Path(index_path).resolve()),
        'index_sha256':_index_hash or file_hash(index_path), 'snapshot_id':index['snapshot_id'],
        'occurrence_id':match['occurrence_id'], 'observed_text':match['text'],
        'color':q.get('color','red'), 'decision_context':q.get('decision_context',{}),
        'review_status':'pending_visual_review'}
    job['insertion_lines' if insertion else 'highlights'] = marks
    if 'region' in q:
        job['region'] = q['region']
    return job


def locate_many(index_path, queries, evidence_dir):
    ids=[q['id'] for q in queries]
    if not ids or len(ids)!=len(set(ids)) or any(not i or Path(i).name!=i or i in ('.','..') for i in ids):
        raise ValueError('Query IDs must be nonempty unique safe filenames')
    # Verify and parse a large page index once for the entire query batch.
    loaded=load_index(index_path);index_hash=file_hash(index_path)
    return {'schema_version':2,'jobs':[
        locate(index_path,q,Path(evidence_dir)/(q['id']+'.png'),loaded,index_hash) for q in queries]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', required=True)
    p.add_argument('--find')
    p.add_argument('--queries', help='JSON array of {id, find/anchor, block_id/occurrence_id, ...}')
    p.add_argument('--output', help='Annotation job plan JSON')
    p.add_argument('--evidence-dir', default='.tmp/evidence')
    args=p.parse_args()
    if args.find is not None:
        index,_=load_index(args.index)
        print(json.dumps(candidates(index,{'find':args.find}),ensure_ascii=False,indent=2))
    elif args.queries and args.output:
        queries=json.loads(Path(args.queries).read_text(encoding='utf-8'))
        plan=locate_many(args.index,queries,args.evidence_dir)
        write_json(args.output,plan)
        print(json.dumps({'plan':args.output,'jobs':len(plan['jobs'])}))
    else:
        p.error('Use --find, or --queries with --output')


if __name__=='__main__':
    main()
