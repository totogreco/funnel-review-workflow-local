#!/usr/bin/env python3
"""Keep screenshot context and highlight exact issue regions inside it."""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw
try:
    from .review_io import digest, file_hash, utc_now, write_json
except ImportError:
    from review_io import digest, file_hash, utc_now, write_json


COLORS = {
    "red": (230, 57, 70),
    "green": (56, 176, 0),
}


def annotate(image_path: str, output_path: str, color: str = "red",
             region: list = None, border_width: int = 6,
             highlights: list = None, context_padding: int = 300,
             insertion_lines: list = None) -> str:
    """Compatibility entry point; batch jobs reuse the same validated renderer."""
    with Image.open(image_path) as source:
        img = source.convert("RGB")
    try:
        return _annotate_image(img, image_path, output_path, color, region,
                               border_width, highlights, context_padding, insertion_lines)
    finally:
        img.close()


def _annotate_image(img, image_path: str, output_path: str, color: str = "red",
             region: list = None, border_width: int = 6,
             highlights: list = None, context_padding: int = 300,
             insertion_lines: list = None) -> str:
    """
    All rectangles are [x, y, width, height] in ORIGINAL image pixels.
    `region` selects context; `highlights` select the exact problem(s).
    `insertion_lines` are [x, y, width] markers for missing content, not boxes
    around unrelated existing text. Without a region, keep full width, padding,
    and at least 1.5 image widths of vertical context (source height permitting).
    Coordinates are validated, but the caller must visually verify text matches.
    """
    if Path(image_path).resolve() == Path(output_path).resolve():
        raise ValueError("Keep the original screenshot; use a different output path")
    if not highlights and not insertion_lines:
        raise ValueError("Supply a highlight or insertion line; a crop border does not locate an issue")
    if color not in COLORS or border_width < 1 or context_padding < 0:
        raise ValueError("Invalid color, border width, or context padding")
    width, height = img.size

    def rectangle(value, name):
        if (not isinstance(value, (list, tuple)) or len(value) != 4
                or any(type(n) is not int for n in value)):
            raise ValueError(f"{name} must contain four integer image-pixel coordinates")
        x, y, w, h = value
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError(f"{name} is outside the source image or has an invalid size")
        return x, y, x + w, y + h

    boxes = [rectangle(value, "Highlight") for value in (highlights or [])]
    for i, a in enumerate(boxes):
        for b in boxes[i+1:]:
            if max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3]):
                raise ValueError("Highlights overlap or touch; use one outer frame for a continuous passage, or separate the regions")
    lines = []
    for value in insertion_lines or []:
        if (not isinstance(value, (list, tuple)) or len(value) != 3
                or any(type(n) is not int for n in value)):
            raise ValueError("Insertion line must contain three integer image-pixel coordinates")
        x, y, w = value
        lines.append(rectangle([x, y, w, border_width], "Insertion line"))
    marks = boxes + lines
    minimum_height = min(height, (width * 3 + 1) // 2)
    if region is not None:
        crop = rectangle(region, "Context region")
        if crop[3] - crop[1] < minimum_height:
            raise ValueError("Context region is too tight; retain at least 1.5 source-image widths of height")
    else:
        first, last = min(b[1] for b in marks), max(b[3] for b in marks)
        crop_height = min(height, max(minimum_height, last - first + 2 * context_padding))
        top = max(0, min(height - crop_height, (first + last - crop_height) // 2))
        crop = (0, top, width, top + crop_height)
    left, top, right, bottom = crop
    for x1, y1, x2, y2 in marks:
        if x1 < left or y1 < top or x2 > right or y2 > bottom:
            raise ValueError("Context region cuts off a highlight or insertion line; enlarge the crop")
        if (x1, y1, x2, y2) == crop:
            raise ValueError("Highlight cannot be the whole crop; include surrounding context")
    for x1, y1, x2, y2 in boxes:
        if min(x2 - x1, y2 - y1) <= 2 * border_width:
            raise ValueError("Highlight is too small for the requested border width")
    img = img.crop(crop)

    draw = ImageDraw.Draw(img)
    for x1, y1, x2, y2 in boxes:
        draw.rounded_rectangle(
            [x1 - left, y1 - top, x2 - left - 1, y2 - top - 1],
            radius=8, outline=COLORS[color], width=border_width,
        )
    for x1, y1, x2, y2 in lines:
        draw.rectangle([x1 - left, y1 - top, x2 - left - 1, y2 - top - 1], fill=COLORS[color])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(output_path).with_suffix('.pending.png')
    try:
        img.save(temporary)
        temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)
        img.close()
    return output_path


def annotate_batch(plan, receipt_path, resume=False):
    """Decode one source at a time; reuse only hash-verified unchanged outputs."""
    jobs = plan.get('jobs', [])
    if plan.get('schema_version') != 2 or not jobs:
        raise ValueError('A version 2 plan with jobs is required')
    outputs = [Path(j['output_path']).resolve() for j in jobs]
    sources = {Path(j['image_path']).resolve() for j in jobs}
    ids = [j['id'] for j in jobs]
    if len(set(outputs)) != len(outputs) or len(set(ids)) != len(ids):
        raise ValueError('Duplicate output paths or job IDs')
    if any(p in sources or p.suffix.lower() != '.png' for p in outputs):
        raise ValueError('Outputs must be distinct PNG files, never source evidence')
    receipt_path = Path(receipt_path)
    protected = sources | set(outputs) | {Path(j['index_path']).resolve() for j in jobs if j.get('index_path')}
    if receipt_path.resolve() in protected:
        raise ValueError('Receipt must not overwrite evidence, an index or an output')
    old = json.loads(receipt_path.read_text()) if resume and receipt_path.exists() else {}
    previous = {j['id']:j for j in old.get('jobs', [])}
    receipt = {'schema_version':2, 'started_at':utc_now(), 'status':'running', 'jobs':[]}
    start = time.monotonic()
    groups = defaultdict(list)
    for job in jobs:
        groups[str(Path(job['image_path']).resolve())].append(job)
    code_hash = file_hash(__file__)
    try:
        for source_path, group in groups.items():
            actual = file_hash(source_path)
            pending = []
            for job in group:
                if job.get('source_sha256') != actual:
                    raise ValueError(f"Source evidence changed for {job['id']}; locate it again")
                if job.get('index_path') and file_hash(job['index_path']) != job.get('index_sha256'):
                    raise ValueError(f"Capture index changed for {job['id']}; locate it again")
                key = digest({'job':job, 'renderer':code_hash, 'source':actual})
                prior = previous.get(job['id'], {})
                output = Path(job['output_path'])
                if (resume and prior.get('key') == key and output.is_file()
                        and file_hash(output) == prior.get('output_sha256')):
                    receipt['jobs'].append(dict(prior, reused=True))
                else:
                    pending.append((job,key))
            if not pending:
                continue
            with Image.open(source_path) as source:
                img = source.convert('RGB')
            try:
                for job,key in pending:
                    began = time.monotonic()
                    options = {k:job[k] for k in ('color','region','border_width','highlights',
                              'context_padding','insertion_lines') if k in job}
                    _annotate_image(img, source_path, job['output_path'], **options)
                    receipt['jobs'].append({'id':job['id'], 'key':key, 'output':job['output_path'],
                        'output_sha256':file_hash(job['output_path']), 'reused':False,
                        'duration_seconds':time.monotonic()-began, 'completed_at':utc_now(),
                        'review_status':'pending_visual_review'})
                    write_json(receipt_path, receipt)
            finally:
                img.close()
        receipt['status'] = 'complete'
    except Exception as error:
        receipt.update(status='failed', error=str(error))
        raise
    finally:
        receipt.update(completed_at=utc_now(), duration_seconds=time.monotonic()-start)
        write_json(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description="Keep screenshot context and mark an issue or insertion location")
    parser.add_argument("--image", help="Path to the source screenshot")
    parser.add_argument("--output", help="Path for the annotated output image")
    parser.add_argument("--plan", help="Version 2 annotation jobs JSON")
    parser.add_argument("--receipt", help="Batch checkpoint JSON")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--color", default="red", choices=list(COLORS.keys()),
                        help="Border color (default: red)")
    parser.add_argument("--region", default=None,
                        help="Context crop in ORIGINAL image pixels: [x, y, w, h]")
    parser.add_argument("--highlight", action="append",
                        help="Exact issue box in ORIGINAL image pixels: [x, y, w, h]; repeat for multiple boxes")
    parser.add_argument("--insertion-line", action="append",
                        help="Missing-content insertion marker in ORIGINAL pixels: [x, y, width]")
    parser.add_argument("--context-padding", type=int, default=300,
                        help="Extra context above/below marks; minimum context height still applies (default: 300)")
    parser.add_argument("--border-width", type=int, default=6,
                        help="Border width in pixels (default: 6)")
    args = parser.parse_args()

    if args.plan:
        if not args.receipt or args.image or args.output:
            parser.error("Batch mode needs --receipt; do not combine with --image/--output")
        result = annotate_batch(json.loads(Path(args.plan).read_text(encoding='utf-8')),
                                args.receipt, args.resume)
        print(json.dumps({'status':result['status'], 'jobs':len(result['jobs']),
                          'reused':sum(j['reused'] for j in result['jobs'])}))
        return
    if not args.image or not args.output:
        parser.error("Supply --image and --output, or --plan and --receipt")

    region = json.loads(args.region) if args.region else None
    result = annotate(args.image, args.output, args.color, region, args.border_width,
                      [json.loads(box) for box in (args.highlight or [])], args.context_padding,
                      [json.loads(line) for line in (args.insertion_line or [])])
    print(json.dumps({"output": result}))


if __name__ == "__main__":
    main()
