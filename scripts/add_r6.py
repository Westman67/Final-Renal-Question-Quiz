"""Append reviewed R6 manual captures without changing prior bank IDs or originals.

Question activation is intentionally separate from visual QA. New sources and
variants start unreviewed; review_r6.py contains the explicit activation gate.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

APP = Path(__file__).resolve().parents[1]
MANUAL = (APP / '..' / 'Renal' / 'Manual').resolve()
VAULT_MANIFEST = Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production/R6 - Proximal Tubule (Physiology)/lecture-manifest.json')
LECTURES = Path('/Users/chriselwell/Desktop/Renal/Lectures')
manifest_path = APP / 'data/source-manifest.json'
bank_path = APP / 'data/question-bank.json'
coverage_path = APP / 'data/coverage.json'
manifest = json.loads(manifest_path.read_text())
bank = json.loads(bank_path.read_text())
coverage = json.loads(coverage_path.read_text())
assert len(manifest['sources']) == 23 and len(bank['questions']) == 47
assert all(s['lecture_id'] != 'R6' for s in manifest['sources'])
assert all(q['collection'] != 'R6' for q in bank['questions'])
vm = json.loads(VAULT_MANIFEST.read_text())
rls_record = next(s for s in vm['sources'] if s['kind'] == 'rls')
notes_record = next(s for s in vm['sources'] if s['kind'] == 'professor-notes')
rls_path = LECTURES / Path(rls_record['path']).name


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


assert rls_path.is_file() and sha(rls_path) == rls_record['sha256']
capture_hashes = {Path(x['path']).name: x['sha256'] for x in vm['picture_quiz_extraction']['capture_inventory']}
files = [
    ('Proximal Tubule Brush Border EM.png', 'TEM', 'Apical brush border', 5, 'USABLE', 'Lumen-facing microvilli form an identifiable brush border; exterior caption can be masked.'),
    ('Proximal Tubule Histo.png', 'Histology', 'Proximal tubule H&E', 4, 'REFERENCE_ONLY', 'Low-resolution H&E crop and labels over tissue do not support a strong single-best-answer scored identification.'),
    ('Proximal Tubule Mitochondria EM.png', 'TEM', 'Mitochondria and apical brush border', 5, 'USABLE', 'Yellow and red arrows indicate distinct structures; exterior teaching caption can be masked.'),
    ('Proximal Tubule PT Cells and Cap Lumen 1.png', 'SEM', 'Tubule-to-capillary orientation', 4, 'USABLE', 'Distinct view shows tubule lumen, PT epithelial cells, and adjacent capillary lumen.'),
    ('Proximal Tubule PT Cells and Cap Lumen 2.png', 'SEM', 'Apical versus basolateral PT orientation', 4, 'USABLE', 'Alternate oblique view shows microvillar apical face and lower capillary-adjacent side.'),
    ('Screenshot 2026-10-03 at 12.51.49 PM.png', 'Histology', 'Proximal tubule H&E annotated alternate', 4, 'REFERENCE_ONLY', 'Same H&E field as other capture with PT label printed directly on tissue; removing it would cover diagnostic pixels.'),
]
assert {x[0] for x in files} == set(capture_hashes)
groups = {
    'histology': 'group-' + hashlib.sha256(('histo:' + ''.join(sorted(capture_hashes[x] for x in (files[1][0], files[5][0])))).encode()).hexdigest()[:16],
    'sem': 'group-' + hashlib.sha256(('sem:' + ''.join(sorted(capture_hashes[x] for x in (files[3][0], files[4][0])))).encode()).hexdigest()[:16],
}


def dhash(im: Image.Image) -> str:
    x = im.convert('L').resize((9, 8))
    bits = ''.join('1' if x.getpixel((j, i)) > x.getpixel((j + 1, i)) else '0' for i in range(8) for j in range(8))
    return f'{int(bits, 2):016x}'


source_by_name = {}
new_questions = []
for name, modality, concept, page, status, reason in files:
    p = MANUAL / 'R6' / name
    assert p.is_file() and sha(p) == capture_hashes[name]
    digest = sha(p)
    with Image.open(p) as im:
        im.load()
        width, height = im.size
        mode, fmt, phash = im.mode, im.format, dhash(im)
    asset = f'assets/{digest[:24]}.png'
    if not (APP / asset).exists():
        shutil.copyfile(p, APP / asset)
    assert sha(APP / asset) == digest
    group = groups['histology'] if name in (files[1][0], files[5][0]) else groups['sem'] if name in (files[3][0], files[4][0]) else 'group-' + digest[:16]
    source = {
        'relative_path': 'R6/' + name, 'extension': '.png', 'bytes': p.stat().st_size,
        'sha256': digest, 'kind': 'raster', 'width': width, 'height': height,
        'format': fmt, 'mode': mode, 'decode_status': 'ok',
        'asset_id': 'asset-' + digest[:16], 'source_id': 'src-' + digest[:16],
        'source_group_id': group, 'perceptual_hash': phash,
        'perceptual_hash_method': '64-bit dHash', 'source_origin': 'lecture',
        'acquisition': 'user manual RLS capture', 'lecture_id': 'R6',
        'system': 'Renal', 'status': status, 'modality': modality,
        'tested_concept': concept, 'review_reason': reason,
        'ground_truth_basis': 'Visible RLS capture matched to verified R6 RLS page and transcript/Notes teaching',
        'source_citation': {'document': rls_path.name, 'page': page, 'sha256': rls_record['sha256']},
        'rights_status': 'User-supplied course material, local educational use only; no redistribution authorization established',
        'original_asset': asset, 'variants': [], 'variant_review_complete': False,
        'question_type_matrix': [{'type': 'Distinct visual targets', 'supported': 'YES' if status == 'USABLE' else 'NO', 'reason': reason}],
    }
    manifest['sources'].append(source)
    source_by_name[name] = source


def variant(source: dict, target: str, masks: list[list[int]] | None = None, fill='black') -> dict:
    masks = masks or []
    recipe = {
        'masks': masks, 'input_dimensions': [source['width'], source['height']],
        'coordinate_basis': 'immutable_original_pixels',
        'method': 'Opaque exterior-text mask only; no anatomy reconstruction' if masks else 'No pixel changes',
        'fill': fill, 'target': target,
        'normalized_masks': [[v / (source['width'] if i % 2 == 0 else source['height']) for i, v in enumerate(b)] for b in masks],
    }
    key = hashlib.sha256((source['sha256'] + json.dumps(recipe, sort_keys=True)).encode()).hexdigest()[:24]
    zoom, display = f'assets/{key}.png', f'assets/{key}.webp'
    with Image.open(MANUAL / source['relative_path']) as original:
        im = original.convert('RGB')
        draw = ImageDraw.Draw(im)
        for x0, y0, x1, y1 in masks:
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill)
        im.save(APP / zoom)
        im.save(APP / display, format='WEBP', quality=90, method=6)
    v = {'variant_id': 'var-' + key, 'image': display, 'zoom_image': zoom,
         'transform': recipe, 'visual_review': 'PENDING full-size review'}
    source['variants'].append(v)
    if len(source['variants']) == 1:
        source.update(variant_id=v['variant_id'], image=display, zoom_image=zoom, transform=recipe)
    return v


def question(source: dict, v: dict, tested_concept: str, stem: str,
             options: list[str], key: int, rationales: list[str], clues: list[str],
             qtype: str, extra_pages: tuple[int, ...] = ()):
    assert len(options) == len(rationales) == 4 and len(set(options)) == 4
    ident = hashlib.sha256((source['source_id'] + tested_concept + v['variant_id']).encode()).hexdigest()[:20]
    citation = source['source_citation']
    citations = [citation, {'document': Path(notes_record['path']).name, 'page': 4, 'sha256': notes_record['sha256']}] + [{**citation, 'page': n} for n in extra_pages]
    q = {
        'question_id': 'q-' + ident, 'asset_id': source['asset_id'],
        'source_group_id': source['source_group_id'], 'source_id': source['source_id'],
        'variant_id': v['variant_id'], 'question_type': qtype, 'tested_concept': tested_concept,
        'stem': stem, 'visual_target': stem, 'joint_composite': False,
        'options': options, 'correct_index': key, 'choice_rationales': rationales,
        'explanation': rationales[key], 'visual_clues': clues,
        'ground_truth_confidence': 'high', 'ground_truth_basis': source['ground_truth_basis'],
        'citations': citations, 'image': v['image'], 'zoom_image': v['zoom_image'],
        'original_image': source['original_asset'], 'original_filename': source['relative_path'],
        'category': source['modality'], 'collection': 'R6', 'source_origin': 'lecture',
        'status': 'USABLE', 'case_context': '', 'accepted_synonyms': [],
    }
    new_questions.append(q)


s = source_by_name[files[0][0]]
v = variant(s, 'Red-arrow apical microvilli', [[0, 1258, 1338, 1426]])
question(s, v, 'R6 red-arrow proximal brush border',
         'What apical specialization do the two red arrows indicate along the labeled proximal-tubule lumen?',
         ['Brush-border microvilli', 'Basolateral membrane infoldings', 'Podocyte foot processes', 'Fenestrated capillary endothelium'], 0,
         ['Both arrows end at the dense fringe of short projections extending into the tubular lumen: the brush border.',
          'Basolateral infoldings would face interstitium and capillary, not project into this central lumen.',
          'Podocyte foot processes surround glomerular capillaries; the arrows instead point to a continuous tubular luminal fringe.',
          'Endothelial fenestrae would be in a capillary lining, not the prominent projections of this tubular epithelium.'],
         ['Red-arrow tips at the luminal fringe', 'Numerous closely spaced projections around the lumen'], 'Structure')

s = source_by_name[files[2][0]]
v = variant(s, 'Yellow-arrow mitochondria and red-arrow microvilli', [[0, 1251, 1372, 1360]])
question(s, v, 'R6 yellow-arrow mitochondria in proximal cells',
         'In this complete proximal-tubule EM cross-section, what structures do the yellow arrows identify within the epithelial cells?',
         ['Mitochondria', 'Brush-border microvilli', 'Cell nuclei', 'Peritubular capillary lumina'], 0,
         ['The yellow arrows target dark, elongated internal profiles throughout the epithelial cytoplasm, consistent with the mitochondria highlighted on RLS p. 5.',
          'Microvilli form the fine apical fringe at the red arrows next to the central lumen, not these internal profiles.',
          'Nuclei are larger rounded profiles lower in the cells, not the multiple narrow yellow-arrow targets.',
          'Capillary lumina lie outside the tubular epithelium; the yellow arrows are within its cytoplasm.'],
         ['Multiple dark elongated cytoplasmic profiles', 'Separate red-arrow apical fringe at the lumen'], 'Cell/Tissue')
question(s, v, 'R6 red-arrow brush border in mitochondria EM',
         'In this complete proximal-tubule EM cross-section, what do the red arrows identify on the side facing the central tubular lumen?',
         ['Apical brush-border microvilli', 'Mitochondria in cytoplasm', 'Basolateral cell membrane', 'Capillary endothelial fenestrae'], 0,
         ['The red arrows touch the fine fringe of projections directly bordering the central lumen, the apical brush border.',
          'Mitochondria are the dark elongated structures within the cells at the yellow arrows, away from the luminal edge.',
          'The basolateral membrane lies on the outer side of the epithelial cells, opposite the red-arrow luminal surface.',
          'Capillary endothelium would surround an external blood space, not line this central tubular lumen.'],
         ['Red arrowheads meet the lumen-facing fringe', 'Yellow arrows separately identify internal profiles'], 'Structure')

s = source_by_name[files[3][0]]
v = variant(s, 'Tubule-to-capillary orientation')
question(s, v, 'R6 reabsorption direction in PT capillary SEM',
         'Using the labeled compartments in this complete oblique EM view, which spatial route represents reabsorption?',
         ['Upper tubule lumen → intervening PT cells → lower capillary lumen',
          'Lower capillary lumen → intervening PT cells → upper tubule lumen',
          'Upper tubule lumen → outer tissue without crossing the PT epithelium',
          'Lower capillary lumen → glomerular tuft → upper tubule lumen'], 0,
         ['The upper Tubule Lumen is separated from the lower Cap Lumen by the visible PT epithelial cells; reabsorption moves downward through or between them toward blood.',
          'This reverses the upper-to-lower lumen-to-blood direction shown in the image and describes secretion instead.',
          'The PT cells visibly intervene between the two labeled spaces; the route cannot bypass the epithelial layer.',
          'No glomerular tuft appears in this image; the labeled lower space is a nearby capillary lumen.'],
         ['Tubule Lumen label above the PT cells', 'Cap Lumen label below their basal side'], 'View/Orientation')

s = source_by_name[files[4][0]]
v = variant(s, 'Apical face of PT cells')
question(s, v, 'R6 apical PT cell surface in oblique SEM',
         'Which visible surface of the labeled PT cells is the apical face in this complete oblique EM view?',
         ['The dense projecting fringe beside the upper Tubule Lumen',
          'The smooth lower edge next to Cap Lumen',
          'The internal cytoplasm beneath the cell surface',
          'The outer capillary wall below the cells'], 0,
         ['The upper fringe projects from PT cells into the labeled Tubule Lumen, identifying their apical microvillar face.',
          'The lower edge faces the labeled capillary side and is basolateral, not apical.',
          'Cytoplasm is inside the PT cells rather than a surface contacting tubular fluid.',
          'The capillary wall belongs to the adjacent vessel, not the apical surface of the PT epithelium.'],
         ['Upper Tubule Lumen label', 'Closely packed projections on the cell side facing that lumen'], 'View/Orientation')

assert len(new_questions) == 5
assert len({q['question_id'] for q in new_questions}) == 5
manifest['source_count_physical'] = len(manifest['sources'])
manifest['approval'] = 'User approved the complete R6 import prompt on 2026-10-04; previous multi-target approval retained.'
manifest['stage'] = 'R6 candidate derivatives generated; full-size QA pending'
manifest['generated_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
bank['bank_version'] = '2026-10-04-renal-r6-1'
bank['questions'].extend(new_questions)
coverage['lectures']['R6'] = {
    'status': 'Partial coverage',
    'tested_summary': ['Brush-border microvilli in two EM views', 'Mitochondria in proximal epithelial cells', 'Tubule-to-capillary direction of reabsorption', 'Apical surface orientation in an oblique EM view'],
    'gaps': ['The two H&E captures are low-resolution or directly labeled over tissue and remain teaching references rather than scored items.', 'The six supplied captures do not cover the R6 index-of-concentration graph, Starling-force diagram, transporter schematics, or glucose threshold/Tm graph.'],
    'next_capture': 'A complete manual R6 capture of a clearly readable index-of-concentration or glucose threshold/Tm graph would broaden visual coverage.',
    'basis': 'Six manual R6 captures matched to RLS pp. 4–5; four scored EM capture files in three source groups, two H&E reference captures. This is not lecture-wide visual coverage.',
}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
bank_path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')
(APP / 'data/review-queue.json').write_text(json.dumps({'schema_version': 2, 'items': [x for x in manifest['sources'] if x['status'] != 'USABLE']}, ensure_ascii=False, indent=2) + '\n')
print('R6: six captures inventoried, four candidate scored images, two reference captures, five questions pending visual QA')
