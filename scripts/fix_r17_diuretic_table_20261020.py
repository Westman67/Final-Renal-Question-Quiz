"""Learner flag fix (2026-10-20): block the Na+ and Ca2+ body cells in the R17 diuretic table question.

Usage: python3 scripts/fix_r17_diuretic_table_20261020.py stage   (render preview into backups/stage-20261020/)
       python3 scripts/fix_r17_diuretic_table_20261020.py commit  (copy assets and update pathology data; run once)
The original capture and its zoom copy are untouched. Question ID is unchanged so browser progress is preserved.
"""
import datetime
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mask_tools import build_masked, save_variant, sha_bytes  # noqa: E402

root = Path(__file__).resolve().parents[1]
STAGE = root / 'backups/stage-20261020'
QID = 'q-b162e3a354041916d035'
SRC = 'src-3b0c6ce91762d719'
# Body cells only (headers stay visible so the learner knows which columns are hidden). One block per row cell.
NA_X, CA_X = (367, 545), (728, 906)
ROWS = [(123, 252), (254, 352), (354, 457), (459, 568), (571, 670), (672, 770)]
BOXES = [[x0, y0, x1, y1] for (x0, x1) in (NA_X, CA_X) for (y0, y1) in ROWS]
REASON = ('Urinary Na+ and Ca2+ body cells were blocked because their arrows state the answer. Row names, diuresis circles, '
          'K+, Mg2+, Cl- and maximum filtered Na+ excreted remain unchanged.')
TARGET = 'Na+ and Ca2+ columns blocked; remaining columns give row context'

bank_path = root / 'data/pathology/question-bank.json'
man_path = root / 'data/pathology/source-manifest.json'
bank = json.loads(bank_path.read_text())
man = json.loads(man_path.read_text())
src = next(s for s in man['sources'] if s['source_id'] == SRC)
q = next(x for x in bank['questions'] if x['question_id'] == QID)
original = root / src['original_asset']
assert sha_bytes(original.read_bytes()) == src['sha256']
im, tr, digest = build_masked(original, BOXES, REASON, TARGET)

if sys.argv[1:] == ['stage']:
    save_variant(im, digest, STAGE)
    print('staged', digest, STAGE)
    raise SystemExit
assert sys.argv[1:] == ['commit']
assert q['variant_id'] != 'var-' + digest, 'already applied'
save_variant(im, digest, root / 'assets')
old = q['variant_id']
tr['supersedes_variant'] = old
variant = {'variant_id': 'var-' + digest, 'image': f'assets/{digest}.webp', 'zoom_image': f'assets/{digest}.png', 'transform': tr,
           'visual_review': 'passed at native size against original'}
src['variants'] = [variant]
src.update(variant_id=variant['variant_id'], image=variant['image'], zoom_image=variant['zoom_image'], transform=tr,
           review_reason='Source-backed visually dependent question; Na+ and Ca2+ cells blocked after learner flag.')
src['visual_review'] = {'status': 'passed', 'checked_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                        'original_and_variant_compared': True,
                        'answer_leakage': 'Na+ and Ca2+ columns blocked; no answer-bearing cell remains',
                        'diagnostic_pixels_preserved': True}
q.update(variant_id=variant['variant_id'], image=variant['image'], zoom_image=variant['zoom_image'],
         stem='The urinary Na⁺ and Ca²⁺ columns are hidden. Which listed diuretic class increases urinary Na⁺ yet decreases urinary Ca²⁺?',
         visual_target='Class rows with the Na⁺ and Ca²⁺ cells blocked; diuresis, K⁺, Mg²⁺, Cl⁻ and maximum filtered Na⁺ excreted remain as row context.',
         visual_clues=['Hidden Na⁺ and Ca²⁺ cells must be recalled for each class row',
                       'After answering, the teaching original shows the thiazide row with Na⁺ up and Ca²⁺ down'])
bank['bank_version'] += '+2026-10-20-r17-table-mask'
bank_path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + '\n')
(root / 'data/pathology/flag-remediation.json').write_text(json.dumps({
    'schema_version': 1, 'batch_id': 'renal-pathology-flags-2026-10-20-r1',
    'created_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
    'flagged_question_ids': [QID]}, indent=2) + '\n')
print('committed', digest)
