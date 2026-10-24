"""Append the approved October 5 R5–R8 manual-capture batch.

Inputs are immutable. This script deliberately fails unless the prior R8 bank is
present. Activation still requires native-size visual review and browser QA.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MANUAL = Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')
VAULT_PROD = Path('/Users/chriselwell/Desktop/Systems Vault/Systems Vault/Renal/Other/Production')
M = ROOT / 'data/source-manifest.json'
B = ROOT / 'data/question-bank.json'
C = ROOT / 'data/coverage.json'

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def Q(code, concept, stem, options, rationales, clues, qtype='Physiologic Interpretation', masks=None):
    assert len(options) == len(rationales) == 4 and len(set(options)) == 4
    assert all(len(x) >= 28 for x in rationales)
    return dict(code=code, concept=concept, stem=stem, options=options,
                rationales=rationales, clues=clues, qtype=qtype, masks=masks or [])

# Mask boxes use immutable original pixel coordinates. Every mask covers only
# target text in non-diagnostic space; no arrow, curve, cell border, or channel
# silhouette is altered. Sample pixels are immediately adjacent background.
SPECS = {
 'R5/ANP counter to TGF.png': dict(page=28, group='r5-anp', questions=[
  Q('anp-oppose', 'R5 ANP opposes high-pressure TGF arteriolar changes',
    'In this glomerular diagram, which pair of TGF arteriolar actions do the green ANP inhibitory marks counter?',
    ['Efferent dilation and afferent constriction', 'Efferent constriction and afferent dilation', 'Dilation of both arterioles', 'Constriction of both arterioles'],
    ['The green bars point to the blue efferent DILATE and red afferent CONSTRICT responses, opposing both.',
     'Those are the opposite actions from the two starbursts targeted by the green inhibitory marks.',
     'The diagram labels dilation on only the blue efferent side, not on both vessels.',
     'The red afferent side constricts, but the blue efferent side is labeled DILATE.'],
    ['Green inhibitory marks target both colored starbursts', 'The blue vessel is efferent and the red vessel afferent'])]),
 'R5/Tubuloglomerular Feedback with decreased blood pressure.png': dict(page=12, group='r5-tgf', questions=[
  Q('low-efferent', 'R5 low-pressure TGF efferent constriction',
    'In the low-NaCl macula-densa diagram, what response is hidden in the blue starburst on the efferent side?',
    ['Efferent constriction', 'Efferent dilation', 'Afferent constriction', 'Afferent dilation'],
    ['Blue arrows converge on the labeled efferent vessel, and the adjacent Pgc box rises: efferent constriction.',
     'Dilation would not match the inward blue arrows or the adjacent rise in Pgc.',
     'The blue starburst is beside the labeled efferent vessel, not the afferent vessel.',
     'The red afferent side has outward arrows; this masked blue target is efferent.'],
    ['Low NaCl at macula densa', 'Blue arrows press inward around the efferent vessel'],
    masks=[([76,214,270,266],[149,207])]),
  Q('low-afferent', 'R5 low-pressure TGF afferent dilation',
    'In the low-NaCl macula-densa diagram, what response is hidden in the red starburst on the afferent side?',
    ['Afferent dilation', 'Afferent constriction', 'Efferent dilation', 'Efferent constriction'],
    ['Red arrows spread from the labeled afferent vessel, with increased RPF and Pgc shown above: afferent dilation.',
     'Constriction conflicts with the outward red arrows and the shown rise in RPF.',
     'The red starburst is on the labeled afferent rather than the blue efferent side.',
     'Efferent constriction is the separate blue response across the glomerulus.'],
    ['Red afferent-side arrows point outward', 'RPF and Pgc rise above this branch'],
    masks=[([806,258,944,307],[807,234])])]),
 'R5/Tubuloglomerular Feedback with increased blood pressure.png': dict(page=13, group='r5-tgf', questions=[
  Q('high-efferent', 'R5 high-pressure TGF efferent dilation',
    'In the high-NaCl macula-densa diagram, what response is hidden in the blue efferent-side starburst?',
    ['Efferent dilation', 'Efferent constriction', 'Afferent dilation', 'Afferent constriction'],
    ['Blue arrows diverge from the labeled efferent vessel and its adjacent Pgc box falls: efferent dilation.',
     'Constriction would make the blue arrows converge rather than spread apart.',
     'The masked starburst sits on the efferent vessel, not the red afferent side.',
     'Afferent constriction is the separate red action across the glomerulus.'],
    ['High NaCl at macula densa', 'Blue arrows spread away from the efferent vessel'],
    masks=[([92,218,219,266],[54,208])]),
  Q('high-afferent', 'R5 high-pressure TGF afferent constriction',
    'In the high-NaCl macula-densa diagram, what response is hidden in the red afferent-side starburst?',
    ['Afferent constriction', 'Afferent dilation', 'Efferent constriction', 'Efferent dilation'],
    ['The red arrows converge on the labeled afferent vessel and the neighboring RPF/Pgc box falls.',
     'Dilation conflicts with inward arrows and the displayed reduction in RPF.',
     'The red starburst is beside the afferent vessel, not the blue efferent branch.',
     'Efferent dilation is the separate blue response on the opposite side.'],
    ['High macula-densa NaCl', 'Red arrows converge on the afferent vessel'],
    masks=[([782,237,1026,285],[840,213])])]),
 'R6/Glucose Threshold.png': dict(page=28, questions=[
  Q('glucose-curves', 'R6 filtered excreted and reabsorbed glucose curves after saturation',
    'On this plasma-glucose graph, which pattern is shown after the orange reabsorbed curve reaches its plateau?',
    ['Filtered and excreted glucose keep rising while reabsorption stays nearly flat', 'All three curves plateau together', 'Filtered glucose plateaus while reabsorbed glucose keeps rising', 'Excreted glucose falls as filtered glucose rises'],
    ['Beyond the orange plateau, the green filtered and blue excreted lines continue upward.',
     'The green and blue trajectories remain sloped after the orange line flattens.',
     'The green dashed filtered line does not flatten; it keeps rising across the graph.',
     'The blue dotted excreted curve rises, rather than falling, beyond the threshold region.'],
    ['Orange reabsorbed line becomes horizontal', 'Green and blue lines remain upward sloping'], 'Graph Interpretation')]),
 'R6/Proximal Tubule Amino Acid and Drug Transport.png': dict(page=26, questions=[
  Q('drug-secretion', 'R6 blood-to-lumen secretion of drugs in proximal tubule',
    'In the lower penicillin and diuretic pathway, what transport direction is represented by the leftward arrows?',
    ['Secretion from blood into tubular lumen', 'Reabsorption from lumen into blood', 'Filtration from blood into Bowman’s space', 'Diffusion from lumen into the cell only'],
    ['The lower arrows start on the blood side, cross the cell, and end in the left-hand lumen.',
     'Reabsorption is the opposite, rightward amino-acid pathway in the upper half.',
     'No glomerular capillary or Bowman’s space is present in this proximal-cell schematic.',
     'The lower arrows cross both cell faces and end in the lumen, not within the cell.'],
    ['Blood is labeled at right and lumen at left', 'Lower arrows traverse the cell right to left'],
    masks=[([393,405,493,434],[391,391])])]),
 'R6/Proximal Tubule Cl Transport.png': dict(page=24, questions=[
  Q('chloride-route', 'R6 paracellular chloride reabsorption in proximal tubule',
    'Which route does the lower dotted Cl⁻ arrow take from lumen toward blood in this proximal-tubule schematic?',
    ['Between adjacent cells', 'Through both faces of a single cell', 'From blood back into the tubular lumen', 'Only through the basolateral Na⁺/K⁺ pump'],
    ['The lower dotted line passes through the gap beneath the cell rather than crossing its interior.',
     'The solid upper chloride path crosses the cell; the question targets the lower dotted path.',
     'The arrowheads point right toward blood, not left toward the lumen.',
     'The Na⁺/K⁺ pump is a separate upper-right oval and not on the dotted chloride path.'],
    ['Lower dotted Cl⁻ path skirts the cell base', 'Arrowheads point toward blood'], 'Pathway')]),
 'R6/Proximal Tubule Glucose Transport.png': dict(page=27, questions=[
  Q('apical-sglt', 'R6 apical sodium glucose cotransporter',
    'Which transporter is hidden at the lumen-facing membrane where Na⁺ and glucose enter the proximal-tubule cell together?',
    ['SGLT1/2', 'GLUT1/2', 'Na⁺/K⁺-ATPase', 'Aquaporin 1'],
    ['Both luminal Na⁺ and glucose arrows cross the masked apical carrier, identifying SGLT1/2.',
     'GLUT1/2 is drawn on the blood-facing glucose exit route, not the joint Na⁺-glucose entry.',
     'The Na⁺/K⁺ pump is on the basolateral membrane with Na⁺ leaving and K⁺ entering.',
     'No water arrow crosses this glucose carrier, unlike aquaporin 1.'],
    ['Na⁺ and glucose converge on one apical carrier', 'Glucose exits through a different basolateral carrier'], 'Transporter Identification',
    masks=[([615,283,739,328],[650,272]),([47,445,474,476],[44,432])]),
  Q('basolateral-glut', 'R6 basolateral facilitated glucose transporter',
    'Which transporter is hidden on the blood-facing membrane where glucose leaves the proximal-tubule cell?',
    ['GLUT1/2', 'SGLT1/2', 'Na⁺/K⁺-ATPase', 'NCC'],
    ['The right-hand glucose arrow exits toward blood through this carrier without a coupled Na⁺ arrow.',
     'SGLT1/2 is the apical entry carrier that moves Na⁺ and glucose together on the left.',
     'The Na⁺/K⁺ pump is the blue upper-right oval exchanging Na⁺ and K⁺.',
     'NCC would couple Na⁺ and Cl⁻, neither of which accompanies the right-hand glucose arrow.'],
    ['Blood-facing glucose exit arrow', 'Apical joint Na⁺ and glucose entry remains visible'], 'Transporter Identification',
    masks=[([1006,327,1136,370],[1020,324]),([1158,441,1711,483],[1155,432])])]),
 'R6/Proximal Tubule H2O Transport.png': dict(page=23, questions=[
  Q('water-routes', 'R6 proximal tubule transcellular and paracellular water pathways',
    'Which two water routes are simultaneously depicted between the lumen and blood in this proximal-tubule image?',
    ['Through aquaporin 1 channels and between neighboring cells', 'Only through aquaporin 2 on the apical membrane', 'Only through the Na⁺/K⁺ pump', 'From blood back to lumen through chloride channels'],
    ['The middle water arrows pass through aquaporin 1 at both membranes; a separate lower dotted path bypasses the cell.',
     'Both water channels are labeled aquaporin 1, and the lower dotted route is also shown.',
     'The blue Na⁺/K⁺ pump exchanges ions on the upper right, away from both water paths.',
     'Both water arrow systems run toward blood, not backward through chloride channels.'],
    ['Water crosses two membrane channels in the middle', 'A separate dotted water path passes below the cell'], 'Pathway')]),
 'R6/Proximal Tubule HCO3 Transport.png': dict(page=25, questions=[
  Q('bicarb-cycle', 'R6 carbon dioxide intermediate in proximal bicarbonate reclamation',
    'What crosses the apical membrane along the dotted arrow after luminal bicarbonate is converted near carbonic anhydrase?',
    ['CO₂ and H₂O', 'Intact HCO₃⁻', 'H₂CO₃ alone', 'Na⁺ and Cl⁻'],
    ['The dotted arrow is labeled H₂O + CO₂ on both sides of the apical membrane.',
     'HCO₃⁻ is shown in the lumen and later exiting toward blood, not on the dotted entry arrow.',
     'H₂CO₃ appears above the luminal and cytosolic conversion steps, not on the crossing arrow.',
     'Na⁺ and Cl⁻ use separate membrane arrows and are not the dotted apical pair.'],
    ['Dotted apical crossing from lumen into cell', 'H₂O + CO₂ labels flank that crossing'], 'Pathway')]),
 'R6/Proximal Tubule Na Transport.png': dict(page=22, questions=[
  Q('na-h', 'R6 proximal tubule apical sodium hydrogen exchanger',
    'Which transporter is hidden in the green lumen-facing box where Na⁺ enters and H⁺ exits?',
    ['Na⁺/H⁺ exchanger', 'Na⁺/K⁺-ATPase', 'Na⁺/Cl⁻ cotransporter', 'Aquaporin 1'],
    ['The green apical box has Na⁺ moving into the cell and H⁺ moving toward the lumen.',
     'The Na⁺/K⁺ pump is the blue basolateral oval exchanging Na⁺ and K⁺.',
     'No Cl⁻ arrow accompanies Na⁺ at this green apical box.',
     'Aquaporin carries water, not the opposed Na⁺ and H⁺ arrows shown.'],
    ['Na⁺ enters from lumen at green box', 'H⁺ arrow leaves through the same box'], 'Transporter Identification',
    masks=[([193,436,296,502],[194,432])])]),
 'R6/Trans vs Paracellular Transport.png': dict(page=13, questions=[
  Q('red-route', 'R6 transcellular proximal reabsorption route',
    'What route is hidden beside the upper red arrow that crosses through the tubular cell?',
    ['Transcellular', 'Paracellular', 'Tubular secretion', 'Glomerular filtration'],
    ['The red arrow traverses the cell body between its lumen-facing and interstitial faces.',
     'The lower orange arrow slips between adjacent cells instead of crossing the cell body.',
     'The red arrow points away from lumen toward interstitium, not into the tubular lumen.',
     'This is a tubular-cell schematic rather than a glomerular filtration barrier.'],
    ['Upper red arrow crosses cell interior', 'Lower orange arrow takes a between-cell path'], 'Pathway',
    masks=[([633,183,825,221],[625,177])]),
  Q('orange-route', 'R6 paracellular proximal reabsorption route',
    'What route is hidden beside the lower orange arrow that passes between tubular cells?',
    ['Paracellular', 'Transcellular', 'Tubular secretion', 'Glomerular filtration'],
    ['The orange arrow passes through the intercellular gap rather than the cell interior.',
     'The upper red arrow is the one that crosses through a tubular cell.',
     'The orange arrow points from lumen toward interstitium, not back into the lumen.',
     'The image shows tubular reabsorption routes, not a glomerular filter.'],
    ['Lower orange arrow traverses the between-cell gap', 'Upper red arrow crosses a cell'], 'Pathway',
    masks=[([633,293,803,330],[626,284])])]),
 'R7/Collecting Duct Intercalated Cells Diagram.png': dict(page=16, group='r7-cd-cells', questions=[
  Q('alpha-intercalated', 'R7 alpha intercalated collecting duct cell',
    'Which collecting-duct cell type is hidden in the title of this diagram with apical H⁺ secretion and bloodward HCO₃⁻ exit?',
    ['α-intercalated cell', 'Principal cell', 'β-intercalated cell', 'Convoluted distal type 1 cell'],
    ['Apical H⁺ pumps send acid to lumen while basolateral HCO₃⁻ goes to blood, matching an α-intercalated cell.',
     'A principal cell would show ENaC-mediated Na⁺ uptake and K⁺ secretion instead of this acid-base polarity.',
     'The source chart states β-intercalated cells have the opposite acid-base polarization.',
     'Type 1 distal cells show NCC-mediated Na⁺/Cl⁻ uptake rather than apical H⁺ pumps.'],
    ['Apical H⁺ arrows point into lumen', 'HCO₃⁻ exits toward blood'], 'Cell Identification',
    masks=[([167,2,513,48],[155,51])])]),
 'R7/Collecting Duct Principal Cells Diagram.png': dict(page=16, group='r7-cd-cells', questions=[
  Q('principal-cell', 'R7 principal collecting duct cell',
    'Which collecting-duct cell type is hidden in the title of this ENaC and K⁺-channel diagram?',
    ['Principal cell', 'α-intercalated cell', 'β-intercalated cell', 'Convoluted distal type 1 cell'],
    ['Apical ENaC brings Na⁺ in while BK and ROMK carry K⁺ out to the lumen, the principal-cell pattern.',
     'An α-intercalated cell instead features apical H⁺ pumps and bloodward HCO₃⁻ export.',
     'The β-intercalated pattern reverses acid-base transport rather than showing ENaC/BK/ROMK.',
     'The type 1 distal diagram has NCC without the paired apical K⁺ channels shown here.'],
    ['Apical ENaC brings Na⁺ inward', 'BK and ROMK point K⁺ toward lumen'], 'Cell Identification',
    masks=[([211,28,461,67],[211,77])])]),
 'R7/Convoluted Distal Tubule Type 1 Cell Diagram.png': dict(page=14, group='r7-cdt-types', questions=[
  Q('type1', 'R7 type 1 convoluted distal tubule cell',
    'Which convoluted distal-cell type is shown with apical NCC but no apical ENaC?',
    ['Type 1', 'Type 2', 'Principal collecting-duct cell', 'α-intercalated cell'],
    ['Only the green NCC carrier receives luminal Na⁺ and Cl⁻ in this diagram; no orange ENaC is present.',
     'The type 2 diagram contains both NCC and ENaC on the luminal surface.',
     'Principal collecting-duct cells show ENaC and BK/ROMK rather than NCC alone.',
     'Intercalated cells show H⁺ and HCO₃⁻ acid-base pathways, not NCC uptake.'],
    ['Green apical NCC is present', 'No orange ENaC appears in the cell'], 'Cell Identification',
    masks=[([177,28,310,74],[174,78]),([168,453,311,488],[164,449])])]),
 'R7/Convoluted Distal Tubule Type 2 Cell Diagram.png': dict(page=14, group='r7-cdt-types', questions=[
  Q('type2', 'R7 type 2 convoluted distal tubule cell',
    'Which convoluted distal-cell type is shown with both apical NCC and ENaC?',
    ['Type 2', 'Type 1', 'Principal collecting-duct cell', 'α-intercalated cell'],
    ['Both green NCC and orange ENaC are visible on the luminal face of this one cell.',
     'Type 1 in the paired RLS figure has NCC without the additional ENaC carrier.',
     'A principal cell has ENaC, but the extra apical NCC here distinguishes type 2 distal cells.',
     'Intercalated cells instead display H⁺ and HCO₃⁻ acid-base transport.'],
    ['Both green NCC and orange ENaC are apical', 'Na⁺ enters by two distinct luminal routes'], 'Cell Identification',
    masks=[([205,21,344,70],[440,47]),([157,440,401,477],[410,457])])]),
 'R7/Straight Distal Transporter Na:Cl:K Co-Transporter Diagram.png': dict(page=12, questions=[
  Q('nkcc-ratio', 'R7 thick ascending limb Na K 2Cl cotransport stoichiometry',
    'What ion combination is carried inward through the green lumen-facing cotransporter in this straight-distal/TAL diagram?',
    ['1 Na⁺, 2 Cl⁻, and 1 K⁺', '1 Na⁺ and 1 Cl⁻ only', '1 Na⁺ and 1 K⁺ only', '2 Na⁺, 1 Cl⁻, and 1 K⁺'],
    ['Three inward arrows beside the green carrier are labeled Na⁺, 2 Cl⁻, and K⁺.',
     'The diagram shows an additional inward K⁺ arrow alongside Na⁺ and two Cl⁻.',
     'A distinct 2 Cl⁻ arrow also enters through the green carrier.',
     'The number 2 is attached to Cl⁻, not Na⁺, beside this carrier.'],
    ['Green apical carrier receives three ion streams', 'The chloride stream is marked 2 Cl⁻'], 'Transporter Identification',
    masks=[([238,113,444,181],[236,108])])]),
 'R8/ADH MoA.png': dict(page=9, questions=[
  Q('adh-hormone', 'R8 ADH V2 cAMP PKA principal cell pathway',
    'Which hormone is hidden at the blood-facing receptor that activates cAMP–PKA and promotes water movement through this principal cell?',
    ['ADH', 'Aldosterone', 'ANP', 'Angiotensin II'],
    ['The blood-side V₂ receptor feeds cAMP and PKA, and the diagram shows water crossing apical and basolateral aquaporins.',
     'Aldosterone in the companion lecture diagram acts through an intracellular receptor and ENaC/SGK1, not V₂–cAMP.',
     'ANP is not shown binding the V₂ receptor or driving the pictured aquaporin water pathway.',
     'Angiotensin II is upstream of several volume responses but is not the V₂-receptor ligand shown here.'],
    ['Blood-facing V₂ receptor', 'cAMP to PKA and water-channel route'], 'Mechanism',
    masks=[([682,539,755,580],[761,539])])]),
 'R8/Aldosterone MoA.png': dict(page=6, questions=[
  Q('aldo-hormone', 'R8 aldosterone SGK1 NEDD4 ENaC principal cell pathway',
    'Which hormone is hidden at the blood side of this principal-cell diagram with an intracellular receptor, SGK1, ENaC, and Na⁺ reabsorption?',
    ['Aldosterone', 'ADH', 'ANP', 'Cortisol'],
    ['The intracellular receptor branches to SGK1, ENaC, Na⁺/K⁺-ATPase, and K⁺ leakage; this is the source aldosterone pathway.',
     'ADH acts through a V₂ receptor and cAMP–PKA water-channel pathway in the companion diagram.',
     'ANP is not the intracellular-receptor signal that raises ENaC activity here.',
     'Cortisol is separately drawn entering the 11β-HSD2 conversion path toward cortisone.'],
    ['Intracellular receptor signals to SGK1 and ENaC', 'Cortisol is separately diverted to cortisone'], 'Mechanism',
    masks=[([669,162,866,202],[665,159])])]),
}

REFERENCE = {
 'R6/Reabsorption of various substances in the proximal tubule.png': (9, 'REFERENCE_ONLY', 'The capture clips the TF/P y-axis label at its left boundary. Reconstructing an axis would invent pixels; retain as teaching original.'),
 'R7/Collecting Duct Intercalated Cells Chart.png': (16, 'REFERENCE_ONLY', 'Text-only summary card; mechanism is tested through the separately supplied cell diagram.'),
 'R7/Collecting Duct Principal Cells Chart.png': (16, 'REFERENCE_ONLY', 'Text-only summary card; mechanism is tested through the separately supplied cell diagram.'),
 'R7/Convoluted Distal Tubule Type 1 Cell Chart.png': (14, 'REFERENCE_ONLY', 'Text-only summary card; NCC pattern is tested through the paired cell diagram.'),
 'R7/Convoluted Distal Tubule Type 2 Cell Chart.png': (14, 'REFERENCE_ONLY', 'Text-only summary card; NCC plus ENaC pattern is tested through the paired cell diagram.'),
}

assert len(SPECS) == 18 and len(REFERENCE) == 5
m = json.loads(M.read_text()); b = json.loads(B.read_text()); c = json.loads(C.read_text())
assert len(m['sources']) == 35 and len(b['questions']) == 69
assert not any(s.get('batch_id') == '2026-10-05-r5-r8-extra' for s in m['sources'])
old = next(s for s in m['sources'] if s['relative_path'].startswith('R6/Screenshot 2026-10-03 at 12.51.49'))
renamed = 'R6/Peritubular Capillary Lumen in the Proximal Tubule Histo.png'
assert not (MANUAL / old['relative_path']).exists()
assert sha(MANUAL / renamed) == old['sha256']
old['aliases'] = [old['relative_path']]
old['relative_path'] = renamed
old['review_reason'] += ' The user renamed this exact-hash capture; the new path is an alias, not a new image.'

VM = {}
for lec in ('R5','R6','R7','R8'):
    path = next(VAULT_PROD.glob(f'{lec} - */lecture-manifest.json'))
    vm = json.loads(path.read_text())
    assert vm['lecture_id'] == lec
    for x in vm['sources']:
        p = Path(x['path'])
        if not p.exists():
            p = Path('/Users/chriselwell/Desktop/Renal/Lectures') / p.name
        assert p.is_file() and sha(p) == x['sha256'], p
    VM[lec] = vm

existing = {s['relative_path'] for s in m['sources']}
new_files = {str(p.relative_to(MANUAL)) for lec in ('R5','R6','R7','R8') for p in (MANUAL / lec).glob('*.png')} - existing
assert new_files == set(SPECS) | set(REFERENCE), sorted(new_files ^ (set(SPECS) | set(REFERENCE)))

families = {}
for rel in SPECS:
    group = SPECS[rel].get('group')
    if group:
        families.setdefault(group, []).append(sha(MANUAL / rel))
group_ids = {k: 'group-' + hashlib.sha256(''.join(sorted(v)).encode()).hexdigest()[:16] for k,v in families.items()}

new_q = []
for rel in sorted(new_files):
    spec = SPECS.get(rel)
    page, status, reason = (spec['page'], 'USABLE', 'One or more distinct source-backed visual targets are safely testable.') if spec else REFERENCE[rel]
    source = MANUAL / rel
    digest = sha(source)
    with Image.open(source) as im:
        im.load(); assert im.format == 'PNG'
        w,h,mode = im.width,im.height,im.mode
        small=im.convert('L').resize((9,8))
        bits=''.join('1' if small.getpixel((x,y)) > small.getpixel((x+1,y)) else '0' for y in range(8) for x in range(8))
    orig=f'assets/{digest[:24]}.png'
    if not (ROOT/orig).exists(): shutil.copyfile(source,ROOT/orig)
    assert sha(ROOT/orig)==digest
    lec=rel.split('/')[0]
    rls=next(x for x in VM[lec]['sources'] if x['kind']=='rls')
    sid='src-'+digest[:16]
    s=dict(relative_path=rel,extension='.png',bytes=source.stat().st_size,
       sha256=digest,kind='raster',width=w,height=h,format='PNG',mode=mode,
       decode_status='ok',asset_id='asset-'+digest[:16],source_id=sid,
       source_group_id=group_ids.get(spec.get('group')) if spec and spec.get('group') else 'group-'+digest[:16],
       perceptual_hash=f'{int(bits,2):016x}',perceptual_hash_method='64-bit dHash',
       source_origin='lecture',acquisition='user manual RLS capture',lecture_id=lec,system='Renal',
       status=status,modality='Graph' if rel.endswith(('Glucose Threshold.png','Reabsorption of various substances in the proximal tubule.png')) else 'Diagram',
       tested_concept='; '.join(q['concept'] for q in spec['questions']) if spec else Path(rel).stem,
       review_reason=reason,
       ground_truth_basis=f'Original manual capture visually matched to {lec} RLS p. {page}; decisive arrows, curves, or labels independently checked.',
       source_citation=dict(document=Path(rls['path']).name,page=page,sha256=rls['sha256']),
       rights_status='User-supplied course material, local educational use only; no redistribution authorization established',
       original_asset=orig,variants=[],variant_review_complete=False,batch_id='2026-10-05-r5-r8-extra',
       question_type_matrix=[dict(type='Distinct visual target',supported='YES' if spec else 'NO',
                                  reason=reason),dict(type='Unverifiable or repetitive task',supported='NO',
                                  reason='No additional distinct image-dependent answer is established from this capture.')])
    if spec:
        for target in spec['questions']:
            with Image.open(source) as original:
                im=original.convert('RGB')
                mask_boxes=[];fills=[]
                for box,sample in target['masks']:
                    x0,y0,x1,y1=box; sx,sy=sample
                    assert 0<=x0<x1<=w and 0<=y0<y1<=h
                    fill=im.getpixel((sx,sy))
                    ImageDraw.Draw(im).rectangle((x0,y0,x1-1,y1-1),fill=fill)
                    mask_boxes.append(box);fills.append(dict(sample=sample,rgb=fill))
                recipe=dict(masks=mask_boxes,input_dimensions=[w,h],coordinate_basis='immutable_original_pixels',
                            method='Opaque target-text masks only; no graph data, arrows, cell borders, or tissue changed' if mask_boxes else 'Unmodified original image; visual relationship is tested without a target-label mask',
                            fills=fills,target=target['concept'],
                            normalized_masks=[[a/w,b/h,c/w,d/h] for a,b,c,d in mask_boxes])
                key=hashlib.sha256((digest+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
                zoom=f'assets/{key}.png';display=f'assets/{key}.webp'
                im.save(ROOT/zoom);im.save(ROOT/display,format='WEBP',quality=92,method=6)
            v=dict(variant_id='var-'+key,image=display,zoom_image=zoom,transform=recipe,
                   visual_review='PENDING individual native-size comparison')
            s['variants'].append(v)
            if len(s['variants'])==1:
                s.update(variant_id=v['variant_id'],image=display,zoom_image=zoom,transform=recipe)
            qid='q-'+hashlib.sha256((sid+target['code']+v['variant_id']).encode()).hexdigest()[:20]
            manual_citation=dict(document=rel,page=None,sha256=digest)
            new_q.append(dict(question_id=qid,asset_id=s['asset_id'],source_group_id=s['source_group_id'],
                source_id=sid,variant_id=v['variant_id'],question_type=target['qtype'],
                tested_concept=target['concept'],stem=target['stem'],visual_target=target['stem'],joint_composite=False,
                options=target['options'],correct_index=0,choice_rationales=target['rationales'],
                explanation=target['rationales'][0],visual_clues=target['clues'],ground_truth_confidence='high',
                ground_truth_basis=s['ground_truth_basis'],citations=[s['source_citation'],manual_citation],
                image=display,zoom_image=zoom,original_image=orig,original_filename=rel,
                category=s['modality'],collection=lec,source_origin='lecture',status='USABLE',
                case_context='',accepted_synonyms=[]))
    m['sources'].append(s)

assert len(new_q)==22 and len({q['question_id'] for q in new_q})==22
m['source_count_physical']=len(m['sources'])
m['approval']='User approved complete R5–R8 added-photo generation prompt on 2026-10-05.'
m['stage']='New R5–R8 candidates staged; individual native-size review and browser QA pending'
m['generated_at']=datetime.now().astimezone().isoformat(timespec='seconds')
b['bank_version']='2026-10-05-renal-r5-r8-extra-1';b['questions'].extend(new_q)
M.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
B.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
(ROOT/'data/review-queue.json').write_text(json.dumps({'schema_version':2,'items':[s for s in m['sources'] if s['status']!='USABLE']},ensure_ascii=False,indent=2)+'\n')
print(f'Staged {len(new_files)} novel originals, {len(new_q)} candidate questions, {sum(s["status"]!="USABLE" for s in m["sources"])} review items; renamed R6 alias reconciled.')
