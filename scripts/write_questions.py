"""Source-grounded authored R1 items. No external content or automatic lecture extraction."""
import json, hashlib
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
manifest=json.loads((APP/'data/source-manifest.json').read_text())
S={s['capture_number']:s for s in manifest['sources']}
Q=[]
def add(n,concept,stem,options,key,rationales,clues,transcript,page,kind='Structure'):
    s=S[n]; assert s['status']=='USABLE'
    ident=hashlib.sha256((s['source_id']+concept).encode()).hexdigest()[:20]
    Q.append({'question_id':'q-'+ident,'asset_id':s['asset_id'],'source_group_id':s['source_group_id'],'source_id':s['source_id'],'variant_id':s['variant_id'],'question_type':kind,'tested_concept':concept,'stem':stem,'visual_target':stem,'joint_composite':False,'options':options,'correct_index':key,'choice_rationales':rationales,'explanation':rationales[key],'visual_clues':clues,'ground_truth_confidence':'high','ground_truth_basis':'Matched authoritative figure and transcript','citations':[s['source_citation'],{'document':transcript,'page':page}],'image':s['image'],'zoom_image':s['zoom_image'],'original_image':s['original_asset'],'original_filename':s['relative_path'],'category':s['modality'],'collection':'R1','source_origin':'lecture','status':'USABLE','case_context':'','accepted_synonyms':[]})
