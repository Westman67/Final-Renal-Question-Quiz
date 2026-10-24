"""Reproducible 2026-10-06 learner-flag remediation from immutable manual captures."""
from __future__ import annotations
import hashlib,json,datetime
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')
MP=ROOT/'data/source-manifest.json';BP=ROOT/'data/question-bank.json'
manifest=json.loads(MP.read_text());bank=json.loads(BP.read_text())
by_q={q['question_id']:q for q in bank['questions']}
by_s={s['source_id']:s for s in manifest['sources']}
now=datetime.datetime.now().astimezone().isoformat(timespec='seconds')
# Every rectangle is in the immutable original's pixel coordinates. Background samples are
# also from the original. No arrows, tissue, graph data, or carrier outlines are covered.
extra={
 'q-f298e13788387e5d6dbc':[
  ([24,386,168,489],[18,372]),([701,385,851,490],[699,369])],
 'q-6f68cbd0e71eba1f4df3':[
  ([315,490,353,520],[353,515])],
 'q-ba53855a7abca217a1f0':[
  ([79,245,169,296],[74,242])],
 'q-d697c9ec879eabf6ea04':[
  ([131,545,267,583],[125,542]),([500,546,635,583],[500,539])],
 'q-796c0e27111715489331':[
  ([628,290,808,335],[626,286])],
 'q-39f7badb81a504bd3afa':[
  ([628,181,828,225],[625,177])],
 'q-0fa4b85115e703a3a2dd':[
  ([300,78,685,133],[300,73]),([70,352,158,409],[56,339]),
  ([359,350,443,407],[352,341]),([831,783,1006,836],[825,778])],
 'q-030275d9ade752ee5929':[
  ([300,78,685,133],[300,73]),([32,520,151,582],[29,512]),
  ([327,520,456,584],[315,517]),([502,410,650,464],[489,405]),
  ([780,368,932,427],[770,361]),([960,368,1231,427],[955,360]),
  ([746,564,971,600],[730,558]),([831,783,1333,838],[825,775])],
}
# Mask both pathway labels in both variants so the unmasked sibling word does not give away
# the answer by binary elimination. Preserve the two route arrows and cell boundaries.
# Reuse old masks as-is, adding only the other text label.
r5low=[([226,384,291,446],[301,422]),([738,381,811,449],[814,442]),
       ([154,105,235,148],[245,125]),([807,162,960,205],[975,182])]
r5high=[([198,380,264,446],[279,414]),([699,362,777,431],[825,423]),
        ([124,117,207,161],[224,143]),([811,133,965,178],[982,154])]
for qid in ['q-a7bcc9d78974450b3134','q-ad64185b2ff11188e740']:
 extra[qid]=r5low
for qid in ['q-14b655ba17ab05463b8f','q-755ce2a85a3b42196812']:
 extra[qid]=r5high

# Question-only rewrite where the unmodified graphic itself is the evidence.
water=by_q['q-80a455573f1703b11609']
water.update(question_type='Route Identification',
 tested_concept='R6 proximal tubule paracellular water route',
 stem='The lower dotted H₂O path bypasses the proximal-tubule cell. Which epithelial route does it take?',
 visual_target='Identify the lower water path relative to the cell boundaries and upper aquaporin route.',
 options=['Paracellular movement between neighboring cells','Transcellular movement through aquaporin 1','Active transport by Na⁺/K⁺-ATPase','Movement from blood into the tubular lumen'],
 correct_index=0,
 choice_rationales=[
  'The lower dotted path passes through the gap between adjacent cells from lumen toward blood.',
  'The upper water path crosses the cell through aquaporin 1; the lower one bypasses it.',
  'The Na⁺/K⁺ pump moves ions at the basolateral membrane, not the lower water path.',
  'The lower dotted arrow runs from the lumen on the left toward blood on the right.'
 ],
 explanation='The lower dotted water route passes between adjacent proximal-tubule cells, so it is paracellular.',
 visual_clues=['Lower dotted H₂O arrow crosses the intercellular gap','Upper arrows instead pass through two aquaporin 1 channels'])

