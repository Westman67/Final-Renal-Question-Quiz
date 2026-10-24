"""Activate only the four R6 variants individually inspected full-size on 2026-10-04."""
import json
from datetime import datetime
from pathlib import Path

root=Path(__file__).resolve().parents[1]
manifest_path=root/'data/source-manifest.json'
bank_path=root/'data/question-bank.json'
m=json.loads(manifest_path.read_text())
b=json.loads(bank_path.read_text())
expected={
 'var-e873a92de2767556d2edf775',
 'var-988900e0814b5e34613303f0',
 'var-588c41ab92f82ab14332f8d3',
 'var-9923cdb33b1d96b04de6a5a2',
}
actual={v['variant_id'] for s in m['sources'] if s['lecture_id']=='R6' for v in s['variants']}
assert expected==actual, 'R6 variants changed; inspect every changed derivative before approval'
assert sum(q['collection']=='R6' for q in b['questions'])==5
now=datetime.now().astimezone().isoformat(timespec='seconds')
for s in m['sources']:
 if s['lecture_id']!='R6':continue
 if s['status']=='USABLE':
  assert s['variants']
  s['variant_review_complete']=True
  s['visual_review']='Original and every final lossless derivative inspected individually at full native resolution; caption masking stays outside tissue, and EM labels/structures remain visible.'
  for v in s['variants']:
   v['visual_review']='PASS: individually inspected at full native resolution on '+now[:10]
 else:
  assert s['status']=='REFERENCE_ONLY' and not s['variants']
  s['visual_review']='Original inspected full-size; excluded from scoring because the H&E image is soft or answer labels overlap tissue.'
notes=next(x for x in json.loads(Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production/R6 - Proximal Tubule (Physiology)/lecture-manifest.json').read_text())['sources'] if x['kind']=='professor-notes')
for q in b['questions']:
 if q['collection']!='R6':continue
 assert len(q['citations'])==1
 q['citations'].append({'document':Path(notes['path']).name,'page':4,'sha256':notes['sha256']})
m['stage']='Complete; R6 originals, safe variants, bank, and browser verified on 2026-10-04'
m['visual_review_completed_at']=now
manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
bank_path.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
print('Approved four individually inspected R6 variants and five source-backed questions.')
