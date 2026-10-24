"""Replace first-pass R8 masks with full interior-only masks after visual QA."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
mp = root / 'data/source-manifest.json'
bp = root / 'data/question-bank.json'
original_path = Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual/R8/Blood Pressure Decrease.png')
m = json.loads(mp.read_text())
b = json.loads(bp.read_text())
s = next(x for x in m['sources'] if x['lecture_id'] == 'R8')
assert len(s['variants']) == 11
assert sum(q['collection'] == 'R8' for q in b['questions']) == 11
assert hashlib.sha256(original_path.read_bytes()).hexdigest() == s['sha256']
boxes = {
    'Myogenic/TGF afferent response': [272, 319, 404, 399],
    'TGF macula-densa input': [594, 171, 756, 250],
    'Juxtaglomerular output': [596, 366, 764, 447],
    'RAAS mediator': [639, 489, 711, 521],
    'Ang II efferent response': [452, 528, 552, 607],
    'Adrenal output': [563, 664, 780, 698],
    'Baroreceptor signal': [1009, 173, 1153, 229],
    'Convergent systemic vascular response': [937, 607, 1083, 688],
    'Posterior-pituitary output': [1257, 504, 1410, 536],
    'Convergent hypothalamic drinking drive': [1480, 534, 1654, 615],
    'Atrial-stretch ANP response': [119, 704, 219, 770],
}
assert {v['transform']['target'] for v in s['variants']} == set(boxes)
updates = {}
for v in s['variants']:
    oldid = v['variant_id']
    recipe = dict(v['transform'])
    box = boxes[recipe['target']]
    recipe['masks'] = [box]
    recipe['normalized_masks'] = [[box[0]/s['width'], box[1]/s['height'],
                                   box[2]/s['width'], box[3]/s['height']]]
    digest = hashlib.sha256((s['sha256'] + json.dumps(recipe, sort_keys=True)).encode()).hexdigest()[:24]
    with Image.open(original_path) as original:
        im = original.convert('RGB')
        ImageDraw.Draw(im).rectangle((box[0], box[1], box[2]-1, box[3]-1), fill=recipe['fill'])
        zoom = f'assets/{digest}.png'
        display = f'assets/{digest}.webp'
        im.save(root/zoom)
        im.save(root/display, format='WEBP', quality=92, method=6)
    v.update(variant_id='var-'+digest, image=display, zoom_image=zoom,
             transform=recipe, visual_review='PENDING second-pass full-size review')
    updates[oldid] = v
for q in b['questions']:
    if q['collection'] != 'R8':
        continue
    v = updates[q['variant_id']]
    q.update(variant_id=v['variant_id'], image=v['image'], zoom_image=v['zoom_image'])
    q['question_id'] = 'q-' + hashlib.sha256((s['source_id']+q['tested_concept']+v['variant_id']).encode()).hexdigest()[:20]
first=s['variants'][0]
s.update(variant_id=first['variant_id'], image=first['image'], zoom_image=first['zoom_image'], transform=first['transform'])
s['variant_review_complete'] = False
m['stage']='R8 expanded interior masks generated; second-pass individual QA pending'
assert len({q['question_id'] for q in b['questions']}) == len(b['questions'])
mp.write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n')
bp.write_text(json.dumps(b, ensure_ascii=False, indent=2)+'\n')
print('Replaced 11 R8 mask variants; old derivatives retained unreferenced for audit history.')