drug=by_q['q-f298e13788387e5d6dbc']
drug.update(stem='What transport process do the lower blue carriers and leftward arrows depict in this proximal-tubule cell?',
 visual_target='Trace the lower carrier pathway from the blood side to the lumen side.',
 explanation='The lower blue-carrier arrows cross from blood at right through the cell to lumen at left, depicting tubular secretion.',
 choice_rationales=[
  'The lower arrows traverse the cell from the blood side into the tubular lumen, which is secretion.',
  'Reabsorption follows the upper, opposite-direction pathway from lumen toward blood.',
  'This image depicts a proximal-tubule cell, not a glomerular capillary and Bowman’s space.',
  'The lower path crosses both cell faces and ends in the lumen rather than stopping in the cell.'
 ],visual_clues=['Blood is on the right and lumen on the left','Lower carrier arrows point toward the lumen'])
na=by_q['q-6f68cbd0e71eba1f4df3']
na.update(question_type='Ion Identification',tested_concept='R6 proximal tubule apical hydrogen secretion via sodium exchange',
 stem='In the green apical exchanger, Na⁺ enters the cell. Which ion is hidden on the oppositely directed lumenward arrow?',
 visual_target='Identify the counter-transported ion on the green apical carrier.',
 options=['H⁺','K⁺','Cl⁻','HCO₃⁻'],correct_index=0,
 choice_rationales=[
  'This apical Na⁺/H⁺ exchanger secretes H⁺ toward the lumen while Na⁺ enters the cell.',
  'K⁺ appears at the basolateral pump and leak paths, not on this apical counter-transport arrow.',
  'The green apical exchanger does not show a chloride counter-transport path.',
  'Bicarbonate is not the ion moving lumenward through this green Na⁺ exchanger.'
 ],explanation='Na⁺ enters through the green apical exchanger while H⁺ is secreted in the opposite direction.',
 visual_clues=['Na⁺ enters at the green apical carrier','The hidden ion moves in the opposite direction toward the lumen'])
nk=by_q['q-ba53855a7abca217a1f0']
nk.update(question_type='Ion Stoichiometry',tested_concept='R7 TAL NKCC2 two-chloride stoichiometry',
 stem='At the green apical cotransporter, what ion and count belong on the masked middle inward arrow?',
 visual_target='Identify the middle inward stream between the visible Na⁺ and K⁺ streams.',
 options=['2 Cl⁻','1 Cl⁻','2 K⁺','1 Ca²⁺'],correct_index=0,
 choice_rationales=[
  'The TAL Na⁺/K⁺/2Cl⁻ cotransporter carries two chloride ions in the middle stream.',
  'The visible Na⁺ and K⁺ streams each carry one ion; chloride is the two-ion component.',
  'K⁺ is already labeled on the lower inward arrow, not the masked middle arrow.',
  'Ca²⁺ is shown on the paracellular route, not through this green apical carrier.'
 ],explanation='The masked middle stream is 2 Cl⁻ in the TAL Na⁺/K⁺/2Cl⁻ cotransporter.',
 visual_clues=['The middle arrow enters the same carrier as Na⁺ and K⁺','Ca²⁺ is separately labeled on the paracellular route'])

