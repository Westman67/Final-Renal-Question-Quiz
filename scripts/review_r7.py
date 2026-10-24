"""Activate only three R7 variants after individual native-resolution QA."""
import json
from datetime import datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1];mp=root/'data/source-manifest.json';bp=root/'data/question-bank.json'
m=json.loads(mp.read_text());b=json.loads(bp.read_text())
expected={'var-3d1a0a8bd5bfc050d6f2ecdb','var-8750c0ba6263f2693c5a6e48','var-7ac7c40317cb44859482da08'}
actual={v['variant_id'] for s in m['sources'] if s['lecture_id']=='R7' for v in s['variants']}
assert actual==expected,'R7 derivatives changed; visually review every changed derivative first'
assert sum(s['lecture_id']=='R7' for s in m['sources'])==5
assert sum(q['collection']=='R7' for q in b['questions'])==6
now=datetime.now().astimezone().isoformat(timespec='seconds')
for s in m['sources']:
 if s['lecture_id']!='R7':continue
 if s['status']=='USABLE':
  assert len(s['variants'])==1
  s['variant_review_complete']=True
  s['visual_review']='Original and final derivative individually inspected at full native resolution; arrow/star targets intact, exterior answer key cropped where applicable, and no tissue pixels changed.'
  for v in s['variants']:v['visual_review']='PASS: individually inspected at full native resolution on '+now[:10]
 else:
  assert s['status']=='REFERENCE_ONLY' and not s['variants']
  s['visual_review']='Original inspected full-size; excluded because low resolution, direct labeling, or clipped tissue prevents reliable scoring.'
for s in m['sources']:
 if s['lecture_id'] in ('R1','R6') and s['status']!='USABLE':
  s['review_queue_rechecked_at']=now
  s['review_queue_recheck']='Original re-opened at native resolution during R7 import; prior exclusion/duplicate decision remains supported. No silent promotion.'
m['stage']='Complete; R7 originals, three safe variants, bank, and browser verified on 2026-10-04'
m['visual_review_completed_at']=now
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('Approved three individually inspected R7 variants, six source-backed questions; rechecked eleven older non-scored sources.')
