"""Verify immutable manual captures and every reproducible quiz-safe variant."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True, help='Manual root containing lecture folders')
parser.add_argument(
    '--bank-root',
    type=Path,
    default=Path('data'),
    help='Repository-relative bank directory, such as data or data/pathology',
)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
bank_root = root / args.bank_root
m = json.loads((bank_root / 'source-manifest.json').read_text())
q = json.loads((bank_root / 'question-bank.json').read_text())
verified_variants = set()

for s in m['sources']:
    p = args.source / s['relative_path']
    assert p.is_file(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == s['sha256'], p
    assert hashlib.sha256((root / s['original_asset']).read_bytes()).hexdigest() == s['sha256']
    if s['status'] != 'USABLE':
        continue
    original = Image.open(p).convert('RGB')
    variants = s.get('variants') or [{
        'variant_id': s['variant_id'], 'image': s['image'],
        'zoom_image': s['zoom_image'], 'transform': s['transform'],
    }]
    for v in variants:
        crop = v['transform'].get('crop') or v['transform'].get('crop_box')
        if crop is not None:
            assert len(crop) == 4
            x0, y0, x1, y1 = crop
            assert all(isinstance(n, int) for n in crop)
            assert 0 <= x0 < x1 <= s['width'] and 0 <= y0 < y1 <= s['height']
            expected = original.crop(tuple(crop))
        else:
            expected = original
        final = Image.open(root / v['zoom_image']).convert('RGB')
        assert expected.size == final.size, (
            'Variant dimensions differ from the declared crop',
            s['relative_path'],
            v['variant_id'],
            expected.size,
            final.size,
            v['transform'],
        )
        delta = ImageChops.difference(expected, final)
        d = ImageDraw.Draw(delta)
        offset_x, offset_y = (crop[0], crop[1]) if crop is not None else (0, 0)
        for mask in v['transform'].get('masks', []):
            x0, y0, x1, y1 = mask['box'] if isinstance(mask, dict) else mask
            feather_radius = mask.get('feather_radius', 0) if isinstance(mask, dict) else 0
            if v['transform'].get('coordinate_basis') == 'immutable_original_pixels' and crop is not None:
                assert 0 <= x0 < x1 <= original.width and 0 <= y0 < y1 <= original.height
                x0, x1 = x0 - offset_x, x1 - offset_x
                y0, y1 = y0 - offset_y, y1 - offset_y
            else:
                assert 0 <= x0 < x1 <= expected.width and 0 <= y0 < y1 <= expected.height
            d.rectangle(
                (
                    x0 - feather_radius,
                    y0 - feather_radius,
                    x1 - 1 + feather_radius,
                    y1 - 1 + feather_radius,
                ),
                fill=(0, 0, 0),
            )
        for polygon in v['transform'].get('polygons', []):
            assert len(polygon) >= 3
            if v['transform'].get('coordinate_basis') == 'immutable_original_pixels' and crop is not None:
                polygon = [[x - offset_x, y - offset_y] for x, y in polygon]
            d.polygon([tuple(point) for point in polygon], fill=(0, 0, 0))
        assert delta.getbbox() is None, ('Pixels changed outside declared mask', s['relative_path'], v['variant_id'])
        for key, fmt in [('image', 'WEBP'), ('zoom_image', 'PNG')]:
            assert re.fullmatch(r'assets/[a-f0-9]{24}\.(png|webp)', v[key])
            with Image.open(root / v[key]) as im:
                assert im.format == fmt and im.size == expected.size
                im.verify()
        assert v['variant_id'] not in verified_variants
        verified_variants.add(v['variant_id'])
        assert s['variant_review_complete'], (s['relative_path'], v['variant_id'])

for question in q['questions']:
    if question.get('visual_kind') == 'table':
        assert question['context_table']['placement'] == 'primary'
        assert not any(question.get(key) for key in ('image', 'zoom_image', 'original_image'))
        continue
    assert question['variant_id'] in verified_variants, question['question_id']
    for key in ('image', 'zoom_image', 'original_image'):
        assert (root / question[key]).is_file(), (question['question_id'], key)

if args.bank_root == Path('data'):
    assert len(m['sources']) == m['source_count_physical'] == 103
    assert len(q['questions']) == 109
    for lecture, sources, questions in [('R3', 0, 2), ('R5', 6, 11), ('R6', 15, 15), ('R7', 14, 11), ('R8', 3, 13), ('R9', 4, 5), ('R12', 29, 8), ('R13', 12, 3)]:
        assert sum(s['lecture_id'] == lecture for s in m['sources']) == sources
        assert sum(question['collection'] == lecture for question in q['questions']) == questions
elif args.bank_root == Path('data/pathology'):
    assert len(m['sources']) == m['source_count_physical'] == 852
    assert len(q['questions']) == 211
print(f"PASS: {args.bank_root} has {len(m['sources'])} immutable captures, {len(verified_variants)} verified variants, and {len(q['questions'])} scored questions")