# R5 follow-up: test downstream hemodynamic predictions, not the printed starburst word.
# The colored arrows remain because they are the evidence for constriction versus dilation.
pairs={
 'q-a7bcc9d78974450b3134':('blue','low','RPF decreases; Pgc increases','The blue inward arrows indicate efferent constriction, which lowers RPF and raises Pgc.'),
 'q-ad64185b2ff11188e740':('red','low','RPF increases; Pgc increases','The red outward arrows indicate afferent dilation, which raises both RPF and Pgc.'),
 'q-14b655ba17ab05463b8f':('blue','high','RPF increases; Pgc decreases','The blue outward arrows indicate efferent dilation, which raises RPF and lowers Pgc.'),
 'q-755ce2a85a3b42196812':('red','high','RPF decreases; Pgc decreases','The red inward arrows indicate afferent constriction, which lowers both RPF and Pgc.'),
}
opts=['RPF decreases; Pgc increases','RPF increases; Pgc increases','RPF increases; Pgc decreases','RPF decreases; Pgc decreases']
for qid,(color,pressure,key,rationale) in pairs.items():
 q=by_q[qid]
 q.update(question_type='Hemodynamic Prediction',tested_concept=q['tested_concept']+' hemodynamic consequence',
  stem=f'In this {pressure}-NaCl macula-densa diagram, what paired RPF and Pgc changes follow the {color}-arrow vessel response considered alone?',
  visual_target=f'Use the {color} vessel arrows and glomerular anatomy to predict RPF and Pgc, with outcome boxes hidden.',
  options=opts[:],correct_index=opts.index(key),
  choice_rationales=[rationale if o==key else f'This pair gives the wrong {"RPF" if o.split(";")[0]!=key.split(";")[0] else "Pgc"} direction for the {color}-arrow vessel response.' for o in opts],
  explanation=rationale,
  visual_clues=[f'{color.capitalize()} arrows show the vessel caliber response',f'The {color}-arrow vessel is identified by its position at the vascular pole'])
 r4={'document':'R4 Renal Plasma Flow (Physiology) RLS.pdf','page':16,'sha256':'573c8a7ec7eaadd5388975da4f76c83eae078c3da18ba0884e1ce94fb9f476f2'}
 if r4 not in q['citations']:q['citations'].append(r4)

hco3=by_q['q-d697c9ec879eabf6ea04']
hco3.update(stem='After luminal HCO₃⁻ is converted near carbonic anhydrase, which products follow the dotted apical path into the proximal cell?',
 visual_target='Identify the two masked small molecules on either side of the dotted apical path.',
 explanation='Luminal H₂CO₃ is converted to H₂O and CO₂, which follow the dotted path into the cell.',
 visual_clues=['Carbonic anhydrase acts beside luminal H₂CO₃','The dotted path crosses the apical membrane'])

for qid in ['q-796c0e27111715489331','q-39f7badb81a504bd3afa']:
 q=by_q[qid]
 q['visual_target']='Compare the upper through-cell arrow with the lower between-cell arrow; both route names are hidden.'
 q['visual_clues']=['Upper red arrow crosses a tubular cell','Lower orange arrow passes between tubular cells']

ammonia=by_q['q-0fa4b85115e703a3a2dd']
ammonia.update(stem='Which uncharged glutamine-derived species follows the upper dotted path from the proximal cell into the lumen?',
 visual_target='Distinguish the upper dotted diffusion path from the lower carrier-associated ammonium path.',
 explanation='The upper dotted route depicts NH₃ diffusion into the lumen, separate from lower NH₄⁺ secretion.',
 visual_clues=['Upper dotted path exits without the green apical carrier','Lower path crosses the green apical carrier'])
paired=by_q['q-030275d9ade752ee5929']
paired.update(stem='Following the two glutamine-derived branches, what paired outputs travel lumenward and bloodward?',
 visual_target='Trace the lower lumenward branch and the α-ketoglutarate-to-blood branch with their product labels hidden.',
 explanation='Glutamine yields two NH₄⁺ toward the lumen and α-ketoglutarate-derived two new HCO₃⁻ toward blood.',
 visual_clues=['The left branch heads toward the lumen via the green apical carrier','The α-ketoglutarate branch points to the blood side'])

