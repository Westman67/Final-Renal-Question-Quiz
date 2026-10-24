"""Replace oversized exterior-key mask with lossless exterior crop after mobile visual QA."""
import json,hashlib
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1];mp=root/'data/source-manifest.json';bp=root/'data/question-bank.json'
m=json.loads(mp.read_text());b=json.loads(bp.read_text())
s=next(x for x in m['sources'] if x['relative_path']=='R7/Collecting Duct Principal and Intercalated Cells EM.png')
assert len(s['variants'])==1 and s['variants'][0]['variant_id']=='var-b5d56cb35bfc9686936b6846'
old=s['variants'][0]
assert sum(q['source_id']==s['source_id'] for q in b['questions'])==2
crop=[0,138,320,584]
recipe={'masks':[],'input_dimensions':[s['width'],s['height']],'coordinate_basis':'immutable_original_pixels','method':'Lossless exterior answer-key crop; no tissue changes','fill':'#f4edcf','target':'Red-starred versus unstarred collecting-duct cells','normalized_masks':[],'crop':crop,'normalized_crop':[0,138/584,1,1]}
key=hashlib.sha256((s['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
zoom=f'assets/{key}.png';display=f'assets/{key}.webp';vid='var-'+key
with Image.open('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual/R7/Collecting Duct Principal and Intercalated Cells EM.png') as original:
 im=original.convert('RGB').crop(crop);im.save(root/zoom);im.save(root/display,format='WEBP',quality=92,method=6)
v={'variant_id':vid,'image':display,'zoom_image':zoom,'transform':recipe,'visual_review':'PENDING new crop full-size review'}
s['variants']=[v];s.update(variant_id=vid,image=display,zoom_image=zoom,transform=recipe,variant_review_complete=False,visual_review='Crop changed after mobile QA; native-size review pending.')
for q in b['questions']:
 if q['source_id']!=s['source_id']:continue
 assert q['variant_id']==old['variant_id']
 q['variant_id']=vid;q['image']=display;q['zoom_image']=zoom
 ident=hashlib.sha256((s['source_id']+q['tested_concept']+vid).encode()).hexdigest()[:20]
 q['question_id']='q-'+ident
assert len({q['question_id'] for q in b['questions']})==len(b['questions'])
m['stage']='R7 SEM exterior key cropped; full-size QA pending'
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');bp.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
print('new crop',vid,zoom)
