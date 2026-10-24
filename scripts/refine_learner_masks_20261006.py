"""Native-size QA corrections to the first learner-flag mask pass."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=R/'data/source-manifest.json';B=R/'data/question-bank.json';P=R/'reports/learner-flag-remediation-2026-10-06.json'
m=json.loads(M.read_text());b=json.loads(B.read_text());report=json.loads(P.read_text())
byq={q['question_id']:q for q in b['questions']};bys={s['source_id']:s for s in m['sources']}
polygons={
 'low':[[(225,444),(280,389),(291,400),(237,455)],[(739,379),(803,437),(791,450),(728,393)]],
 'high':[[(193,437),(246,381),(260,394),(207,450)],[(700,358),(775,419),(763,433),(688,374)]]}
r5={'q-a7bcc9d78974450b3134':'low','q-ad64185b2ff11188e740':'low',
    'q-14b655ba17ab05463b8f':'high','q-755ce2a85a3b42196812':'high'}
ids=list(r5)+['q-0fa4b85115e703a3a2dd','q-030275d9ade752ee5929']
for qid in ids:
 q=byq[qid];s=bys[q['source_id']];v=next(x for x in s['variants'] if x['variant_id']==q['variant_id'])
 recipe=dict(v['transform']);boxes=list(recipe['masks']);fills=list(recipe['fills'])
 if qid in r5:
  # The original rectangular vessel-name masks crossed vessel outlines. Replace them
  # with rotated text-only polygons, preserving caliber arrows and vascular borders.
  boxes=boxes[:1]+boxes[3:];fills=fills[:1]+fills[3:]
  recipe['polygons']=polygons[r5[qid]]
  recipe['polygon_fills']=[[255,255,255],[255,255,255]]
  recipe['method']='Opaque outcome-text rectangles and rotated vessel-name text polygons; all caliber arrows and vessel borders preserved'
 else:
  # Prevent red/pink sample pixels from creating misleading high-contrast blocks.
  if qid=='q-0fa4b85115e703a3a2dd':
   fills[3]={'sample':[850,750],'rgb':None}
  else:
   fills[4]={'sample':[860,355],'rgb':None}
   fills[-1]={'sample':[850,750],'rgb':None}
  recipe['method']='Opaque answer-text masks sampled from local background; all pathway arrows and cell boundaries preserved'
 recipe['masks']=boxes;recipe['fills']=fills
 recipe['normalized_masks']=[[z[0]/s['width'],z[1]/s['height'],z[2]/s['width'],z[3]/s['height']] for z in boxes]
 source=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')/s['relative_path']
 assert hashlib.sha256(source.read_bytes()).hexdigest()==s['sha256']
 with Image.open(source) as base:
  original=base.convert('RGB');im=original.copy();d=ImageDraw.Draw(im)
  for box,fill in zip(boxes,fills):
   if fill['rgb'] is None:fill['rgb']=list(original.getpixel(tuple(fill['sample'])))
   d.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=tuple(fill['rgb']))
  for poly,fill in zip(recipe.get('polygons',[]),recipe.get('polygon_fills',[])):
   d.polygon([tuple(p) for p in poly],fill=tuple(fill))
 digest=hashlib.sha256((s['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
 oldid=q['variant_id'];newid='var-'+digest;zoom=f'assets/{digest}.png';display=f'assets/{digest}.webp'
 im.save(R/zoom);im.save(R/display,format='WEBP',quality=92,method=6)
 v.update(variant_id=newid,zoom_image=zoom,image=display,transform=recipe,
          visual_review='PENDING full-size corrected-derivative review')
 q.update(variant_id=newid,zoom_image=zoom,image=display)
 if s.get('variant_id')==oldid:s.update(variant_id=newid,zoom_image=zoom,image=display,transform=recipe)
 for c in report['changed_derivatives']:
  if c['question_id']==qid:
   c.update(new_variant_id=newid,added_masks=boxes[1:] if qid in r5 else boxes,
            note='Second-pass QA replaced rough vessel text rectangles or corrected footer/background fill.')
print('Refined',len(ids),'derivatives')
B.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n');M.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');P.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