H='R1 Review - Renal Histology Tran.pdf'; K='R1 Review - Kidney Structure Tran.pdf'
add(2,'Macula densa location','Which structure is indicated by leader line A?',
['Macula densa','Extraglomerular mesangium','Parietal layer of Bowman’s capsule','Intraglomerular mesangium'],0,
['A ends at the closely packed epithelial cells in the tubule wall where it meets the vascular pole.',
'The extraglomerular mesangium occupies the wedge below that tubular wall, indicated by B, rather than the epithelial row at A.',
'The parietal layer forms the outer capsule around the tuft, indicated by F, not this crowded tubular epithelial row.',
'Intraglomerular mesangium lies within the glomerular tuft, indicated by E, not in the adjoining tubule wall.'],
['Crowded tubular epithelial cells','Contact with the vascular pole'],H,2)
add(2,'Extraglomerular mesangium location','Which structure is indicated by leader line B?',
['Visceral layer of Bowman’s capsule','Macula densa','Extraglomerular mesangium','Intraglomerular mesangium'],2,
['The visceral layer lies on the capillary loops inside the tuft, shown at G, rather than in the wedge at B.',
'The macula densa is the crowded row in the adjoining tubular wall at A. B points beneath that row.',
'B points into the cellular wedge outside the glomerular tuft, between the contacting tubule and the arterioles.',
'The intraglomerular mesangium is inside the tuft at E. B lies outside the tuft.'],
['Cellular wedge outside the tuft','Position next to the contacting tubule and arterioles'],H,1)
add(2,'Parietal capsule location','Which layer is indicated by leader line F?',
['Visceral layer of Bowman’s capsule','Parietal layer of Bowman’s capsule','Macula densa','Intraglomerular mesangium'],1,
['The visceral layer follows the capillary surfaces within the tuft at G, not the outer capsule at F.',
'F points to the thin outer wall surrounding the renal corpuscle and bounding the urinary space.',
'The macula densa is the crowded epithelial row in the tubule near A, not the outer corpuscular wall.',
'Intraglomerular mesangium lies between capillary loops inside the tuft at E, not along its outer capsule.'],
['Thin outer corpuscular wall','Urinary space separates this wall from the tuft'],H,1)
add(3,'Corticomedullary architecture','Compare the far left and far right of this entire field. Which regional arrangement best fits the visible architecture?',
['Medulla on the left, cortex on the right','Cortex on the left, medulla on the right','Cortex on both sides','Medulla on both sides'],0,
['The left shows mainly parallel tubular profiles without visible renal corpuscles; the right contains numerous rounded corpuscles among tubules.',
'This reverses the image. The rounded renal corpuscles are concentrated on the right, not the far left.',
'The far-left parallel tubular field lacks the corpuscles that establish cortex on the right.',
'The numerous renal corpuscles on the right are incompatible with medulla on both sides.'],
['Rounded corpuscles on the right','Parallel tubular field at the far left'],H,1,'Comparison')
opts=['Podocyte foot processes','Filtration slits','Glomerular basement membrane','Endothelial fenestrae']
add(7,'Podocyte foot processes in TEM','What do the three arrows from A identify?',opts,0,
['The arrows end on repeated cytoplasmic projections resting on the outer face of the continuous basement membrane.',
'Slits are the narrow spaces between adjacent projections, indicated by B, not the projections themselves.',
'The basement membrane is the continuous intervening band around C, below the A projections.',
'Endothelial fenestrae interrupt the thin layer on the blood side near F, below the basement membrane.'],
['Repeated cytoplasmic projections','Location above the continuous basement membrane'],H,4)
add(7,'Filtration slits in TEM','What do the two arrows from B identify?',opts,1,
['Foot processes are the cytoplasmic projections flanking each B arrow tip; the arrows indicate the intervening gaps.',
'Both B arrows end at narrow gaps between adjacent podocyte foot processes immediately above the basement membrane.',
'The basement membrane forms a continuous band underneath these gaps, not the gaps themselves.',
'Endothelial fenestrae lie in the lower, blood-side cell layer near F rather than between the upper foot processes.'],
['Narrow gaps between foot processes','Urinary side of the basement membrane'],H,4)
add(7,'Glomerular basement membrane in TEM','Identify the continuous band visible immediately beside label C, between the upper projections and the lower cell layer.',opts,2,
['Foot processes form the separate upper projections; they are not the continuous central band.',
'Filtration slits are discrete gaps between the upper projections, not a continuous sheet.',
'The band extends continuously between podocyte foot processes above and the thin endothelial layer below, identifying the glomerular basement membrane.',
'Fenestrations are interruptions in the lower endothelial layer, illustrated near F, not this continuous band.'],
['Continuous central band','Position between podocyte and endothelial layers'],H,4)
add(7,'Endothelial fenestra in TEM','Which feature is indicated by arrow F?',opts,3,
['Foot processes are the upper projections at A, on the opposite side of the basement membrane.',
'Filtration slits lie between those upper projections at B. F is in the lower cell layer.',
'The continuous basement membrane lies above the F arrow tip; F points to an interruption in the cell layer below it.',
'F identifies a small opening in the thin endothelial layer facing the capillary lumen, below the basement membrane.'],
['Opening in the lower thin cell layer','Capillary-lumen side of the basement membrane'],H,4)
add(8,'Mitochondrial abundance across medullary profiles','Compare the walls of the four labeled structures. Which contains the most conspicuous concentration of dark, elongated mitochondrial profiles?',
['Collecting tubule','Descending thin limb','Ascending thick limb','Vasa recta'],2,
['The collecting profile at lower right has a substantial epithelial wall, but fewer densely packed elongated mitochondrial profiles than the upper thick limb.',
'The upper-right thin limb has a slender wall without the dense array of elongated dark profiles in the thick limb.',
'The upper thick-limb wall is packed with elongated dark mitochondrial profiles, markedly more prominent than in the collecting profile.',
'The vasa recta have very thin walls around broad lumens, not the thick mitochondrial-rich epithelial wall at the top.'],
['Dense elongated dark profiles in the upper tubular wall','Much less prominent mitochondrial packing in the collecting profile'],H,5,'Comparison')
add(12,'Urinary space in light microscopy','Which compartment is marked X above the central tuft?',
['Glomerular capillary lumen','Proximal tubular lumen','Renal interstitium','Urinary space'],3,
['Capillary lumens are the smaller channels inside the central tuft, not the broad space surrounding it.',
'The proximal tubular profile lies toward PT at upper left; X occupies the space around the tuft rather than within that epithelial tube.',
'Interstitium lies outside the corpuscle among neighboring structures. X is inside its outer capsule.',
'X occupies the pale space between the central glomerular tuft and its outer capsule, identifying the urinary space.'],
['Pale space outside the tuft','Location inside the surrounding capsule'],K,2)
add(14,'Filtration barrier layer order','Following the red dashed arrow upward, which sequence of layers is crossed from the lower compartment toward the upper compartment?',
['Podocyte slit layer → basement membrane → fenestrated endothelium','Fenestrated endothelium → basement membrane → podocyte slit layer','Basement membrane → fenestrated endothelium → podocyte slit layer','Fenestrated endothelium → podocyte slit layer → basement membrane'],1,
['This reverses the displayed direction. The arrow begins near the lower capillary lumen and ends in the upper urinary space.',
'The arrow travels from the lower capillary lumen across the fenestrated endothelial layer, the central basement membrane, and then between the upper podocyte projections.',
'The lower endothelial layer lies before the central basement membrane along the upward arrow, not after it.',
'The continuous basement membrane lies between endothelium and podocyte projections, not above both cell layers.'],
['Arrow points from capillary lumen toward urinary space','Continuous membrane between the lower lining and upper projections'],K,3,'Physiologic Interpretation')
add(15,'Endothelial surface morphology in SEM','What surface feature is visible where the two right-hand yellow arrowheads end?',
['Interdigitating external foot processes','A brush border of projecting microvilli','Numerous small endothelial openings','Layers of dome-shaped surface cells'],2,
['The interdigitating foot processes lie on the outside of this vessel, especially at the left. The right arrowheads point to its inner lining.',
'The indicated surface is pitted by openings rather than covered by a dense projecting brush border.',
'The right arrowheads point to the inner capillary surface, where numerous small pore-like openings identify endothelial fenestrae.',
'The indicated inner capillary surface is a thin porous lining, not the multilayered dome-cell surface shown in the bladder material.'],
['Pore-like openings on the inner surface','Contrast with external interlocking processes at the left'],K,3,'Pattern Recognition')
Q[-1]['citations'] += [{'document':H,'page':2},{'document':H,'page':5}]
bank={'schema_version':2,'bank_version':'2026-09-30-r1-1','title':'Renal Picture Quiz','lecture':'R1','questions':Q}
(APP/'data/question-bank.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
(APP/'data/review-queue.json').write_text(json.dumps({'schema_version':2,'items':[s for s in manifest['sources'] if s['status']!='USABLE']},ensure_ascii=False,indent=2)+'\n')
print(f'Authored {len(Q)} source-grounded questions.')
