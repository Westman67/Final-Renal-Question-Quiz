"""Append approved R9 manual-picture questions using the R9 course RLS only."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil,datetime
ROOT=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal Quiz App')
MANUAL=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')
RLS=Path('/Users/chriselwell/Desktop/Desktop Download/R9 Acid-Base Regulation (Physiology) RLS.pdf')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def Q(code,concept,stem,options,rationales,clues,qtype='Physiologic Interpretation',masks=None):
 assert len(options)==len(rationales)==4 and len(set(options))==4
 return dict(code=code,concept=concept,stem=stem,options=options,rationales=rationales,clues=clues,qtype=qtype,masks=masks or [])
SPECS={
 'R9/Anion Gap.png':dict(page=30,group='anion-balance',questions=[
  Q('unmeasured-band','Anion gap is the unmeasured-anion band in plasma balance',
    'In this equal-height plasma-ion balance, what occupies the masked blue band above the measured anions?',
    ['Unmeasured anions','Measured chloride and bicarbonate','Measured sodium cations','Unbound hydrogen ions'],
    ['The blue band fills the difference between the measured red anions and the total cation height; the RLS calls that remainder unmeasured anions.',
     'Chloride and bicarbonate belong to the lower red measured-anion compartment, not the masked blue remainder.',
     'Sodium contributes to the green cation side of the balance rather than the blue anion side.',
     'Hydrogen ions are cations, whereas the masked band is on the anion side of this diagram.'],
    ['Equal total heights represent electroneutrality','The masked band is on the anion side above the red compartment'],
    masks=[([626,44,943,141],[605,86])])]),
 'R9/Metabolic acidosis caused by increased fixed acids Anion Gap.png':dict(page=32,group='anion-balance',questions=[
  Q('fixed-acid-gap','Fixed-acid accumulation enlarges the anion gap',
    'As the white fixed-acid arrow rises above the blue unmeasured-anion pool, which change in the yellow anion-gap span is depicted?',
    ['It increases','It decreases','It stays unchanged','It reverses below zero'],
    ['The incoming fixed-acid anions enlarge the blue unmeasured pool, and the yellow double arrow spans that enlarged region.',
     'The blue region expands upward rather than shrinking, so the yellow gap span does not decrease.',
     'The added fixed-acid arrow and taller blue span depict a change, not an unchanged gap.',
     'The yellow span remains positive above the measured red anions; no reversal is shown.'],
    ['White arrow points upward over fixed acids','Yellow gap span covers the enlarged blue region'],
    'Direction of Change')]),
 'R9/Where NH3 Comes from.png':dict(page=22,questions=[
  Q('ammonia-route','Permeable ammonia exits the proximal cell into lumen',
    'Which glutamine-derived form follows the upper dotted route from the proximal-tubule cell into the lumen?',
    ['NH₃','NH₄⁺','HCO₃⁻','α-ketoglutarate'],
    ['The upper red dotted arrow carries NH₃ leftward across the apical side into the lumen.',
     'NH₄⁺ uses the separate lower green-carrier pathway toward the lumen.',
     'HCO₃⁻ is shown moving toward blood on the right, not along the upper apical route.',
     'α-ketoglutarate remains on the intracellular branch leading to new bicarbonate.'],
    ['Upper red dotted arrow runs from cell to lumen','Lower green carrier handles a different ammonium route'],
    'Pathway'),
  Q('glutamine-products','Glutamine-derived ammonium and new bicarbonate outputs',
    'Following both branches from glutamine in this proximal-cell diagram, which paired outputs and destinations are shown?',
    ['Two NH₄⁺ toward lumen and two new HCO₃⁻ toward blood','Two HCO₃⁻ toward lumen and two NH₄⁺ toward blood','Only NH₃ toward blood with no bicarbonate generation','Only α-ketoglutarate into lumen with no ammonium'],
    ['The left branch labels 2 NH₄⁺ and points into the lumen, while the right branch labels 2 new HCO₃⁻ toward blood.',
     'The directions are reversed; bicarbonate goes bloodward and ammonium goes lumenward in this figure.',
     'NH₃ moves toward lumen, and the right branch explicitly shows new bicarbonate entering blood.',
     'α-ketoglutarate feeds bicarbonate production, while the other branch visibly produces ammonium.'],
    ['Glutamine splits into left ammonium and right α-ketoglutarate branches','The right-hand output is labeled new bicarbonate'],
    'Integrated Mechanism')])}
REF={'R9/Metabolic Acidosis Anion Gap Types.png':dict(page=33,reason='Thin text-only three-column summary with no independently identifiable picture target; retained as lecture reference.')}
m_path=ROOT/'data/source-manifest.json';q_path=ROOT/'data/question-bank.json';m=json.loads(m_path.read_text());bank=json.loads(q_path.read_text())
assert len(m['sources'])==58 and len(bank['questions'])==91 and RLS.exists()
rls_hash=sha(RLS);audit=json.loads(Path('/tmp/r9-audit.json').read_text());records={f"R9/{r['relative_path']}":r for r in audit['records']}
assert set(records)==set(SPECS)|set(REF)
assert not {s['relative_path'] for s in m['sources']}&set(records)
group_hashes={k:[records[r]['sha256'] for r,v in SPECS.items() if v.get('group')==k] for k in {'anion-balance'}}
groups={k:'group-'+hashlib.sha256(''.join(sorted(v)).encode()).hexdigest()[:16] for k,v in group_hashes.items()}
newq=[]
for rel in sorted(records):
 a=records[rel];p=MANUAL/rel;assert sha(p)==a['sha256']
 scored=rel in SPECS;spec=SPECS.get(rel) or REF[rel];digest=a['sha256'];w,h=a['width'],a['height']
 orig=f'assets/{digest[:24]}.png';shutil.copyfile(p,ROOT/orig)
 sid='src-'+digest[:16]
 group=groups.get(spec.get('group'),'group-'+digest[:16])
 source=dict(relative_path=rel,extension='.png',bytes=a['bytes'],sha256=digest,kind='raster',width=w,height=h,
  format='PNG',mode=a['mode'],decode_status='ok',asset_id='asset-'+digest[:16],source_id=sid,source_group_id=group,
  source_origin='lecture',acquisition='user manual R9 RLS capture',lecture_id='R9',system='Renal',status='USABLE' if scored else 'REFERENCE_ONLY',
  modality='Diagram',tested_concept='; '.join(x['concept'] for x in spec['questions']) if scored else Path(rel).stem,
  review_reason='Distinct source-backed visual target(s) supported.' if scored else spec['reason'],
  ground_truth_basis=f'Manual capture visually matched to R9 Acid-Base Regulation (Physiology) RLS.pdf p. {spec["page"]}.',
  source_citation=dict(document=RLS.name,page=spec['page'],sha256=rls_hash),
  rights_status='User-supplied course material, local educational use only; redistribution rights not established',
  original_asset=orig,variants=[],variant_review_complete=False,batch_id='2026-10-05-r9-course-grounded',
  question_type_matrix=[dict(type='Distinct visual target',supported='YES' if scored else 'NO',reason=spec.get('reason','Source-backed visual relationship.'))])
 if scored:
  for target in spec['questions']:
   with Image.open(p) as original:
    im=original.convert('RGB');fills=[]
    for box,sample in target['masks']:
     rgb=im.getpixel(tuple(sample));ImageDraw.Draw(im).rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=rgb);fills.append(dict(sample=sample,rgb=rgb))
    recipe=dict(masks=[a for a,b in target['masks']],input_dimensions=[w,h],coordinate_basis='immutable_original_pixels',
      method='Opaque target-text mask in non-diagnostic area' if target['masks'] else 'Unmodified original; complete diagram interpreted',
      fills=fills,target=target['concept'],normalized_masks=[[x0/w,y0/h,x1/w,y1/h] for (x0,y0,x1,y1),_ in target['masks']])
    key=hashlib.sha256((digest+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
    zoom=f'assets/{key}.png';display=f'assets/{key}.webp';im.save(ROOT/zoom);im.save(ROOT/display,format='WEBP',quality=92,method=6)
   variant=dict(variant_id='var-'+key,image=display,zoom_image=zoom,transform=recipe,visual_review='PENDING native-size comparison')
   source['variants'].append(variant)
   if len(source['variants'])==1:source.update(variant_id=variant['variant_id'],image=display,zoom_image=zoom,transform=recipe)
   qid='q-'+hashlib.sha256((sid+target['code']+variant['variant_id']).encode()).hexdigest()[:20]
   newq.append(dict(question_id=qid,asset_id=source['asset_id'],source_group_id=group,source_id=sid,variant_id=variant['variant_id'],
    question_type=target['qtype'],tested_concept=target['concept'],stem=target['stem'],visual_target=target['stem'],joint_composite=False,
    options=target['options'],correct_index=0,choice_rationales=target['rationales'],explanation=target['rationales'][0],
    visual_clues=target['clues'],ground_truth_confidence='high',ground_truth_basis=source['ground_truth_basis'],
    citations=[source['source_citation'],dict(document=rel,page=None,sha256=digest)],image=display,zoom_image=zoom,
    original_image=orig,original_filename=rel,category='Diagram',collection='R9',source_origin='lecture',status='USABLE',
    case_context='',accepted_synonyms=[]))
 m['sources'].append(source)
assert len(newq)==4
m['source_count_physical']=len(m['sources']);m['approval']='User approved R1–R9 lecture-grounded picture-quiz review and R9 import on 2026-10-05.'
m['stage']='R9 staged; full-bank visual and content review pending';m['generated_at']=datetime.datetime.now().astimezone().isoformat(timespec='seconds')
bank['questions'].extend(newq);bank['bank_version']='2026-10-05-renal-r9-lecture-review-1'
m_path.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');q_path.write_text(json.dumps(bank,indent=2,ensure_ascii=False)+'\n')
(ROOT/'data/review-queue.json').write_text(json.dumps({'schema_version':2,'items':[s for s in m['sources'] if s['status']!='USABLE']},indent=2,ensure_ascii=False)+'\n')
print('Added',len(newq),'questions from 3 scored R9 originals; 1 reference')
