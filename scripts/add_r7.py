"""Append R7 manual captures after explicit 2026-10-04 quiz-prompt approval.

Fail-closed baseline. Activation requires separate full-size visual review.
"""
from __future__ import annotations
import hashlib,json,shutil
from datetime import datetime
from pathlib import Path
from PIL import Image,ImageDraw
APP=Path(__file__).resolve().parents[1]
MANUAL=Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual/R7')
VM=Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production/R7 - Countercurrent Mechanism, Distal Tubule & Collecting Duct (Physiology)/lecture-manifest.json')
LECTURES=Path('/Users/chriselwell/Desktop/Renal/Lectures')
mp=APP/'data/source-manifest.json';bp=APP/'data/question-bank.json';cp=APP/'data/coverage.json'
m=json.loads(mp.read_text());b=json.loads(bp.read_text());c=json.loads(cp.read_text());vm=json.loads(VM.read_text())
assert len(m['sources'])==29 and len(b['questions'])==52
assert all(s['lecture_id']!='R7' for s in m['sources'])
assert all(q['collection']!='R7' for q in b['questions'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in vm['sources']:
 p=LECTURES/Path(x['path']).name
 assert p.is_file() and sha(p)==x['sha256'] and p.stat().st_size==x['size'],p
rls=next(x for x in vm['sources'] if x['kind']=='rls')
notes=next(x for x in vm['sources'] if x['kind']=='professor-notes')
tran=next(x for x in vm['sources'] if x['kind']=='transcript' and 'Part 3' in x['path'])
capture={Path(x['path']).name:x['sha256'] for x in vm['picture_quiz_extraction']['capture_inventory']}
files=[
 ('Collecting Duct Lumen EM.png','TEM','Collecting-duct cell contrast',15,'USABLE','Red arrows target darker intercalated cells and green arrows target paler principal cells; both are visible at native size.'),
 ('Collecting Duct Lumen Histo.png','Histology','Collecting-duct H&E teaching field',15,'REFERENCE_ONLY','Small soft H&E field has CD answer text in lumen and blue blood annotation over tissue; after masking, independent duct recognition is not strong enough.'),
 ('Collecting Duct Principal and Intercalated Cells EM.png','SEM','Principal versus intercalated cells',15,'USABLE','Red-starred protruding cells and darker unstarred central cells are distinct; exterior color key can be masked without covering tissue.'),
 ('Distal Tubule Lumen EM.png','TEM','Distal-tubule mitochondria and apical surface',13,'USABLE','Numerous elongated cytoplasmic mitochondria and sparse apical projections are visible; the lumen label does not reveal these targets.'),
 ('Distal Tubule Lumen Histo.png','Histology','Distal-tubule H&E teaching field',13,'REFERENCE_ONLY','Soft low-resolution H&E crop is directly labeled inside its lumen and cuts off part of the lower tubular wall; unlabelled segment identification would be weak.'),
]
assert set(capture)=={x[0] for x in files}
def dhash(im):
 x=im.convert('L').resize((9,8));bits=''.join('1' if x.getpixel((j,i))>x.getpixel((j+1,i)) else '0' for i in range(8) for j in range(8));return f'{int(bits,2):016x}'
sources={};newq=[]
for name,modality,concept,page,status,reason in files:
 p=MANUAL/name;assert p.is_file() and sha(p)==capture[name]
 digest=sha(p)
 with Image.open(p) as im:im.load();w,h=im.size;mode,fmt,ph=im.mode,im.format,dhash(im)
 asset=f'assets/{digest[:24]}.png'
 if not (APP/asset).exists():shutil.copyfile(p,APP/asset)
 assert sha(APP/asset)==digest
 s={'relative_path':'R7/'+name,'extension':'.png','bytes':p.stat().st_size,'sha256':digest,'kind':'raster','width':w,'height':h,'format':fmt,'mode':mode,'decode_status':'ok','asset_id':'asset-'+digest[:16],'source_id':'src-'+digest[:16],'source_group_id':'group-'+digest[:16],'perceptual_hash':ph,'perceptual_hash_method':'64-bit dHash','source_origin':'lecture','acquisition':'user manual RLS capture','lecture_id':'R7','system':'Renal','status':status,'modality':modality,'tested_concept':concept,'review_reason':reason,'ground_truth_basis':f'Visible user RLS capture matched to verified R7 RLS p. {page}, professor Notes, and transcript Part 3','source_citation':{'document':Path(rls['path']).name,'page':page,'sha256':rls['sha256']},'rights_status':'User-supplied course material, local educational use only; no redistribution authorization established','original_asset':asset,'variants':[],'variant_review_complete':False,'question_type_matrix':[{'type':'Distinct visual targets','supported':'YES' if status=='USABLE' else 'NO','reason':reason}]}
 m['sources'].append(s);sources[name]=s

def variant(s,target,masks=None,fill='#f4edcf',crop=None):
 masks=masks or []
 recipe={'masks':masks,'input_dimensions':[s['width'],s['height']],'coordinate_basis':'immutable_original_pixels','method':'Lossless exterior answer-key crop; no tissue changes' if crop else 'Opaque exterior-answer-key mask only; no tissue changes' if masks else 'No pixel changes','fill':fill,'target':target,'normalized_masks':[[v/(s['width'] if i%2==0 else s['height']) for i,v in enumerate(box)] for box in masks]}
 if crop:recipe['crop']=crop;recipe['normalized_crop']=[v/(s['width'] if i%2==0 else s['height']) for i,v in enumerate(crop)]
 key=hashlib.sha256((s['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
 zoom,display=f'assets/{key}.png',f'assets/{key}.webp'
 with Image.open(MANUAL/s['relative_path'][3:]) as original:
  im=original.convert('RGB')
  if crop:im=im.crop(crop)
  d=ImageDraw.Draw(im)
  for x0,y0,x1,y1 in masks:d.rectangle((x0,y0,x1-1,y1-1),fill=fill)
  im.save(APP/zoom);im.save(APP/display,format='WEBP',quality=92,method=6)
 v={'variant_id':'var-'+key,'image':display,'zoom_image':zoom,'transform':recipe,'visual_review':'PENDING full-size review'};s['variants'].append(v)
 if len(s['variants'])==1:s.update(variant_id=v['variant_id'],image=display,zoom_image=zoom,transform=recipe)
 return v

def question(s,v,concept,stem,options,key,rationales,clues,qtype,note_page):
 assert len(options)==len(rationales)==4 and len(set(options))==4
 ident=hashlib.sha256((s['source_id']+concept+v['variant_id']).encode()).hexdigest()[:20]
 citations=[s['source_citation'],{'document':Path(notes['path']).name,'page':note_page,'sha256':notes['sha256']},{'document':Path(tran['path']).name,'page':4 if s['source_citation']['page']==15 else 2,'sha256':tran['sha256']}]
 newq.append({'question_id':'q-'+ident,'asset_id':s['asset_id'],'source_group_id':s['source_group_id'],'source_id':s['source_id'],'variant_id':v['variant_id'],'question_type':qtype,'tested_concept':concept,'stem':stem,'visual_target':stem,'joint_composite':False,'options':options,'correct_index':key,'choice_rationales':rationales,'explanation':rationales[key],'visual_clues':clues,'ground_truth_confidence':'high','ground_truth_basis':s['ground_truth_basis'],'citations':citations,'image':v['image'],'zoom_image':v['zoom_image'],'original_image':s['original_asset'],'original_filename':s['relative_path'],'category':s['modality'],'collection':'R7','source_origin':'lecture','status':'USABLE','case_context':'','accepted_synonyms':[]})

s=sources[files[0][0]];v=variant(s,'Red-arrow dark and green-arrow pale cells in complete collecting-duct TEM')
question(s,v,'R7 red-arrow intercalated cells in CD TEM','In this complete collecting-duct EM cross-section, which cells do the red arrows indicate?',
 ['Intercalated cells','Principal cells','Podocytes','Capillary endothelial cells'],0,
 ['The red arrows point to the darker, more granular cells lining the same collecting-duct lumen; the RLS identifies these as intercalated cells.','The principal cells are the paler cells identified by the separate green arrows, not the dark red-arrow targets.','Podocytes belong to a glomerular capillary tuft, which is absent from this tubular cross-section.','Endothelium would line a blood vessel outside the duct rather than the central CD lumen.'],['Two red-arrow targets have darker granular cytoplasm','Green arrows mark adjacent paler cells around the same lumen'],'Cell/Tissue',10)
question(s,v,'R7 green-arrow principal cells in CD TEM','In this complete collecting-duct EM cross-section, which cells do the green arrows indicate?',
 ['Principal cells','Intercalated cells','Macula-densa cells','Podocytes'],0,
 ['The green arrows meet the paler cells lining the collecting-duct lumen; the RLS contrasts them with the darker red-arrow intercalated cells.','Intercalated cells are the darker, granular cells indicated by the red arrows in this same image.','A macula densa is a crowded distal-tubule patch at the vascular pole, not these cells distributed around a CD lumen.','Podocytes wrap glomerular capillaries and do not form this tubular lining.'],['Green-arrow targets have paler cytoplasm','Darker red-arrow cells form the contrasting population'],'Cell/Tissue',10)

s=sources[files[2][0]];v=variant(s,'Red-starred versus unstarred collecting-duct cells',crop=[0,138,320,584])
question(s,v,'R7 red-starred intercalated cells in CD SEM','In this complete collecting-duct surface EM, what cell class is marked by the red stars?',
 ['Intercalated cells','Principal cells','Podocytes','Distal convoluted-tubule cells'],0,
 ['The stars mark the lighter, bulging cells interspersed among the broader dark luminal cells; the source legend identifies the starred cells as intercalated.','Principal cells are the broader dark unstarred cells between the starred cells in this field.','Podocytes surround glomerular capillaries, not the luminal surface of this collecting duct.','The starred cells are within the displayed collecting-duct epithelium rather than a separate distal-tubule profile.'],['Three red stars over lighter protruding cells','Darker unstarred cells form a separate surface population'],'Cell/Tissue',10)
question(s,v,'R7 unstarred principal cells in CD SEM','In this complete collecting-duct surface EM, which cell class forms the broad darker unstarred luminal surface between the red-starred cells?',
 ['Principal cells','Intercalated cells','Macula-densa cells','Glomerular endothelial cells'],0,
 ['The broad darker unstarred cells form the central luminal surface; the source contrasts these principal cells with the red-starred intercalated cells.','Intercalated cells are the lighter protruding cells specifically marked by red stars, not the darker unstarred surface.','Macula-densa cells form a compact distal-tubule patch adjacent to the renal corpuscle, not this longitudinal duct lining.','Glomerular endothelium would line capillary blood spaces, none of which are shown in this duct surface view.'],['Broad dark cells remain unstarred','Smaller lighter starred cells interrupt the dark surface'],'Cell/Tissue',10)

s=sources[files[3][0]];v=variant(s,'Cytoplasmic mitochondria and sparse apical surface in complete distal-tubule TEM')
question(s,v,'R7 distal-tubule abundant mitochondria in EM','In this complete distal-tubule EM cross-section, which cytoplasmic structures are repeatedly visible as dark elongated profiles around the labeled lumen?',
 ['Mitochondria','Nuclei','Brush-border microvilli','Capillary lumina'],0,
 ['Numerous narrow dark profiles occupy the epithelial cytoplasm around the lumen, matching the mitochondria emphasized in the R7 distal-tubule teaching.','Nuclei are the fewer large rounded profiles, not the many narrow dark structures throughout the cytoplasm.','Microvilli would project from the apical cell edge into the lumen rather than lie deep within the cells.','Capillary lumina would be open spaces outside the epithelium, not dark intracellular profiles.'],['Many elongated dark cytoplasmic profiles','Larger rounded nuclei and an open central lumen are separate structures'],'Cell/Tissue',9)
question(s,v,'R7 distal-tubule sparse apical border in EM','Compared with the dense proximal brush border, what is visible along the apical edge of this complete distal-tubule EM cross-section?',
 ['A relatively sparse, short apical fringe','A dense tall microvillus brush border','Podocyte foot processes around a capillary','A sheet of endothelial fenestrae'],0,
 ['The luminal cell edge has only short, sparse projections rather than the thick, continuous proximal brush border described in the lecture.','A dense tall brush border would produce a prominent continuous fringe filling more of the lumen; that is not present here.','Foot processes flank glomerular capillaries, whereas this image shows an epithelial ring around a tubule lumen.','Endothelial fenestrae belong to capillary lining and are not the apical surface bordering this tubular lumen.'],['Central lumen has a thin irregular edge','No dense continuous microvillar band surrounds the lumen'],'Structure',9)

assert len(newq)==6 and len({q['question_id'] for q in newq})==6
m['source_count_physical']=len(m['sources']);m['approval']='User approved complete R7 addition prompt on 2026-10-04; multi-target policy applies to all existing and future captures.';m['stage']='R7 candidate variants generated; full-size QA pending';m['generated_at']=datetime.now().astimezone().isoformat(timespec='seconds')
b['bank_version']='2026-10-04-renal-r7-1';b['questions'].extend(newq)
c['lectures']['R7']={'status':'Partial coverage','tested_summary':['Red-arrow intercalated and green-arrow principal cells in collecting-duct TEM','Red-starred intercalated and dark unstarred principal cells in collecting-duct surface EM','Distal-tubule mitochondrial abundance and sparse apical fringe in EM'],'gaps':['The two small H&E captures remain teaching references because their answer labels and softness make unlabelled segment identification unreliable.','Five captures do not cover the R7 countercurrent gradient, urea recycling, vasa recta exchange, transport schematics, or diuretic site maps.'],'next_capture':'For broader R7 visual coverage, supply a complete readable manual capture of the countercurrent/urea diagram or transporter map with axes, labels, and context retained.','basis':'Five manual R7 captures matched to RLS pp. 13 and 15; three candidate scored EM files, two reference-only H&E files. This is not lecture-wide visual coverage.'}
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');bp.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n');cp.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
(APP/'data/review-queue.json').write_text(json.dumps({'schema_version':2,'items':[x for x in m['sources'] if x['status']!='USABLE']},ensure_ascii=False,indent=2)+'\n')
print('R7: five captures, three candidate scored EMs, two H&E references, six candidate questions pending visual QA')