changes=[]
for qid,added in extra.items():
 q=by_q[qid];s=by_s[q['source_id']]; old=next(v for v in s['variants'] if v['variant_id']==q['variant_id'])
 source=SOURCE/s['relative_path']
 assert source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==s['sha256'],source
 with Image.open(source) as original:
  original=original.convert('RGB')
  assert original.size==(s['width'],s['height'])
  image=original.copy();draw=ImageDraw.Draw(image)
  oldmasks=old['transform'].get('masks',[])
  oldfills=old['transform'].get('fills',[])
  boxes=[];fills=[]
  for n,box in enumerate(oldmasks):
   spec=oldfills[n] if n<len(oldfills) else {'rgb':[255,255,255]}
   color=spec['rgb'];draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=tuple(color))
   boxes.append(box);fills.append(spec)
  for box,sample in added:
   assert 0<=box[0]<box[2]<=s['width'] and 0<=box[1]<box[3]<=s['height']
   color=original.getpixel(tuple(sample))
   draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=color)
   boxes.append(box);fills.append({'sample':sample,'rgb':list(color)})
  recipe={'masks':boxes,'input_dimensions':[s['width'],s['height']],
   'coordinate_basis':'immutable_original_pixels',
   'method':'Opaque answer-text masks only; arrows, carrier contours, cell boundaries, and tissue preserved',
   'fills':fills,'target':q['tested_concept'],
   'normalized_masks':[[b[0]/s['width'],b[1]/s['height'],b[2]/s['width'],b[3]/s['height']] for b in boxes]}
  digest=hashlib.sha256((s['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
  zoom=f'assets/{digest}.png';display=f'assets/{digest}.webp'
  image.save(ROOT/zoom)
  image.save(ROOT/display,format='WEBP',quality=92,method=6)
 oldid=q['variant_id'];newid='var-'+digest
 newv=dict(old,variant_id=newid,image=display,zoom_image=zoom,transform=recipe,
           visual_review='PENDING full-size learner-flag remediation review')
 s['variants']=[newv if v['variant_id']==oldid else v for v in s['variants']]
 q.update(variant_id=newid,image=display,zoom_image=zoom)
 if s.get('variant_id')==oldid:s.update(variant_id=newid,image=display,zoom_image=zoom,transform=recipe)
 s['variant_review_complete']=False
 changes.append({'question_id':qid,'source_id':s['source_id'],'old_variant_id':oldid,'new_variant_id':newid,
                 'action':'mask_and_rewrite' if qid in pairs or qid in ['q-f298e13788387e5d6dbc','q-6f68cbd0e71eba1f4df3','q-ba53855a7abca217a1f0'] else 'mask',
                 'added_masks':added,'reason':'Remove direct answer text or a sibling-label leak while retaining diagnostic arrows and topology.'})

bank['bank_version']='renal-2026-10-06-r1'
manifest['stage']='Learner-flag remediation generated; native-size derivative QA pending'
manifest['generated_at']=now
BP.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
MP.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
report={'schema_version':1,'batch_id':'renal-flags-2026-10-06-r1','created_at':now,
 'source':'Five open learner flags recovered read-only from the quiz browser progress store on 2026-10-06; user approved remediation.',
 'flagged_question_ids':['q-80a455573f1703b11609','q-f298e13788387e5d6dbc','q-6f68cbd0e71eba1f4df3','q-a7bcc9d78974450b3134','q-ba53855a7abca217a1f0'],
 'decisions':[
  {'question_id':'q-80a455573f1703b11609','action':'retain','reason':'Rewrote an overly broad two-route prompt into an image-dependent lower paracellular route identification; image itself is unchanged.'},
  {'question_id':'q-f298e13788387e5d6dbc','action':'mask','reason':'Removed both lower substrate labels as well as existing secretion text; arrows and compartment labels remain.'},
  {'question_id':'q-6f68cbd0e71eba1f4df3','action':'mask','reason':'Changed to ask for the hidden counter-transported ion and masked the actual H⁺ label; Na⁺ input and arrows remain.'},
  {'question_id':'q-a7bcc9d78974450b3134','action':'mask','reason':'Changed from reading the constrict starburst to predicting paired RPF/Pgc effects; masked vessel names and printed outcomes. Vessel arrows remain necessary evidence.'},
  {'question_id':'q-ba53855a7abca217a1f0','action':'mask','reason':'Changed to ask for the missing middle-stream ion and count; masked the printed 2 Cl⁻ and cotransporter title, retaining the Na⁺ and K⁺ streams.'}
 ],
 'propagated_to':['Other three R5 TGF response questions','R6 HCO₃⁻ apical products','Both R6 transcellular/paracellular route variants','Both R9 glutamine/ammonia pathway questions'],
 'changed_derivatives':changes,
 'question_only_rewrite':['q-80a455573f1703b11609'],
 'qa_status':'PENDING'}
(ROOT/'reports/learner-flag-remediation-2026-10-06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Updated',len(changes),'variants and',1,'question-only rewrite; 5 flags represented; source originals unchanged.')
