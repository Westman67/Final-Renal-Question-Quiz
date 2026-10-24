"""Shared helpers for answer-blocking masks on learner images.

Originals are never modified. A learner variant is derived from the immutable original asset by painting opaque
light-gray blocks (with a question mark) over declared rectangles. Every changed pixel lies inside a declared box,
so verify_images.py style checks (pixels unchanged outside declared masks) hold for variants built here.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FILL = (222, 226, 232)
EDGE = (150, 158, 170)
INK = (84, 92, 106)
FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/Library/Fonts/Arial Bold.ttf',
]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _font(size):
    for f in FONTS:
        if Path(f).is_file():
            return ImageFont.truetype(f, size)
    return None


def block(im, box, label='?'):
    """Paint one opaque block inside box=[x0,y0,x1,y1) (exclusive end, matching verify_images.py)."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(im)
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=FILL)
    d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=EDGE, width=1)
    if label:
        size = max(10, min((y1 - y0) * 0.5, (x1 - x0) * 0.5))
        font = _font(int(size))
        if font:
            l, t, r, b = d.textbbox((0, 0), label, font=font)
            d.text((x0 + (x1 - x0 - (r - l)) / 2 - l, y0 + (y1 - y0 - (b - t)) / 2 - t), label, fill=INK, font=font)
        else:
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            d.text((cx - 3, cy - 5), label, fill=INK)


def build_masked(original_path, boxes, reason, target, labels=None):
    """Return (png_bytes_source_sha, image, transform_record, 24-hex digest)."""
    raw = Path(original_path).read_bytes()
    im = Image.open(original_path).convert('RGB')
    w, h = im.size
    records = []
    for i, b in enumerate(boxes):
        assert 0 <= b[0] < b[2] <= w and 0 <= b[1] < b[3] <= h, b
        block(im, b, (labels or {}).get(i, '?') if isinstance(labels, dict) else '?')
        records.append({'box': list(b), 'fill': 'opaque light-gray block with a question mark', 'rgb': list(FILL)})
    tr = {'type': 'mask', 'input_dimensions': [w, h], 'coordinate_basis': 'immutable_original_pixels', 'crop_box': None,
          'normalized_crop': None, 'masks': records, 'output_dimensions': [w, h], 'target': target, 'reason': reason}
    digest = sha_bytes((sha_bytes(raw) + json.dumps(tr, sort_keys=True)).encode())[:24]
    return im, tr, digest


def save_variant(im, digest, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    im.save(out_dir / f'{digest}.png', optimize=True)
    im.save(out_dir / f'{digest}.webp', 'WEBP', quality=92, method=6)


def render(original_path, specs):
    """Paint blocks from specs=[{'box':[x0,y0,x1,y1],'label':'?','keep_color':bool}] and return (image, records, size, source_sha).

    keep_color=True samples the cell's own background and keeps it, so color-coded tables still hint at the answer
    while the printed text is hidden. Otherwise the block is the standard light gray.
    """
    raw = Path(original_path).read_bytes()
    im = Image.open(original_path)
    im = im.convert('RGBA' if ('A' in im.getbands() or 'transparency' in im.info) else 'RGB')
    w, h = im.size
    records = []
    for sp in specs:
        x0, y0, x1, y1 = sp['box']
        assert 0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h, sp
        fill, ink, edge = FILL, INK, EDGE
        if sp.get('keep_color'):
            fill = im.getpixel((x0 + 6, y0 + 6))[:3]
            ink = (255, 255, 255) if sum(fill) / 3 < 150 else (40, 40, 40)
            edge = fill
        d = ImageDraw.Draw(im)
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill, outline=edge, width=1)
        label = sp.get('label', '?')
        if label:
            font = _font(int(max(10, min((y1 - y0) * 0.5, (x1 - x0) * 0.5))))
            if font:
                l, t, r, b = d.textbbox((0, 0), label, font=font)
                d.text((x0 + (x1 - x0 - (r - l)) / 2 - l, y0 + (y1 - y0 - (b - t)) / 2 - t), label, fill=ink, font=font)
        records.append({'box': [x0, y0, x1, y1], 'rgb': list(fill),
                        'fill': 'cell background color kept, printed text hidden behind a question mark' if sp.get('keep_color') else 'opaque light-gray block with a question mark'})
    return im, records, (w, h), sha_bytes(raw)


def pathology_transform(records, size, target, reason):
    return {'type': 'mask', 'input_dimensions': list(size), 'coordinate_basis': 'immutable_original_pixels', 'crop_box': None,
            'normalized_crop': None, 'masks': records, 'output_dimensions': list(size), 'target': target, 'reason': reason}


def physiology_transform(records, size, target, reason):
    w, h = size
    return {'crop': None, 'masks': [r['box'] for r in records], 'input_dimensions': list(size),
            'coordinate_basis': 'immutable_original_pixels', 'method': reason, 'fills': [r['fill'] for r in records],
            'target': target, 'normalized_crop': None,
            'normalized_masks': [[r['box'][0] / w, r['box'][1] / h, r['box'][2] / w, r['box'][3] / h] for r in records]}


def digest_for(source_sha, transform):
    return sha_bytes((source_sha + json.dumps(transform, sort_keys=True)).encode())[:24]
