"""Append approved R8 manual diagram as distinct masked visual targets.

Run once against the verified R7 baseline. Activation requires separate
individual full-size variant review, bank checks, and browser QA.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

APP = Path(__file__).resolve().parents[1]
MANUAL = Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual/R8')
VM = Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production/R8 - ADH and Aldosterone (Physiology)/lecture-manifest.json')
MP = APP / 'data/source-manifest.json'
BP = APP / 'data/question-bank.json'
CP = APP / 'data/coverage.json'
SOURCE = MANUAL / 'Blood Pressure Decrease.png'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

m = json.loads(MP.read_text())
b = json.loads(BP.read_text())
c = json.loads(CP.read_text())
vm = json.loads(VM.read_text())
assert len(m['sources']) == 34 and len(b['questions']) == 58
assert all(s['lecture_id'] != 'R8' for s in m['sources'])
assert all(q['collection'] != 'R8' for q in b['questions'])
assert vm['lecture_id'] == 'R8' and len(vm['sources']) == 9
for source in vm['sources']:
    path = Path(source['path'])
    assert path.is_file() and sha(path) == source['sha256']
capture = vm['picture_quiz_extraction']['capture_inventory']
assert len(capture) == 1 and capture[0]['path'] == str(SOURCE)
assert SOURCE.is_file() and sha(SOURCE) == capture[0]['sha256']

with Image.open(SOURCE) as original:
    original.load()
    assert original.size == (1702, 970) and original.format == 'PNG'
    width, height, mode = original.width, original.height, original.mode
    tiny = original.convert('L').resize((9, 8))
    bits = ''.join('1' if tiny.getpixel((x, y)) > tiny.getpixel((x + 1, y)) else '0'
                   for y in range(8) for x in range(8))
    phash = f'{int(bits, 2):016x}'

digest = sha(SOURCE)
original_asset = f'assets/{digest[:24]}.png'
if not (APP / original_asset).exists():
    shutil.copyfile(SOURCE, APP / original_asset)
assert sha(APP / original_asset) == digest
rls = next(s for s in vm['sources'] if s['kind'] == 'rls')
tran = next(s for s in vm['sources'] if s['kind'] == 'transcript' and 'Part 5' in s['path'])
slides = next(s for s in vm['sources'] if s['kind'] == 'annotated-slides')

s = {
    'relative_path': 'R8/' + SOURCE.name, 'extension': '.png',
    'bytes': SOURCE.stat().st_size, 'sha256': digest, 'kind': 'raster',
    'width': width, 'height': height, 'format': 'PNG', 'mode': mode,
    'decode_status': 'ok', 'asset_id': 'asset-' + digest[:16],
    'source_id': 'src-' + digest[:16], 'source_group_id': 'group-' + digest[:16],
    'perceptual_hash': phash, 'perceptual_hash_method': '64-bit dHash',
    'source_origin': 'lecture', 'acquisition': 'user manual RLS capture',
    'lecture_id': 'R8', 'system': 'Renal', 'status': 'USABLE',
    'modality': 'Diagram', 'tested_concept': 'Integrated response to falling pressure',
    'review_reason': 'One complete readable RLS p. 20 chart has independently identifiable renal autoregulation, RAAS, sympathetic, ADH, thirst, and ANP branches. Distinct target labels can be masked inside printed boxes without changing connecting arrows, borders, or other teaching content.',
    'ground_truth_basis': 'Original manual capture visually matched to the full R8 RLS p. 20 flowchart and transcript Part 5 pp. 1–3.',
    'source_citation': {'document': Path(rls['path']).name, 'page': 20, 'sha256': rls['sha256']},
    'rights_status': 'User-supplied course material, local educational use only; no redistribution authorization established',
    'original_asset': original_asset, 'variants': [], 'variant_review_complete': False,
    'question_type_matrix': [
        {'type': 'Distinct pathway steps and directional responses', 'supported': 'YES',
         'reason': 'Each listed target has a distinct printed box with directional arrows and enough surrounding labels to establish one best answer.'},
        {'type': 'Severe-loss numeric RPF/GFR prediction', 'supported': 'NO',
         'reason': 'The chart warns that profound sympathetic activation can reverse moderate-loss autoregulatory trends; no patient-specific numerical RPF/GFR is shown.'},
        {'type': 'Repeated downstream blood-volume/BP boxes', 'supported': 'NO',
         'reason': 'These duplicate the same terminal outcome on several arms and would add repetitive questions.'},
    ],
}

# Coordinates refer to immutable original pixels. Each mask is confined to the
# text-bearing interior of a colored box; arrows and box borders remain.
# Sample points are explicitly recorded, and yield a flat opaque local fill.
targets = [
    dict(code='afferent', title='Myogenic/TGF afferent response', box=[272, 319, 404, 399], sample=[283, 322],
         concept='R8 afferent dilation after falling pressure',
         stem='In the myogenic and macula-densa branches of this complete low-pressure diagram, what response belongs in the blank arteriole box immediately before RPF rises?',
         options=['Afferent arteriole dilates', 'Afferent arteriole constricts', 'Efferent arteriole dilates', 'Efferent arteriole constricts'], key=0,
         rationales=[
             'The blank box receives reduced afferent stretch and a macula-densa signal and leads to increased RPF; the source identifies afferent dilation.',
             'Afferent constriction would oppose the displayed rise in RPF and does not match the two incoming low-pressure signals.',
             'The blank box is explicitly on the afferent, not efferent, branch and precedes the RPF box.',
             'Efferent constriction is the separate Ang II branch to the right, not this box under the myogenic response.'
         ], clues=['Reduced afferent stretch and macula-densa inputs converge', 'The next box shows increased RPF'], qtype='Direction of Change'),
    dict(code='nacl', title='TGF macula-densa input', box=[594, 171, 756, 250], sample=[746, 180],
         concept='R8 lower NaCl delivery to macula densa',
         stem='In the TGF branch of this complete low-pressure diagram, what change is hidden in the box feeding the macula densa?',
         options=['Decreased NaCl delivery to the macula densa', 'Increased NaCl delivery to the macula densa', 'Increased plasma osmolarity at osmoreceptors', 'Decreased atrial stretch at volume receptors'], key=0,
         rationales=[
             'The hidden box lies directly above the macula densa in the TGF pathway under falling pressure; the RLS labels decreased NaCl delivery.',
             'An increase in NaCl delivery would be the opposite input from the low-pressure TGF branch shown.',
             'Plasma osmolarity is the separate right-hand hypothalamic branch, not the box leading into the macula densa.',
             'Atrial stretch is the far-left heart branch, not this kidney/TGF input.'
         ], clues=['The box sits below TGF and above macula densa', 'The neighboring branch raises renin release'], qtype='Physiologic Interpretation'),
    dict(code='renin', title='Juxtaglomerular output', box=[596, 366, 764, 447], sample=[751, 369],
         concept='R8 renin release from juxtaglomerular cells',
         stem='In this complete low-pressure diagram, which output belongs in the blank juxtaglomerular-cell box between the macula densa and the next RAAS mediator?',
         options=['Increased renin release', 'Decreased renin release', 'Increased ADH release', 'Decreased ANP release'], key=0,
         rationales=[
             'The blank JG-cell box follows low macula-densa NaCl and sympathetic β-adrenergic input and leads into the Ang II branch; it is increased renin release.',
             'The displayed low-NaCl and sympathetic inputs activate rather than suppress the JG-to-Ang II pathway.',
             'ADH is released through the separate posterior-pituitary branch on the right, not from JG cells.',
             'ANP belongs to the left atrial-stretch branch, not the JG-cell output.'
         ], clues=['Macula densa is directly upstream', 'Sympathetic β-adrenergic arrow also reaches JG cells'], qtype='Mechanism'),
    dict(code='angii', title='RAAS mediator', box=[639, 489, 711, 521], sample=[705, 489],
         concept='R8 angiotensin II as central RAAS mediator',
         stem='Which mediator is hidden in the central box after the juxtaglomerular-cell step and before the adrenal, efferent-arteriole, vascular, and thirst branches?',
         options=['Angiotensin II', 'Aldosterone', 'ADH', 'ANP'], key=0,
         rationales=[
             'The central mediator follows JG renin and fans out to the adrenal gland, efferent arteriole, systemic vessels, and thirst pathway; the RLS labels Ang II.',
             'Aldosterone appears downstream of the adrenal gland rather than at this upstream four-way branching point.',
             'ADH is downstream of the posterior pituitary and primarily feeds the water-reabsorption branch here.',
             'ANP belongs to the separate atrial-stretch branch and decreases with reduced atrial stretch.'
         ], clues=['The box follows JG cells', 'It has several outgoing arrows, including to adrenal gland and efferent arteriole'], qtype='Pathway'),
    dict(code='efferent', title='Ang II efferent response', box=[452, 528, 552, 607], sample=[453, 530],
         concept='R8 efferent constriction in low-pressure RAAS branch',
         stem='On the Ang II branch of this complete chart, what happens at the blank arteriole box that points toward the GFR response?',
         options=['Efferent arteriole constricts', 'Efferent arteriole dilates', 'Afferent arteriole constricts', 'Afferent arteriole dilates'], key=0,
         rationales=[
             'The blank box receives the Ang II arrow and points toward the GFR response; the RLS identifies preferential efferent constriction in this simplified compensation model.',
             'Efferent dilation is opposite the Ang II response pictured and would not support the displayed GFR direction in this model.',
             'The incoming arrow is the Ang II branch to the efferent box, not a low-pressure afferent-constriction pathway.',
             'Afferent dilation is the separate myogenic/TGF box at the far left; it is not the Ang II-linked blank box.'
         ], clues=['Ang II arrow enters this box', 'A separate far-left branch already handles afferent dilation'], qtype='Direction of Change'),
    dict(code='aldo', title='Adrenal output', box=[563, 664, 780, 698], sample=[773, 666],
         concept='R8 aldosterone release downstream of Ang II',
         stem='In the complete low-pressure diagram, which hormone response is hidden immediately after the adrenal gland and before renal Na⁺ reabsorption?',
         options=['Increased aldosterone release', 'Increased ADH release', 'Increased renin release', 'Decreased ANP release'], key=0,
         rationales=[
             'The blank box is directly below the Ang II-stimulated adrenal gland and directly above increased renal Na⁺ reabsorption; it is increased aldosterone release.',
             'ADH comes from the separate posterior-pituitary branch and points to renal water reabsorption.',
             'Renin is the earlier juxtaglomerular-cell output, upstream of Ang II and adrenal stimulation.',
             'Reduced ANP is the far-left atrial-stretch branch, not the adrenal output.'
         ], clues=['Adrenal gland is immediately above', 'Renal Na⁺ reabsorption is immediately below'], qtype='Pathway'),
    dict(code='baro', title='Baroreceptor signal', box=[1009, 173, 1153, 229], sample=[1144, 177],
         concept='R8 lower baroreceptor stretch with reduced EABV',
         stem='Under the falling plasma-volume branch, what signal is hidden inside the baroreceptor box before sympathetic activation?',
         options=['Decreased stretch', 'Increased stretch', 'Increased plasma osmolarity', 'Decreased NaCl delivery'], key=0,
         rationales=[
             'The box is downstream of lower effective arterial blood volume and upstream of sympathetic activity; the source shows reduced baroreceptor stretch.',
             'More stretch would accompany a different volume state than the downward plasma-volume arrow shown.',
             'Increased osmolarity is sensed by the separate right-hand osmoreceptor box, not baroreceptors in this branch.',
             'Macula-densa NaCl delivery is the separate kidney TGF branch, not this baroreceptor signal.'
         ], clues=['Plasma volume (EABV) falls above the box', 'Sympathetic nervous system is downstream'], qtype='Physiologic Interpretation'),
    dict(code='vasoconstriction', title='Convergent systemic vascular response', box=[937, 607, 1083, 688], sample=[1078, 608],
         concept='R8 systemic vasoconstriction from SNS and Ang II',
         stem='Which systemic response belongs in the blank box where sympathetic and Ang II arrows converge before blood pressure rises?',
         options=['Increased systemic vascular constriction', 'Decreased systemic vascular constriction', 'Increased renal water reabsorption', 'Increased renal Na⁺ reabsorption'], key=0,
         rationales=[
             'The converging sympathetic and Ang II arrows end in this vascular box, which then points to increased pressure; the RLS labels increased systemic vascular constriction.',
             'Systemic dilation would oppose the upward pressure outcome drawn below this box.',
             'Renal water reabsorption is the separate blue ADH branch on the right, not the convergent vascular node.',
             'Renal Na⁺ reabsorption is the separate aldosterone branch to the left, not the vascular node.'
         ], clues=['Two incoming arrows come from SNS and Ang II', 'An arrow descends to increased blood pressure'], qtype='Mechanism'),
    dict(code='adh', title='Posterior-pituitary output', box=[1257, 504, 1410, 536], sample=[1403, 504],
         concept='R8 ADH release from posterior pituitary',
         stem='In this complete chart, which hormonal response is hidden below the posterior pituitary and above renal water reabsorption?',
         options=['Increased ADH release', 'Increased aldosterone release', 'Increased renin release', 'Decreased ANP release'], key=0,
         rationales=[
             'The blank blue box directly follows the posterior pituitary and leads to renal H₂O reabsorption; the source labels increased ADH release.',
             'Aldosterone is the adrenal output on the central Na⁺-reabsorption branch, not the posterior-pituitary output.',
             'Renin is produced by the juxtaglomerular cells in the kidney branch, not by posterior pituitary.',
             'ANP is linked to the heart-atrial branch, not this water-reabsorption pathway.'
         ], clues=['Posterior pituitary is immediately above', 'Increased kidney H₂O reabsorption is immediately below'], qtype='Pathway'),
    dict(code='thirst', title='Convergent hypothalamic drinking drive', box=[1480, 534, 1654, 615], sample=[1647, 537],
         concept='R8 increased thirst from Ang II baroreceptor and osmoreceptor inputs',
         stem='What response belongs in the pink dashed box receiving Ang II, baroreceptor, and osmoreceptor signals and leading to water intake?',
         options=['Increased thirst', 'Decreased thirst', 'Increased renal Na⁺ excretion', 'Decreased renal water reabsorption'], key=0,
         rationales=[
             'The three dashed inputs converge on a hypothalamic response that points to increased H₂O intake; the RLS identifies increased thirst.',
             'Reduced thirst would not fit the downstream increased water-intake box and low-volume signals.',
             'Na⁺ excretion is a kidney output, not the hypothalamic drinking-drive node receiving these three inputs.',
             'Renal water reabsorption belongs to the posterior-pituitary/ADH arm, not this box pointing to intake.'
         ], clues=['Multiple dashed arrows converge', 'A dashed arrow continues to H₂O intake'], qtype='Integrated Mechanism'),
    dict(code='anp', title='Atrial-stretch ANP response', box=[119, 704, 219, 770], sample=[213, 706],
         concept='R8 lower ANP with lower atrial stretch',
         stem='On the heart-atrial branch of this complete low-pressure chart, what hormone change is hidden in the purple box?',
         options=['Decreased ANP release', 'Increased ANP release', 'Increased ADH release', 'Increased aldosterone release'], key=0,
         rationales=[
             'The atrial-volume-receptor arrow ends in this purple box under falling volume; the RLS shows lower stretch and reduced ANP.',
             'More ANP would be expected with greater atrial filling, not the low-volume branch displayed here.',
             'ADH is the posterior-pituitary output on the blue right-hand water pathway, not the atrial purple box.',
             'Aldosterone is the adrenal output near the middle Na⁺ pathway, not the heart-atrial signal.'
         ], clues=['Heart atrium and atrial volume receptors are directly upstream', 'A dashed arrow leaves toward the vascular response'], qtype='Pathway'),
]

assert len(targets) == 11 and len({t['code'] for t in targets}) == 11
questions = []
for t in targets:
    x0, y0, x1, y1 = t['box']
    sx, sy = t['sample']
    assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
    assert 0 <= sx < width and 0 <= sy < height
    with Image.open(SOURCE) as original:
        im = original.convert('RGB')
        fill_rgb = im.getpixel((sx, sy))
        fill = '#%02x%02x%02x' % fill_rgb
        ImageDraw.Draw(im).rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill_rgb)
        recipe = {
            'masks': [t['box']], 'input_dimensions': [width, height],
            'coordinate_basis': 'immutable_original_pixels',
            'method': 'Opaque target-label mask inside printed diagram box; no arrows, borders, or other boxes changed',
            'fill': fill, 'fill_sample_pixel': t['sample'], 'target': t['title'],
            'normalized_masks': [[x0 / width, y0 / height, x1 / width, y1 / height]],
        }
        key = hashlib.sha256((digest + json.dumps(recipe, sort_keys=True)).encode()).hexdigest()[:24]
        zoom = f'assets/{key}.png'
        display = f'assets/{key}.webp'
        im.save(APP / zoom)
        im.save(APP / display, format='WEBP', quality=92, method=6)
    v = {'variant_id': 'var-' + key, 'image': display, 'zoom_image': zoom,
         'transform': recipe, 'visual_review': 'PENDING individual native-resolution inspection'}
    s['variants'].append(v)
    if len(s['variants']) == 1:
        s.update(variant_id=v['variant_id'], image=display, zoom_image=zoom, transform=recipe)
    assert len(t['options']) == len(t['rationales']) == 4
    assert len(set(t['options'])) == len(set(t['rationales'])) == 4
    qid = 'q-' + hashlib.sha256((s['source_id'] + t['concept'] + v['variant_id']).encode()).hexdigest()[:20]
    citations = [s['source_citation'],
                 {'document': Path(tran['path']).name, 'page': 1 if t['code'] in ('afferent', 'nacl', 'renin', 'angii', 'efferent', 'aldo') else 2 if t['code'] in ('baro', 'vasoconstriction', 'adh') else 3,
                  'sha256': tran['sha256']},
                 {'document': Path(slides['path']).name, 'page': 15, 'sha256': slides['sha256']}]
    questions.append({
        'question_id': qid, 'asset_id': s['asset_id'],
        'source_group_id': s['source_group_id'], 'source_id': s['source_id'],
        'variant_id': v['variant_id'], 'question_type': t['qtype'],
        'tested_concept': t['concept'], 'stem': t['stem'],
        'visual_target': t['stem'], 'joint_composite': False,
        'options': t['options'], 'correct_index': t['key'],
        'choice_rationales': t['rationales'], 'explanation': t['rationales'][t['key']],
        'visual_clues': t['clues'], 'ground_truth_confidence': 'high',
        'ground_truth_basis': s['ground_truth_basis'], 'citations': citations,
        'image': display, 'zoom_image': zoom, 'original_image': original_asset,
        'original_filename': s['relative_path'], 'category': 'Diagram',
        'collection': 'R8', 'source_origin': 'lecture', 'status': 'USABLE',
        'case_context': '', 'accepted_synonyms': [],
    })

assert len(questions) == len({q['question_id'] for q in questions}) == 11
m['sources'].append(s)
m['source_count_physical'] = len(m['sources'])
m['approval'] = 'User approved full R8 quiz-generation prompt on 2026-10-05; existing multi-target rule retained.'
m['stage'] = 'R8 candidate masks generated; individual visual QA and browser validation pending'
m['generated_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
b['bank_version'] = '2026-10-05-renal-r8-1'
b['questions'].extend(questions)
c['lectures']['R8'] = {
    'status': 'Partial coverage',
    'tested_summary': ['Distinct masked renal autoregulation, RAAS, baroreceptor/SNS, ADH, thirst, and ANP responses in the RLS p. 20 integrated falling-pressure chart.'],
    'gaps': ['Only one manually supplied R8 diagram is available; there are no manual AQP2, SGK1–NEDD4–ENaC, free-water-clearance, potassium, or diabetes-insipidus captures.',
             'Repeated terminal blood-volume/BP boxes and ambiguous severe-loss quantitative RPF/GFR predictions are deliberately not scored.'],
    'next_capture': 'For broader R8 visual coverage, supply complete manual RLS captures of the ADH/AQP2 pathway, aldosterone/ENaC mechanism, free-water-clearance equation, or K⁺ handling figure.',
    'basis': 'One user-made manual R8 PNG verified against RLS p. 20 and transcript Part 5. Diagram branch questions are source-grouped and do not imply whole-lecture coverage.',
}
MP.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n')
BP.write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n')
CP.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\n')
(APP / 'data/review-queue.json').write_text(json.dumps({'schema_version': 2, 'items': [x for x in m['sources'] if x['status'] != 'USABLE']}, ensure_ascii=False, indent=2) + '\n')
print('R8 staged: 1 immutable capture, 11 distinct masked candidates, 1 source group; full-size QA pending')
