"""Rebuild the reviewed renal manual-capture bank without changing source images.

The existing R1 question IDs are retained so browser progress remains compatible.
Every new mask is an opaque rectangle over a source arrow or pre-existing label
area. Recipes use immutable-original pixel coordinates.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

APP = Path(__file__).resolve().parents[1]
MANUAL = (APP / '..' / 'Renal' / 'Manual').resolve()
LECTURES = Path('/Users/chriselwell/Desktop/Renal/Lectures')
PRODUCTION = Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production')
OLD_MANIFEST = json.loads((APP / 'data/source-manifest.json').read_text())
OLD_BANK = json.loads((APP / 'data/question-bank.json').read_text())
sources = [dict(s) for s in OLD_MANIFEST['sources'] if s['lecture_id'] == 'R1']
questions = [dict(q) for q in OLD_BANK['questions'] if q['collection'] == 'R1' and q['question_id'] in {
    'q-3bde81ca5b28287df5ec', 'q-335788742cee7918e165', 'q-14f9426f02d85984d507',
    *[q['question_id'] for q in OLD_BANK['questions'][3:12]],
}]
assert len(sources) == 16 and len(questions) == 12, 'Expected the reviewed R1 pilot as input'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


for s in sources:
    s['relative_path'] = 'R1/' + Path(s['relative_path']).name
    p = MANUAL / s['relative_path']
    assert p.is_file() and sha(p) == s['sha256']
    assert sha(APP / s['original_asset']) == s['sha256']

source_by_capture = {s['capture_number']: s for s in sources}
rls_citations = {}
for lecture, dirname in [
    ('R2', 'R2 - Fluid Regulation & Fluid Compartments (Physiology)'),
    ('R4', 'R4 - Renal Plasma Flow (Physiology)'),
    ('R5', 'R5 - Autoregulation & Renal Hemodynamics (Physiology)'),
]:
    m = json.loads((PRODUCTION / dirname / 'lecture-manifest.json').read_text())
    rls = next(s for s in m['sources'] if s['kind'] == 'rls')
    p = LECTURES / Path(rls['path']).name
    assert p.is_file() and sha(p) == rls['sha256'], p
    rls_citations[lecture] = {'document': p.name, 'sha256': rls['sha256']}


def dhash(im: Image.Image) -> str:
    x = im.convert('L').resize((9, 8))
    bits = ''.join('1' if x.getpixel((j, i)) > x.getpixel((j + 1, i)) else '0'
                   for i in range(8) for j in range(8))
    return f'{int(bits, 2):016x}'


def add_source(lecture: str, filename: str, modality: str, topic: str, page: int, note: str):
    p = MANUAL / lecture / filename
    assert p.is_file(), p
    digest = sha(p)
    with Image.open(p) as im:
        im.load()
        width, height = im.size
        mode, fmt, phash = im.mode, im.format, dhash(im)
    key = digest[:24]
    original = f'assets/{key}.png'
    if not (APP / original).exists():
        shutil.copyfile(p, APP / original)
    assert sha(APP / original) == digest
    citation = {**rls_citations[lecture], 'page': page}
    s = {
        'relative_path': f'{lecture}/{filename}', 'extension': p.suffix.lower(),
        'bytes': p.stat().st_size, 'sha256': digest, 'kind': 'raster',
        'width': width, 'height': height, 'format': fmt, 'mode': mode,
        'decode_status': 'ok', 'asset_id': 'asset-' + digest[:16],
        'source_id': 'src-' + digest[:16], 'source_group_id': 'group-' + digest[:16],
        'perceptual_hash': phash, 'perceptual_hash_method': '64-bit dHash',
        'source_origin': 'lecture', 'acquisition': 'user manual RLS capture',
        'lecture_id': lecture, 'system': 'Renal', 'status': 'USABLE',
        'modality': modality, 'tested_concept': topic, 'review_reason': note,
        'ground_truth_basis': 'Visible RLS labels/diagram and matching authoritative RLS page',
        'source_citation': citation,
        'rights_status': 'User-supplied course material, local educational use only; no redistribution authorization established',
        'original_asset': original, 'variants': [], 'variant_review_complete': False,
        'question_type_matrix': [{'type': 'Distinct visual targets', 'supported': 'YES', 'reason': note}],
    }
    sources.append(s)
    return s


def add_variant(s: dict, target: str, box=None, fill='white'):
    p = MANUAL / s['relative_path']
    recipe = {
        'masks': [box] if box else [], 'input_dimensions': [s['width'], s['height']],
        'coordinate_basis': 'immutable_original_pixels', 'method': 'Opaque target-only mask; no anatomy reconstruction',
        'fill': fill, 'target': target,
    }
    recipe['normalized_masks'] = [[v / (s['width'] if i % 2 == 0 else s['height'])
                                   for i, v in enumerate(b)] for b in recipe['masks']]
    key = hashlib.sha256((s['sha256'] + json.dumps(recipe, sort_keys=True)).encode()).hexdigest()[:24]
    zoom, display = f'assets/{key}.png', f'assets/{key}.webp'
    with Image.open(p) as original:
        im = original.convert('RGB')
        if box:
            d = ImageDraw.Draw(im)
            d.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=fill)
        im.save(APP / zoom)
        im.save(APP / display, format='WEBP', quality=90, method=6)
    v = {'variant_id': 'var-' + key, 'image': display, 'zoom_image': zoom,
         'transform': recipe, 'visual_review': 'PENDING full-size review'}
    s['variants'].append(v)
    if len(s['variants']) == 1:
        s.update(variant_id=v['variant_id'], image=display, zoom_image=zoom,
                 transform=recipe)
    return v


def add_question(s: dict, v: dict, concept: str, stem: str, options: list[str], key: int,
                 rationales: list[str], clues: list[str], kind='Structure', extra_pages=()):
    assert len(options) == len(rationales) == 4 and len(set(options)) == 4
    ident = hashlib.sha256((s['source_id'] + concept + v['variant_id']).encode()).hexdigest()[:20]
    citation = s['source_citation']
    citations = [citation] + [{**citation, 'page': n} for n in extra_pages]
    if s['lecture_id'] == 'R1':
        citations.append({'document': 'R1 Review - Renal Histology Tran.pdf',
                          'page': 4 if s.get('capture_number') == 7 else 1})
    q = {
        'question_id': 'q-' + ident, 'asset_id': s['asset_id'],
        'source_group_id': s['source_group_id'], 'source_id': s['source_id'],
        'variant_id': v['variant_id'], 'question_type': kind, 'tested_concept': concept,
        'stem': stem, 'visual_target': stem, 'joint_composite': False,
        'options': options, 'correct_index': key, 'choice_rationales': rationales,
        'explanation': rationales[key], 'visual_clues': clues,
        'ground_truth_confidence': 'high', 'ground_truth_basis': s['ground_truth_basis'],
        'citations': citations, 'image': v['image'], 'zoom_image': v['zoom_image'],
        'original_image': s['original_asset'], 'original_filename': s['relative_path'],
        'category': s['modality'], 'collection': s['lecture_id'], 'source_origin': 'lecture',
        'status': 'USABLE', 'case_context': '', 'accepted_synonyms': [],
    }
    questions.append(q)
    return q


# Expand two already-reviewed R1 variants. No new R1 original is altered.
s = source_by_capture[2]
v = {'variant_id': s['variant_id'], 'image': s['image'], 'zoom_image': s['zoom_image']}
diagram = [
    ('C', 'Afferent arteriole', 'the vessel approaching the glomerular tuft at the vascular pole',
     ['Afferent arteriole', 'Efferent arteriole', 'Glomerular capillary loop', 'Parietal capsule']),
    ('D', 'Efferent arteriole', 'the vessel leaving the tuft at the vascular pole',
     ['Afferent arteriole', 'Efferent arteriole', 'Glomerular capillary loop', 'Parietal capsule']),
    ('E', 'Intraglomerular mesangium', 'the supporting region among capillary loops inside the tuft',
     ['Intraglomerular mesangium', 'Extraglomerular mesangium', 'Macula densa', 'Bowman’s space']),
    ('G', 'Visceral layer of Bowman’s capsule', 'the layer hugging capillary surfaces within the tuft',
     ['Visceral layer of Bowman’s capsule', 'Parietal layer of Bowman’s capsule', 'Macula densa', 'Extraglomerular mesangium']),
    ('H', 'Glomerular capillary loops', 'the looping vessels within the corpuscular tuft',
     ['Glomerular capillary loops', 'Bowman’s space', 'Macula densa', 'Parietal capsule']),
]
for letter, correct, feature, opts in diagram:
    key = opts.index(correct)
    rationales = []
    for option in opts:
        if option == correct:
            rationales.append(f'Leader line {letter} reaches {feature}; that is the {correct.lower()}.')
        else:
            rationales.append(f'{option} is a different labeled region; line {letter} instead reaches {feature}.')
    add_question(s, v, f'{correct} at {letter}', f'Which structure does leader line {letter} identify in this entire corpuscle diagram?',
                 opts, key, rationales, [feature.capitalize(), 'Follow the line to its terminal point'], extra_pages=(2,))

s = source_by_capture[7]
v = {'variant_id': s['variant_id'], 'image': s['image'], 'zoom_image': s['zoom_image']}
add_question(s, v, 'Capillary lumen in filtration TEM', 'In this filtration-barrier TEM, what does region D represent?',
             ['Capillary lumen', 'Urinary space', 'Glomerular basement membrane', 'Filtration slit'], 0,
             ['D lies below the endothelial layer, on the blood side of the barrier, in the capillary lumen.',
              'Urinary space lies above the podocyte processes, on the opposite side of the barrier from D.',
              'The basement membrane is the continuous middle band at C, above D.',
              'Filtration slits are the tiny gaps between upper podocyte processes at B, not the large lower region.'],
             ['Large lower compartment', 'Blood side of the endothelial layer'], kind='Cell/Tissue')
add_question(s, v, 'Blood cell in filtration TEM', 'In this filtration-barrier TEM, what does region E contain?',
             ['Blood cell', 'Podocyte foot process', 'Basement membrane', 'Urinary space'], 0,
             ['E overlies a cell within the lower capillary-lumen compartment of this TEM.',
              'Foot processes project into the upper urinary-space side at A, not within lower region E.',
              'The basement membrane is the continuous central band at C, not the cell in E.',
              'Urinary space is above the podocyte processes, not within the lower blood-side compartment.'],
             ['Cell profile within the capillary lumen', 'Below the continuous barrier band'], kind='Cell/Tissue')


# R2 compartment diagrams are three independent manual crops of RLS p. 26.
# The slide specifies solid = normal and dashed = post-infusion, with pink ICF
# and yellow ECF. The crop filenames are hidden until answer feedback.
volume_options = [
    'ICF decreases; ECF increases', 'ICF increases; ECF increases',
    'ICF unchanged; ECF increases', 'ICF decreases; ECF decreases',
]
osmolality_options = [
    'Higher in both compartments', 'Lower in both compartments',
    'Unchanged in both compartments', 'Higher in ECF but lower in ICF',
]
r2_cases = [
    ('Hypertonic Solution Addition.png', 0, 0,
     'The dashed pink left boundary moves inward, while the dashed yellow right boundary moves outward.',
     'The dashed top border is above the solid top border, indicating higher final osmolality.'),
    ('Hypotonic Solution Addition.png', 1, 1,
     'The dashed outline expands to the left of pink ICF and to the right of yellow ECF.',
     'The dashed top border sits below the solid top border, indicating lower final osmolality.'),
    ('Isotonic Solution Addition.png', 2, 2,
     'The pink ICF boundaries overlap; only the yellow ECF extends rightward in the dashed final outline.',
     'The dashed and solid top borders remain at the same height, indicating no osmolality change.'),
]
for filename, vol_key, osm_key, vol_clue, osm_clue in r2_cases:
    s = add_source('R2', filename, 'Diagram', 'Body-fluid compartment shifts', 26,
                   'Unlabeled crop of the source compartment graph; solid normal and dashed final outlines remain visible.')
    v = add_variant(s, 'Complete compartment comparison')
    rationales = []
    for j, option in enumerate(volume_options):
        if j == vol_key:
            rationales.append(vol_clue + ' This matches ' + option.lower() + '.')
        else:
            rationales.append(vol_clue + ' That visible width pattern conflicts with ' + option.lower() + '.')
    add_question(s, v, f'R2 compartment-volume direction {s["sha256"][:8]}',
                 'Compare solid baseline with dashed final outline. What happens to pink left ICF and yellow right ECF volume after the illustrated infusion?',
                 volume_options, vol_key, rationales,
                 ['Solid lines are the baseline', 'Dashed side boundaries show final compartment widths'],
                 kind='Comparison', extra_pages=(23,))
    rationales = []
    for j, option in enumerate(osmolality_options):
        if j == osm_key:
            rationales.append(osm_clue + ' Osmotic equilibration gives the same final direction in both compartments.')
        else:
            rationales.append(f'{option} conflicts with the dashed top-border height. ' + osm_clue)
    add_question(s, v, f'R2 final-osmolality direction {s["sha256"][:8]}',
                 'The graph height represents osmolality. Relative to the solid baseline, what does the dashed final top border show?',
                 osmolality_options, osm_key, rationales,
                 ['Compare the heights of solid and dashed top borders', 'Both compartment tops settle at the same final height'],
                 kind='Physiologic Interpretation', extra_pages=(23,))


# R4's four interventions each have four separately maskable outcome arrows.
# These answer the source diagram's simplified isolated-change model, not every
# possible severity or clinical state. The efferent-constriction asterisk stays.
s = add_source('R4', 'Changes in arteriole resistance alters RPF and GFR.png',
               'Diagram', 'Arteriolar resistance and filtration', 16,
               'Complete four-by-four source table; make one target-arrow mask per distinct cell.')
r4_rows = [
    ('Afferent constriction', 0, 380, [1, 1, 1, 2], [
        'higher entry resistance reduces plasma inflow',
        'reduced inflow lowers glomerular capillary hydrostatic pressure',
        'the fall in capillary pressure reduces filtration',
        'the simple diagram treats the RPF and GFR falls as proportionate; actual FF can shift modestly',
    ]),
    ('Afferent dilation', 1, 550, [0, 0, 0, 2], [
        'lower entry resistance increases plasma inflow',
        'greater inflow raises glomerular capillary hydrostatic pressure',
        'the rise in capillary pressure increases filtration',
        'the simple diagram treats the RPF and GFR rises as proportionate; actual FF can shift modestly',
    ]),
    ('Efferent constriction', 2, 718, [1, 0, 0, 0], [
        'higher outflow resistance reduces total renal plasma flow',
        'impeded outflow raises glomerular capillary hydrostatic pressure',
        'higher capillary pressure initially raises filtration; severe constriction can later reverse this',
        'RPF falls while GFR initially rises, so FF rises; the source asterisk flags an oncotic caveat',
    ]),
    ('Efferent dilation', 3, 885, [0, 1, 1, 1], [
        'lower outflow resistance raises total renal plasma flow',
        'easier outflow lowers glomerular capillary hydrostatic pressure',
        'the fall in capillary pressure lowers filtration',
        'GFR falls while RPF rises, so the filtered fraction falls',
    ]),
]
r4_metrics = ['RPF', 'Pgc', 'GFR', 'filtration fraction']
r4_x = [(757, 828), (1005, 1084), (1235, 1314), (1457, 1576)]
direction_options = ['Increase (↑)', 'Decrease (↓)', 'Approximately unchanged (↔)', 'No directional result is given']
for intervention, row_index, y, keys, mechanisms in r4_rows:
    for column, metric in enumerate(r4_metrics):
        x0, x1 = r4_x[column]
        if column == 3 and row_index in (0, 1):
            x1 = 1604  # remove both tips of the wide green ↔ arrow
        if column == 3 and row_index == 2:
            x1 = 1557  # keep the printed asterisk visible
        box = [x0, y - 54, x1, y + 57]
        v = add_variant(s, f'{intervention}: {metric}', box, fill='#e6f0df')
        key = keys[column]
        rationale = (f'In the {intervention.lower()} row, {metric} is shown as '
                     f'{direction_options[key].lower()} because {mechanisms[column]}.')
        rationales = []
        for j, option in enumerate(direction_options):
            if j == key:
                rationales.append(rationale)
            elif j == 3:
                rationales.append(f'The {intervention.lower()} row supplies a directional {metric} arrow; the blank covers that arrow rather than an unspecified cell.')
            else:
                rationales.append(f'{option} conflicts with the masked {metric} arrow for {intervention.lower()}; {mechanisms[column]}.')
        add_question(s, v, f'R4 {intervention} {metric} arrow',
                     f'In the complete arteriole-resistance table, which directional arrow fills the blank for {metric} under {intervention.lower()}?',
                     direction_options, key, rationales,
                     [f'Locate the {intervention.lower()} row and {metric} column', mechanisms[column].capitalize()],
                     kind='Direction of Change', extra_pages=(23, 24) if row_index == 2 else (15,))


# R5 overview and three-cell JGA diagram. Masks stay inside existing
# text-only callout areas. No vessel, tubular epithelium, leader, or H&E
# tissue is reconstructed.
s = add_source('R5', 'Juxtaglomerular Apparatus Diagram.png', 'Diagram',
               'Nephron location of the JGA', 9,
               'Whole-nephron diagram; one exterior JGA-title target is maskable without covering anatomy.')
v = add_variant(s, 'JGA location', [500, 30, 833, 113], fill='black')
add_question(s, v, 'R5 JGA location in nephron',
             'What is the blue-circled region where the distal tubule returns to the glomerular vascular pole?',
             ['Juxtaglomerular apparatus', 'Collecting duct', 'Loop of Henle', 'Proximal tubule'], 0,
             ['The blue circle surrounds the distal-tubule contact with the arterioles at the glomerular vascular pole, the JGA.',
              'The collecting duct is the separate descending yellow channel at the right, outside the blue circle.',
              'The loop of Henle is the long U-shaped tubular segment below the glomerulus, not the circled contact.',
              'The proximal tubule leaves the corpuscle toward the left, away from the blue-circled distal return.'],
             ['Distal tubule touches the vascular pole', 'Afferent and efferent vessels lie in the same circled region'],
             kind='Localization', extra_pages=(10,))

s = add_source('R5', 'Juxtaglomerular Apparatus Diagram 2.png', 'Diagram',
               'Three JGA cell populations', 10,
               'Three exterior label boxes point to separate JGA populations; mask one label interior at a time.')
r5_diagram_targets = [
    ('Juxtaglomerular cells', [947, 258, 1181, 325],
     'the modified arteriolar smooth-muscle cells along the vessel wall',
     ['Juxtaglomerular cells', 'Macula densa cells', 'Extraglomerular mesangial cells', 'Podocytes']),
    ('Macula densa cells', [939, 529, 1113, 599],
     'the tightly packed distal-tubule epithelial patch facing the arterioles',
     ['Macula densa cells', 'Juxtaglomerular cells', 'Extraglomerular mesangial cells', 'Podocytes']),
    ('Extraglomerular mesangial cells', [410, 608, 641, 677],
     'the cellular wedge between the contacting distal tubule and arterioles, outside the tuft',
     ['Extraglomerular mesangial cells', 'Intraglomerular mesangial cells', 'Macula densa cells', 'Podocytes']),
]
for target, box, feature, options in r5_diagram_targets:
    v = add_variant(s, target, box, fill='#fff9cf')
    rationales = []
    for option in options:
        if option == target:
            rationales.append(f'The blank callout points to {feature}; these are {target.lower()}.')
        else:
            rationales.append(f'{option} occupy a different location; the blank leader points to {feature}.')
    add_question(s, v, f'R5 JGA diagram {target}',
                 'Which cell population belongs in the blank callout of this complete JGA diagram?',
                 options, 0, rationales,
                 [feature.capitalize(), 'Follow the blank callout leader to its tip'],
                 kind='Cell/Tissue', extra_pages=(9,))

s = add_source('R5', 'Juxtaglomerular Apparatus Histo.png', 'Histology',
               'JGA histology at the vascular pole', 10,
               'Mask text only inside pre-existing opaque MD or JG boxes; leave arrows and tissue untouched.')
hist_targets = [
    ('Macula densa cells', [364, 625, 421, 683],
     'the compact epithelial group in the distal tubule beside the arteriole'),
    ('Juxtaglomerular cells', [325, 321, 384, 378],
     'the granular cells indicated along the arteriolar wall at the vascular pole'),
]
for target, box, feature in hist_targets:
    v = add_variant(s, target, box, fill='white')
    options = ['Macula densa cells', 'Juxtaglomerular cells',
               'Extraglomerular mesangial cells', 'Glomerular podocytes']
    key = options.index(target)
    rationales = []
    for option in options:
        if option == target:
            rationales.append(f'The blank box points to {feature}, which identifies {target.lower()}.')
        else:
            rationales.append(f'{option} do not match the arrowed {feature} in this H&E field.')
    add_question(s, v, f'R5 JGA H&E {target}',
                 'Which cell type is identified by the blank callout in this H&E vascular-pole field?',
                 options, key, rationales,
                 [feature.capitalize(), 'Compare the pointer with the adjacent tubule and arteriole'],
                 kind='Cell/Tissue', extra_pages=(9,))


assert len(sources) == 23 and len({q['question_id'] for q in questions}) == len(questions)
assert len(questions) == 47, Counter(q['collection'] for q in questions)
manifest = {
    'schema_version': 2, 'system': 'Renal', 'lecture_id': 'mixed',
    'source_directory': '../Renal/Manual', 'source_count_physical': 23,
    'approval': 'User approved multi-target prompt for all existing and future photos in conversation',
    'stage': 'Candidate derivatives; individual full-size QA pending',
    'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
    'sources': sources,
}
bank = {'schema_version': 2, 'bank_version': '2026-10-02-renal-multitarget-1',
        'title': 'Renal Picture Quiz', 'lecture': 'mixed', 'questions': questions}
coverage = {
    'schema_version': 1,
    'lectures': {
        'R1': {'status': 'Partial coverage',
               'tested_summary': ['Renal corpuscle and vascular-pole structures', 'Cortex versus medulla',
                                  'Filtration-barrier layers and direction', 'Urinary space and medullary mitochondrial comparison'],
               'gaps': ['Size-and-charge filterability graph', 'Osmolarity/tonicity visuals beyond the separate R2 captures',
                        'Full tubular identification, including proximal versus distal convoluted tubules'],
               'next_capture': 'An unlabeled manual capture from R1.2 Renal Histology p. 3 would improve cortical-structure testing.',
               'basis': 'R1 source and question review; 16 original captures, 7 scored image families. This is partial lecture coverage.'},
        'R2': {'status': 'Partial coverage',
               'tested_summary': ['ICF/ECF volume changes after three solution additions',
                                  'Shared final osmolality direction in the three diagrams'],
               'gaps': ['Other R2 visual targets and the two case-study images were not manually supplied.'],
               'next_capture': 'Supply additional manual R2 captures if broader visual coverage is wanted.',
               'basis': 'Three manual solution-addition diagrams matched to R2 RLS p. 26.'},
        'R4': {'status': 'Partial coverage',
               'tested_summary': ['The four-by-four arteriolar resistance outcome table, one masked arrow per cell'],
               'gaps': ['The capillary oncotic-pressure curves and clearance/Fick visuals were not manually supplied.'],
               'next_capture': 'Supply R4 manual captures for the oncotic-pressure and clearance graphs if desired.',
               'basis': 'One manual resistance-table capture matched to R4 RLS pp. 16 and 23–24.'},
        'R5': {'status': 'Partial coverage',
               'tested_summary': ['JGA position in the nephron', 'Three JGA cell groups in a diagram',
                                  'Macula densa and JG cells in H&E'],
               'gaps': ['Low/high NaCl TGF mediator and autoregulation-plateau figures were not manually supplied.'],
               'next_capture': 'Supply manual R5 TGF mediator or plateau captures if broader visual coverage is wanted.',
               'basis': 'Three manual JGA captures matched to R5 RLS pp. 9–10.'},
    },
}
(APP / 'data/source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(APP / 'data/question-bank.json').write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
(APP / 'data/review-queue.json').write_text(json.dumps({
    'schema_version': 2, 'items': [s for s in sources if s['status'] != 'USABLE']
}, ensure_ascii=False, indent=2) + '\n')
(APP / 'data/coverage.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')
print('sources', len(sources), 'questions', len(questions),
      'by lecture', dict(Counter(q['collection'] for q in questions)))
