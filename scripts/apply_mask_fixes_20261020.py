"""Answer-leak fixes and new blocked-cell questions (2026-10-20), approved by the owner.

Usage: python3 scripts/apply_mask_fixes_20261020.py stage   (render previews into backups/stage-20261020-b/)
       python3 scripts/apply_mask_fixes_20261020.py commit  (copy assets and update both banks; run once)
Originals are never modified. Question IDs of existing questions are unchanged so browser progress is preserved.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mask_tools import digest_for, pathology_transform, physiology_transform, render, save_variant  # noqa: E402

root = Path(__file__).resolve().parents[1]
STAGE = root / 'backups/stage-20261020-b'
PATH = dict(bank=root / 'data/pathology/question-bank.json', man=root / 'data/pathology/source-manifest.json', cov=root / 'data/pathology/coverage.json')
PHYS = dict(bank=root / 'data/question-bank.json', man=root / 'data/source-manifest.json', cov=root / 'data/coverage.json')
D = {'path': PATH, 'phys': PHYS}

# ---- geometry -------------------------------------------------------------------------------------------------
COLS = {'A1': (864, 1180), 'A2': (1189, 1485), 'A3': (1494, 1788)}
ROWS = {'G1': (779, 906), 'G2': (912, 1036), 'G3a': (1042, 1180), 'G3b': (1185, 1325), 'G4': (1330, 1455), 'G5': (1462, 1585)}


def risk(g, a):
    return {'box': [COLS[a][0], ROWS[g][0], COLS[a][1], ROWS[g][1]], 'keep_color': True}


def box(x0, y0, x1, y1, label='?'):
    return {'box': [x0, y0, x1, y1], 'label': label}


R17 = {'dia': (188, 363), 'na': (367, 545), 'k': (549, 725), 'ca': (728, 906), 'mg': (911, 1087), 'cl': (1091, 1267), 'max': (1271, 1446)}
R17ROWS = [(123, 252), (254, 352), (354, 457), (459, 568), (571, 670), (672, 770)]


def t17(col, row):
    return box(R17[col][0], R17ROWS[row][0], R17[col][1], R17ROWS[row][1])


# ---- existing questions: replace the learner image (same question id) --------------------------------------------
FIXES = [
    dict(bank='path', qid='q-c7dad792051d8afa32aa', specs=[risk('G4', 'A3')],
         target='G4 and A3 cell text hidden; cell color and every other cell and heading kept',
         reason='The printed action and frequency in the G4 and A3 cell were hidden behind a question mark. The cell keeps its own color, so the map color scale and neighboring cells still support the answer.',
         upd=dict(stem='The text in the G4 and A3 cell is hidden, but its color is kept. Using the color scale and neighboring cells, which action and frequency belong there?',
                  visual_target='G4 row crossed with A3 column with the printed text hidden, retaining the complete row and column headings and every other cell',
                  visual_clues=['The cell is the darkest maroon, matching every G5 cell', 'Cells above and to the left, G3b and A3 and G4 and A2, are the lighter red of Refer 3'])),
    dict(bank='path', qid='q-1fef41f50349faa42368',
         specs=[box(232, 253, 336, 300, ''), box(541, 253, 636, 300, ''), box(232, 1098, 336, 1142, ''), box(541, 1098, 636, 1142, ''),
                box(1783, 740, 1893, 785, ''), box(2097, 740, 2182, 785, '')],
         target='H+ pump arrows and the HCO3- exchanger arrow hidden; pumps, labels, pH boxes and Cl- arrow kept',
         reason='The arrowheads and shafts beside the two apical H+ ATPases and the basolateral HCO3- exchanger were hidden because the arrows state the answer.',
         upd=dict(stem='The arrows beside the apical H⁺ ATPases and the basolateral HCO₃⁻ exchanger are hidden. Which paired direction of transport belongs in this alpha-intercalated cell?',
                  visual_target='Apical H⁺ pumps and basolateral HCO₃⁻ exchanger with their arrows hidden, lumen at left and blood at right',
                  visual_clues=['After answering, the teaching original shows leftward apical H⁺ arrows', 'After answering, the teaching original shows a rightward basolateral HCO₃⁻ arrow'])),
    dict(bank='phys', qid='q-feff8e2e753cb4e5f818', specs=[box(705, 610, 1050, 648)],
         target='Tm callout explanation hidden', reason='The callout text stating that glucose carriers are saturated was hidden because it names the plateau mechanism.', upd={}),
    dict(bank='phys', qid='q-50974bb5a3c9a279897d', specs=[box(380, 236, 690, 362), box(768, 230, 1006, 356)],
         target='Two buffering curve labels hidden', reason='The labels over the extracellular and cellular buffering curves were hidden because they name the answer.', upd={}),
]

# ---- new questions: one blocked region each ---------------------------------------------------------------------
NEW = [
    dict(bank='path', base='q-c7dad792051d8afa32aa', key='r31-g2-a1', specs=[risk('G2', 'A1')], pos=1, concept='G2 and A1 risk map cell', qtype='Table Interpretation',
         stem='The text in the G2 and A1 cell is hidden, but its color is kept. Which action and frequency belong there?',
         correct='Monitor; 1', wrong=['Monitor; 2', 'Refer; 3', 'Refer; 4+'],
         rats=['The dark green color marks the lowest-risk cells, and the G1 and A1 cell directly above prints Monitor with frequency 1.',
               'Monitor 2 is printed in orange cells such as G3b and A1, not in a dark green cell.',
               'Refer 3 is printed in red cells in the higher-risk part of the map.',
               'Refer 4+ is printed only in the darkest maroon cells, not in a dark green cell.'],
         clues=['Dark green matches the visible G1 and A1 cell', 'Lowest-risk cells print Monitor with frequency 1'], target='G2 and A1 cell text hidden, cell color kept'),
    dict(bank='path', base='q-c7dad792051d8afa32aa', key='r31-g3a-a1', specs=[risk('G3a', 'A1')], pos=3, concept='G3a and A1 risk map cell', qtype='Table Interpretation',
         stem='The text in the G3a and A1 cell is hidden, but its color is kept. Which action and frequency belong there?',
         correct='Monitor; 1', wrong=['Monitor; 2', 'Refer; 2', 'Refer; 3'],
         rats=['The yellow color matches the G1 and A2 cell and the G2 and A2 cell, which print Monitor with frequency 1.',
               'Monitor 2 is printed in orange cells such as G3a and A2, not in a yellow cell.',
               'Refer 2 appears with an asterisk in orange cells in the A3 column, not in a yellow cell.',
               'Refer 3 is printed in red cells, which are darker than this yellow cell.'],
         clues=['Yellow matches the visible G1 and A2 and G2 and A2 cells', 'Yellow cells print Monitor with frequency 1'], target='G3a and A1 cell text hidden, cell color kept'),
    dict(bank='path', base='q-c7dad792051d8afa32aa', key='r31-g3b-a3', specs=[risk('G3b', 'A3')], pos=0, concept='G3b and A3 risk map cell', qtype='Table Interpretation',
         stem='The text in the G3b and A3 cell is hidden, but its color is kept. Which action and frequency belong there?',
         correct='Refer; 3', wrong=['Monitor; 2', 'Refer; 4+', 'Monitor; 1'],
         rats=['The red color matches the G3a and A3 cell directly above, which prints Refer with frequency 3.',
               'Monitor 2 is printed in orange cells, not in a red cell.',
               'Refer 4+ is printed in the darkest maroon cells at G5 and G4 and A3, which are darker than this red cell.',
               'Monitor 1 is printed in green and yellow cells, which are lower risk than this red cell.'],
         clues=['Red matches the visible G3a and A3 cell above', 'Red cells in the A3 column print Refer 3'], target='G3b and A3 cell text hidden, cell color kept'),
    dict(bank='path', base='q-c7dad792051d8afa32aa', key='r31-g5-a1', specs=[risk('G5', 'A1')], pos=2, concept='G5 and A1 risk map cell', qtype='Table Interpretation',
         stem='The text in the G5 and A1 cell is hidden, but its color is kept. Which action and frequency belong there?',
         correct='Refer; 4+', wrong=['Refer; 3', 'Monitor; 2', 'Refer; 2'],
         rats=['The maroon color matches the G5 and A2 cell, the G5 and A3 cell and the G4 and A3 cell, which all print Refer with 4+.',
               'Refer 3 is printed in red cells, which are lighter than this maroon cell.',
               'Monitor 2 is printed in orange cells, not in a maroon cell.',
               'Refer 2 appears in orange cells in the A3 column, not in a maroon cell.'],
         clues=['Maroon matches the other G5 cells', 'Maroon cells print Refer with 4+'], target='G5 and A1 cell text hidden, cell color kept'),
    dict(bank='path', base='q-b162e3a354041916d035', key='r17-k-aldosterone', specs=[t17('k', 4)], pos=0, concept='Aldosterone antagonist urinary potassium pattern', qtype='Table Interpretation',
         stem='The urinary K⁺ cell for aldosterone antagonists is hidden. Which change belongs there?',
         correct='Decrease (↓)', wrong=['Increase (↑)', 'Marked increase (↑↑)', 'No change (↔)'],
         rats=['Aldosterone antagonists are potassium sparing, and the ENaC blocker row below shows the same downward red arrow.',
               'A single upward K⁺ arrow is shown for classes such as osmotic diuretics and thiazides, not for potassium-sparing drugs.',
               'Two upward K⁺ arrows are shown for carbonic anhydrase inhibitors and loop diuretics, which waste potassium.',
               'No class in the K⁺ column shows a horizontal arrow, and potassium-sparing drugs lower urinary K⁺.'],
         clues=['The ENaC blocker row below shows a downward red K⁺ arrow', 'Potassium-sparing classes are the only downward K⁺ arrows'], target='Aldosterone antagonist K+ cell hidden'),
    dict(bank='path', base='q-b162e3a354041916d035', key='r17-diuresis-loop', specs=[t17('dia', 2)], pos=2, concept='Loop diuretic diuresis magnitude', qtype='Table Interpretation',
         stem='The diuresis circles for loop diuretics are hidden. Which relative diuresis belongs in that cell?',
         correct='Four circles (greatest diuresis)', wrong=['Three circles', 'Two circles', 'One circle'],
         rats=['Loop diuretics have the greatest diuretic effect in the table, shown by four circles and the largest maximum filtered Na⁺ excretion.',
               'No class in the table is shown with three circles.',
               'Two circles mark carbonic anhydrase inhibitors, osmotic diuretics and thiazides, which excrete far less filtered Na⁺ than loop diuretics.',
               'One circle marks the potassium-sparing classes, which have the smallest diuresis.'],
         clues=['Other rows show two circles or one circle', 'Loop diuretics have the largest maximum Na⁺ excretion'], target='Loop diuretic diuresis circles hidden'),
    dict(bank='path', base='q-b162e3a354041916d035', key='r17-max-na-loop', specs=[t17('max', 2)], pos=1, concept='Loop diuretic maximum filtered sodium excreted', qtype='Table Interpretation',
         stem='The maximum percent of filtered Na⁺ excreted for loop diuretics is hidden. Which value belongs there?',
         correct='25%', wrong=['8%', '50%', '3%'],
         rats=['Loop diuretics have the highest maximum fraction of filtered Na⁺ excreted in the table, 25%, above the 20% shown for osmotic diuretics.',
               '8% is the thiazide value, which is shown in its own row.',
               '50% is far above any value in the table, whose largest entry is 25%.',
               '3% is the value for the potassium-sparing classes, the weakest diuretics in the table.'],
         clues=['Osmotic diuretics show 20% and thiazides show 8%', 'Loop diuretics have the greatest diuresis'], target='Loop diuretic maximum Na+ excreted cell hidden'),
    dict(bank='path', base='q-b162e3a354041916d035', key='r17-ca-loop', specs=[t17('ca', 2)], pos=3, concept='Loop diuretic urinary calcium pattern', qtype='Table Interpretation',
         stem='The urinary Ca²⁺ cell for loop diuretics is hidden. Which change belongs there?',
         correct='Marked increase (↑↑)', wrong=['Decrease (↓)', 'No change (↔)', 'Single increase (↑)'],
         rats=['Loop diuretics remove the lumen-positive drive for paracellular Ca²⁺ reabsorption, so urinary Ca²⁺ rises and the cell shows two upward arrows.',
               'A downward Ca²⁺ arrow belongs to thiazides, which lower urinary Ca²⁺.',
               'Horizontal Ca²⁺ arrows mark carbonic anhydrase inhibitors, osmotic diuretics, aldosterone antagonists and ENaC blockers.',
               'A single upward arrow understates the loop effect, which the table shows with two arrows.'],
         clues=['The thiazide row shows the opposite, a downward Ca²⁺ arrow', 'Loop diuretics have the largest Na⁺ effect'], target='Loop diuretic Ca2+ cell hidden'),
]


def load(which):
    p = D[which]
    return json.loads(p['bank'].read_text()), json.loads(p['man'].read_text())


banks = {k: load(k) for k in D}
for spec in FIXES + NEW:
    bank, man = banks[spec['bank']]
    qid = spec.get('qid') or spec['base']
    q = next(x for x in bank['questions'] if x['question_id'] == qid)
    s = next(x for x in man['sources'] if x['source_id'] == q['source_id'])
    original = root / s['original_asset']
    im, records, size, sha = render(original, spec['specs'])
    assert sha == s['sha256'], 'original hash changed'
    mk = pathology_transform if spec['bank'] == 'path' else physiology_transform
    tr = mk(records, size, spec['target'], spec.get('reason') or 'Answer-bearing region blocked for a recall question; every other pixel unchanged.')
    digest = digest_for(sha, tr)
    spec['_img'], spec['_tr'], spec['_digest'], spec['_q'], spec['_s'] = im, tr, digest, q, s

if sys.argv[1:] == ['stage']:
    for spec in FIXES + NEW:
        save_variant(spec['_img'], spec['_digest'], STAGE)
        print(spec.get('key') or spec['qid'], spec['_digest'])
    raise SystemExit
assert sys.argv[1:] == ['commit']
now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
for spec in FIXES + NEW:
    save_variant(spec['_img'], spec['_digest'], root / 'assets')


def vrec(spec):
    d = spec['_digest']
    return {'variant_id': 'var-' + d, 'image': f'assets/{d}.webp', 'zoom_image': f'assets/{d}.png', 'transform': spec['_tr'],
            'visual_review': 'passed at native size against original'}


for spec in FIXES:
    bank, man = banks[spec['bank']]
    q, s = spec['_q'], spec['_s']
    v = vrec(spec)
    old = q['variant_id']
    assert sum(x['variant_id'] == old for x in bank['questions']) == 1, 'variant shared'
    v['transform']['supersedes_variant'] = old
    s['variants'] = [v if x['variant_id'] == old else x for x in s['variants']]
    assert any(x['variant_id'] == v['variant_id'] for x in s['variants'])
    q.update(variant_id=v['variant_id'], image=v['image'], zoom_image=v['zoom_image'], **spec['upd'])
    if 'variant_id' in s and s['variant_id'] == old:
        s.update(variant_id=v['variant_id'], image=v['image'], zoom_image=v['zoom_image'], transform=v['transform'])
    s['visual_review'] = ({'status': 'passed', 'checked_at': now, 'original_and_variant_compared': True,
                           'answer_leakage': 'answer-bearing region blocked 2026-10-20', 'diagnostic_pixels_preserved': True}
                          if spec['bank'] == 'path' else 'PASS: original and final variant inspected at native size; answer-bearing region blocked 2026-10-20.')
for spec in NEW:
    bank, man = banks[spec['bank']]
    base, s = spec['_q'], spec['_s']
    v = vrec(spec)
    s['variants'].append(v)
    opts = list(spec['wrong'])
    opts.insert(spec['pos'], spec['correct'])
    rats = list(spec['rats'][1:])
    rats.insert(spec['pos'], spec['rats'][0])
    assert len(set(opts)) == 4 and all(len(r) > 25 for r in rats)
    nq = {k: base[k] for k in ('asset_id', 'source_group_id', 'source_id', 'ground_truth_confidence', 'ground_truth_basis', 'citations', 'category',
                                'collection', 'source_origin', 'status', 'original_image', 'original_filename')}
    nq.update(question_id='q-' + hashlib.sha1((base['source_id'] + '|' + spec['key']).encode()).hexdigest()[:20], variant_id=v['variant_id'],
              question_type=spec['qtype'], tested_concept=spec['concept'], stem=spec['stem'], visual_target=spec['target'], joint_composite=False,
              options=opts, correct_index=spec['pos'], choice_rationales=rats, explanation=spec['rats'][0], visual_clues=spec['clues'],
              image=v['image'], zoom_image=v['zoom_image'], case_context='', accepted_synonyms=[])
    assert nq['question_id'] not in {x['question_id'] for x in bank['questions']}
    bank['questions'].append(nq)
for which, (bank, man) in banks.items():
    bank['bank_version'] += '+2026-10-20-mask-fixes'
    D[which]['bank'].write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
    D[which]['man'].write_text(json.dumps(man, ensure_ascii=False, indent=2) + '\n')
cov = json.loads(PATH['cov'].read_text())
for lec in ('R17', 'R31'):
    for spec in NEW:
        if spec['_q']['collection'] == lec and spec['concept'] not in cov['lectures'][lec]['tested_summary']:
            cov['lectures'][lec]['tested_summary'].append(spec['concept'])
PATH['cov'].write_text(json.dumps(cov, ensure_ascii=False, indent=2) + '\n')
print('committed', len(FIXES), 'fixes and', len(NEW), 'new questions')
