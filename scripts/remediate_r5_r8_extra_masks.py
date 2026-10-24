"""Replace seven leaky first-pass masks after native-size visual review."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')
MP=ROOT/'data/source-manifest.json';BP=ROOT/'data/question-bank.json'
m=json.loads(MP.read_text());b=json.loads(BP.read_text())
changes={
 'R5 low-pressure TGF efferent constriction': [([76,214,270,266],[149,207])],
 'R5 high-pressure TGF afferent constriction': [([782,237,1026,285],[840,213])],
 'R6 apical sodium glucose cotransporter': [([615,283,739,328],[650,272]),([47,445,474,476],[44,432])],
 'R6 basolateral facilitated glucose transporter': [([1006,327,1136,370],[1020,324]),([1158,441,1711,483],[1155,432])],
 'R6 proximal tubule apical sodium hydrogen exchanger': [([193,436,296,502],[194,432])],
 'R7 type 2 convoluted distal tubule cell': [([205,21,344,70],[440,47]),([157,440,401,477],[410,457])],
}
done=set()
for s in m['sources']:
 if s.get('batch_id')!='2026-10-05-r5-r8-extra' or s['status']!='USABLE':continue
 for v in s['variants']:
  concept=v['transform']['target']
  if concept not in changes:continue
  assert concept not in done
  oldid=v['variant_id']
  original=SOURCE/s['relative_path'];assert hashlib.sha256(original.read_bytes()).hexdigest()==s['sha256']
  with Image.open(original) as base:
   im=base.convert('RGB');w,h=im.size;fills=[];boxes=[]
   for box,sample in changes[concept]:
    x0,y0,x1,y1=box;sx,sy=sample
    fill=im.getpixel((sx,sy));ImageDraw.Draw(im).rectangle((x0,y0,x1-1,y1-1),fill=fill)
    boxes.append(box);fills.append(dict(sample=sample,rgb=fill))
   recipe=dict(masks=boxes,input_dimensions=[w,h],coordinate_basis='immutable_original_pixels',
       method='Opaque target-text masks only; no graph data, arrows, cell borders, or tissue changed',
       fills=fills,target=concept,normalized_masks=[[a/w,b/h,c/w,d/h] for a,b,c,d in boxes])
   key=hashlib.sha256((s['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
   zoom=f'assets/{key}.png';display=f'assets/{key}.webp'
   im.save(ROOT/zoom);im.save(ROOT/display,format='WEBP',quality=92,method=6)
  v.update(variant_id='var-'+key,image=display,zoom_image=zoom,transform=recipe,
           visual_review='PENDING second-pass individual native-size review')
  if s.get('variant_id')==oldid:s.update(variant_id=v['variant_id'],image=display,zoom_image=zoom,transform=recipe)
  q=next(q for q in b['questions'] if q['variant_id']==oldid)
  q.update(variant_id=v['variant_id'],image=display,zoom_image=zoom,
           question_id='q-'+hashlib.sha256((s['source_id']+concept+v['variant_id']).encode()).hexdigest()[:20])
  done.add(concept)
assert done==set(changes)
MP.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
BP.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
print('Regenerated',len(done),'target masks from immutable originals; QA still pending')
