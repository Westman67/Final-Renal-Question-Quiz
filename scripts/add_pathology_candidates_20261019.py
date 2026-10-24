"""Append reviewed pathology captures (R15, R18, R20, R21, R25, R28, R29, R34) as scored questions.

Usage: python3 scripts/add_pathology_candidates_20261019.py stage   (build learner images into a staging folder)
       python3 scripts/add_pathology_candidates_20261019.py commit  (copy assets and append data; run once)
Originals are never modified. Course RLS pages come from the lecture RLS PDFs. No outside sources are used.
"""
from pathlib import Path
from PIL import Image, ImageFilter
import hashlib, json, shutil, sys, datetime, statistics

Image.MAX_IMAGE_PIXELS = None
ROOT = Path('/Users/chriselwell/Desktop/Picture Quiz/Renal Quiz App')
MANUAL = Path('/Users/chriselwell/Desktop/Picture Quiz/Renal/Manual')
STAGE = Path('/tmp/stage-path-20261019')
BATCH = '2026-10-19-pathology-candidate-review'
BANK_VERSION = 'renal-pathology-2026-10-19-candidate-review'
POS = [0, 2, 1, 3, 2, 0, 3, 1]
SPECS = []


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def Q(key, path, concept, qtype, cat, stem, correct, wrong, rats, clues, pages, conf, target, crop=None, masks=None, why=''):
    assert len(wrong) == 3 and len(rats) == 4 and len({correct, *wrong}) == 4, key
    assert all(len(r) > 25 for r in rats), key
    SPECS.append(dict(key=key, path=path, concept=concept, qtype=qtype, cat=cat, stem=stem, correct=correct, wrong=wrong,
                      rats=rats, clues=clues, pages=pages, conf=conf, target=target, crop=crop, masks=masks or [], why=why))


def px(box, w, h):
    x0, y0, x1, y1 = box
    return [int(round(x0 * w)), int(round(y0 * h)), int(round(x1 * w)), int(round(y1 * h))]


def ring_color(im, b):
    w, h = im.size
    x0, y0, x1, y1 = b
    pts = []
    for x in range(max(0, x0 - 8), min(w, x1 + 8), 3):
        for y in (max(0, y0 - 6), min(h - 1, y1 + 6)):
            pts.append(im.getpixel((x, y))[:3])
    for y in range(max(0, y0 - 8), min(h, y1 + 8), 3):
        for x in (max(0, x0 - 6), min(w - 1, x1 + 6)):
            pts.append(im.getpixel((x, y))[:3])
    return tuple(int(statistics.median(p[i] for p in pts)) for i in range(3))


def build_variant(spec):
    src = MANUAL / spec['path']
    raw = src.read_bytes()
    im = Image.open(src).convert('RGB')
    w, h = im.size
    mask_rec = []
    for m in spec['masks']:
        b = px(m[:4], w, h)
        if len(m) > 4:
            mode, thr, dil, med = m[4:8]
            region = im.crop(tuple(b))
            gray = region.convert('L')
            sel = gray.point(lambda v: 255 if (v > thr if mode == 'bright' else v < thr) else 0)
            sel = sel.filter(ImageFilter.MaxFilter(dil))
            cleaned = region.filter(ImageFilter.MedianFilter(med))
            region.paste(cleaned, (0, 0), sel)
            im.paste(region, tuple(b[:2]))
            mask_rec.append({'box': b, 'fill': f'text strokes ({mode} pixels beyond {thr}) replaced by a local median filter', 'threshold': thr})
        else:
            c = ring_color(im, b)
            layer = Image.new('RGB', im.size, c)
            alpha = Image.new('L', im.size, 0)
            alpha.paste(255, tuple(b))
            alpha = alpha.filter(ImageFilter.GaussianBlur(4))
            im = Image.composite(layer, im, alpha)
            mask_rec.append({'box': b, 'fill': 'local median of surrounding pixels', 'rgb': list(c)})
    crop_box = None
    if spec['crop']:
        crop_box = px(spec['crop'], w, h)
        im = im.crop(tuple(crop_box))
    kind = 'crop_mask' if (crop_box and mask_rec) else 'crop' if crop_box else 'mask' if mask_rec else 'unmodified'
    tr = {'type': kind, 'input_dimensions': [w, h], 'coordinate_basis': 'immutable_original_pixels', 'crop_box': crop_box,
          'normalized_crop': list(spec['crop']) if spec['crop'] else None, 'masks': mask_rec, 'output_dimensions': list(im.size),
          'reason': spec['why'] or 'Full capture retained; no answer-revealing text appears in the learner view.'}
    hx = sha_bytes((sha_bytes(raw) + json.dumps(tr, sort_keys=True)).encode())[:24]
    return raw, im, tr, hx


# ---- R18 glomerular (nephritic) captures --------------------------------------------------------------------
Q('r18-crescent', 'R18/Cellular Crescent Extracapillary Proliferation - Histology.png', 'Cellular crescent', 'Visual Identification', 'Histology',
  'In this PAS-stained glomerulus, what is the cell-rich proliferation that fills the urinary space around a compressed capillary tuft?',
  'Cellular crescent (extracapillary proliferation)',
  ['Endocapillary hypercellularity within the capillary loops', 'Nodular mesangial sclerosis', 'Global glomerulosclerosis'],
  ['The cells lie outside the tuft within Bowman space, the extracapillary location of a cellular crescent made of parietal cells and macrophages.',
   'Endocapillary hypercellularity fills the capillary lumens inside the tuft, whereas here the proliferating cells surround the tuft.',
   'Nodular mesangial sclerosis forms acellular matrix nodules within the tuft and does not create a cell-rich collar in the urinary space.',
   'A globally sclerotic glomerulus is a scarred, acellular tuft, but this glomerulus shows an active cellular process around a visible tuft.'],
  ['Cells fill Bowman space around the tuft', 'The capillary tuft is compressed at the center'], [27], 'high',
  'The cellular proliferation surrounding the compressed tuft in the full glomerulus', crop=(0, 0.105, 1, 1),
  why='Top title banner cropped; all tissue pixels below it are unchanged.')
Q('r18-mpgn-pattern', 'R18/Membranoproliferative Pattern - Histology.png', 'Membranoproliferative pattern of injury', 'Pattern Recognition', 'Histology',
  'Which pattern of glomerular injury does this lobulated, hypercellular PAS-stained glomerulus show?',
  'Membranoproliferative pattern',
  ['Minimal-change pattern with normal-appearing glomeruli', 'Collapsing pattern with a retracted tuft', 'Diffuse crescentic pattern with an obliterated tuft'],
  ['Lobulated hypercellular tufts with thickened, reduplicated capillary walls characterize the membranoproliferative pattern, a nonspecific pattern of injury.',
   'Minimal change shows near-normal glomeruli by light microscopy, whereas this tuft is clearly hypercellular and thickened.',
   'A collapsing pattern shows a retracted, wrinkled tuft with swollen overlying podocytes rather than a lobulated expanded tuft.',
   'A crescentic pattern shows a cell mass in Bowman space around the tuft, which is not the dominant feature here.'],
  ['Lobulated tuft with hypercellularity', 'Thickened capillary walls with duplication'], [19, 20], 'high',
  'The overall lobulated hypercellular tuft with thick capillary walls', crop=(0, 0.105, 1, 1),
  why='Top title banner naming the pattern cropped; tuft pixels unchanged.')
Q('r18-tram-track', 'R18/Membranoproliferative Pattern Tram Track - Histology.png', 'GBM tram-track double contours', 'Visual Identification', 'Histology',
  'What is the basement-membrane appearance along the capillary walls on this silver-stained section?',
  'Tram-track double contours',
  ['Spikes projecting from the outer GBM surface', 'Uniform linear thickening without splitting', 'Fibrinoid necrosis of the tuft'],
  ['The silver stain outlines parallel contours along many capillary walls, the tram-track appearance of a membranoproliferative pattern.',
   'Spikes are short projections from the epithelial side of the GBM in membranous nephropathy, not parallel duplicated contours.',
   'Uniform thickening without splitting would show a single dark line, but here the walls show a doubled outline.',
   'Fibrinoid necrosis is a smudgy pink lesion of the tuft, not a doubled silver-stained wall.'],
  ['Parallel doubled dark contours on capillary walls', 'Silver-stained lobulated tuft'], [20], 'high',
  'The doubled capillary-wall contours across the upper tuft', crop=(0, 0.115, 1, 0.74),
  why='Title banner above and the answer label box below the tissue were cropped; remaining pixels unchanged.')
Q('r18-ddd-em', 'R18/Dense Deposit Disease Intramembranous Electron Dense Deposits - EM.png', 'Intramembranous dense deposits', 'Visual Identification', 'Electron microscopy',
  'Which deposit pattern lies within the glomerular basement membrane on this electron micrograph?',
  'Continuous intramembranous electron-dense deposits',
  ['Discrete subepithelial humps', 'Mesangial deposits only', 'No deposits with diffuse foot-process effacement'],
  ['A dark continuous ribbon runs inside the basement membrane, the intramembranous sausage-link pattern of dense deposit disease.',
   'Subepithelial humps are discrete dome-shaped deposits on the epithelial side, not a continuous ribbon within the membrane.',
   'The dense material lies along the capillary wall rather than being confined to the mesangium.',
   'This capillary wall contains obvious dense material, so a no-deposit disease with only effacement does not fit.'],
  ['Dark ribbon within the GBM', 'Loops of thickened dense capillary wall'], [58, 60, 61], 'high',
  'The dense ribbon-like material inside the capillary wall', crop=(0, 0.095, 0.77, 0.82),
  why='Title banner, the answer tag, and a black filler block were cropped out; remaining pixels unchanged.')
Q('r18-hump-em', 'R18/Infection Associated Glomerulonephritis Subepithelial Hump - EM.png', 'Subepithelial hump deposit', 'Visual Identification', 'Electron microscopy',
  'What type of electron-dense deposit is outlined in blue along the capillary wall?',
  'Subepithelial hump',
  ['Subendothelial deposit', 'Mesangial deposit', 'Intramembranous ribbon-like deposit'],
  ['The outlined dome-shaped dense deposit sits on the epithelial side of the GBM, the hump-like subepithelial deposit.',
   'Subendothelial deposits lie on the capillary lumen side of the GBM, opposite the epithelial side where this deposit sits.',
   'Mesangial deposits lie between capillary loops within the stalk rather than along the peripheral wall.',
   'An intramembranous deposit runs inside the GBM as a ribbon, but this deposit forms a discrete dome on one side.'],
  ['Dome-shaped dense deposit on the epithelial side', 'Blue outline marks the deposit'], [49, 61], 'high',
  'The blue-outlined dome-shaped dense deposit', crop=(0, 0.22, 1, 1),
  why='Title banner naming the deposit cropped; lecturer outline kept as a marker.')
Q('r18-fullhouse-if', 'R18/Lupus Nephritis Full House IgG IgM IgA C3 C1q - Immunofluorescence.png', 'Full-house immunofluorescence pattern', 'Pattern Recognition', 'Immunofluorescence',
  'Which immunofluorescence pattern is shown across these panels from one glomerulus?',
  'Full-house pattern with several immunoglobulins plus C3 and C1q',
  ['Linear IgG along the GBM only', 'IgA-dominant mesangial staining only', 'No immune deposits (pauci-immune)'],
  ['IgG, IgA, C3 and C1q all stain the same glomerulus, which is the full-house pattern classically seen in lupus nephritis.',
   'Linear IgG alone would trace smooth capillary walls in a single panel, but multiple panels are positive here.',
   'IgA-dominant staining would be limited to IgA with the other panels negative, which is not the case.',
   'A pauci-immune pattern would show little or no staining in every panel, whereas several panels are bright.'],
  ['Several panels stain in one glomerulus', 'Both immunoglobulins and complement are positive'], [81], 'high',
  'The combined positivity across the immunoglobulin and complement panels')

Q('r18-alport-em', 'R18/Alport Syndrome - EM.png', 'Alport basket-weave GBM', 'Clinical Association', 'Electron microscopy',
  'A young man with hematuria and sensorineural hearing loss has a family history of kidney disease. Which basement-membrane change does this electron micrograph illustrate?',
  'Splitting and fraying of the lamina densa (basket-weave GBM)',
  ['Continuous intramembranous dense deposits', 'Subepithelial hump-like deposits', 'A uniformly thin but structurally intact GBM'],
  ['Alport syndrome shows a thickened, split and frayed lamina densa with basket-weave lamellation and no immune deposits.',
   'Continuous intramembranous deposits define dense deposit disease, which is an immune-complement disease without deafness.',
   'Humps are discrete subepithelial deposits of infection-associated or C3 glomerulonephritis, not a lamellated membrane.',
   'A uniformly thin intact GBM describes thin basement membrane disease, which lacks hearing loss and the lamellated splitting seen here.'],
  ['Thickened irregular capillary wall', 'Lamellation of the basement membrane without dense deposits'], [73, 75, 76], 'high',
  'The thickened lamellated capillary-wall segment', crop=(0.23, 0.115, 1, 1),
  why='Slide title banner and empty left margin cropped; electron micrograph pixels unchanged.')
Q('r18-gbm-fracture-em', 'R18/Cellular Crescent with Fracturing of the GBM - EM.png', 'GBM fracture in crescentic injury', 'Visual Identification', 'Electron microscopy',
  'In this electron micrograph from a crescentic glomerulonephritis, what do the arrows mark?',
  'Gaps where the glomerular basement membrane has fractured',
  ['Subepithelial humps', 'Tubuloreticular inclusions', 'Amyloid fibrils'],
  ['The arrows point to breaks in the otherwise continuous dark basement membrane, the GBM fracturing seen with crescent formation.',
   'Humps are intact dome-shaped dense deposits on the epithelial side, not discontinuities in the membrane.',
   'Tubuloreticular inclusions are tubular structures inside endothelial cytoplasm, not breaks in the basement membrane.',
   'Amyloid fibrils are randomly arranged non-branching fibrils, which are not the finding at the arrows.'],
  ['Arrows sit at discontinuities in the dark GBM', 'Cellular material spills across the gap'], [29], 'medium',
  'The arrowed discontinuities in the basement membrane', crop=(0, 0, 1, 0.93),
  why='Book-citation watermark strip at the bottom cropped; arrows retained.')
Q('r18-pulm-hemorrhage', 'R18/Goodpasture Syndrome Pulmonary Hemorrhage - Gross.png', 'Pulmonary hemorrhage in Goodpasture syndrome', 'Visual Identification', 'Gross pathology',
  'What process is shown on the cut surface of this lung from a patient with rapidly progressive kidney injury?',
  'Diffuse alveolar hemorrhage',
  ['Miliary granulomatous disease', 'Lobar pneumonia with consolidation', 'Anthracosis with emphysema'],
  ['The mottled brown-red cut surface reflects blood and hemosiderin in the air spaces, the pulmonary hemorrhage of Goodpasture syndrome.',
   'Miliary granulomas appear as tiny discrete pale nodules, not a diffuse brown-red discoloration.',
   'Lobar pneumonia produces a uniformly firm, gray-tan consolidated lobe rather than mottled hemorrhage.',
   'Anthracosis shows black carbon pigment and emphysema shows enlarged air spaces, neither of which dominates here.'],
  ['Diffuse mottled red-brown discoloration', 'Hemorrhage spread through the lobe'], [62, 63], 'high',
  'The diffuse red-brown mottling of the cut lung surface', crop=(0, 0.115, 1, 1),
  why='Slide caption banner naming the finding cropped; lung pixels unchanged.')
Q('r18-effacement-em', 'R18/Diffuse Podocyte Foot Process Effacement - EM.png', 'Podocyte foot process effacement', 'Visual Identification', 'Electron microscopy',
  'Which change affects the podocyte foot processes along this capillary wall?',
  'Diffuse effacement (flattening) of the foot processes',
  ['Preserved, regularly spaced foot processes', 'Dense deposits beneath the processes', 'Basket-weave splitting of the GBM'],
  ['The epithelial layer lies flattened along the GBM without distinct interdigitating processes, which is diffuse foot process effacement.',
   'Preserved processes would appear as separated finger-like projections along the membrane, which are not seen here.',
   'No dense deposits appear beneath the flattened cell layer, so the finding is a podocyte change rather than an immune-complex deposit.',
   'The membrane is smooth and thin with no lamellation, so basket-weave splitting does not apply.'],
  ['Flattened epithelial layer on the GBM', 'Enlarged inset shows no separate foot processes'], [38, 97, 99], 'high',
  'The flattened podocyte layer along the capillary wall', crop=(0.02, 0.07, 0.97, 0.965),
  why='Slide title banner and black edge strips cropped; micrograph and inset unchanged.')
# ---- R34 slide-review captures --------------------------------------------------------------------------------
Q('r34-crescent-fibrinoid', 'R34/Anti-GBM Crescentic Glomerulus - Histology.png', 'Cellular crescent with fibrinoid necrosis', 'Visual Identification', 'Histology',
  'This H&E glomerulus from a patient with rapidly progressive kidney injury is replaced by proliferating cells and pink fibrin-like strands. Which active lesion is shown?',
  'Cellular crescent with fibrinoid necrosis',
  ['Membranoproliferative double contours', 'Segmental sclerosis with hyalinosis', 'Kimmelstiel-Wilson nodular glomerulosclerosis'],
  ['Proliferating cells fill the glomerular space with bright pink fibrin-rich strands, the cellular crescent with fibrinoid necrosis of rapidly progressive disease.',
   'Double contours need a basement-membrane stain and show split capillary walls, not a cell mass with fibrin strands.',
   'Segmental sclerosis is a pale scarred segment of the tuft, whereas this field is highly cellular and active.',
   'Kimmelstiel-Wilson nodules are round acellular matrix nodules in a chronic diabetic glomerulus, not an active cellular lesion.'],
  ['Densely cellular glomerulus', 'Bright pink strands within the cell mass'], [20, 29, 30], 'high',
  'The cellular crescent with pink fibrin strands filling the glomerulus')
Q('r34-iga-mesangial', 'R34/IgA Nephropathy Mesangial Proliferation - Histology.png', 'Mesangial proliferation', 'Visual Identification', 'Histology',
  'On this PAS-stained glomerulus, in which compartment is the cellular proliferation concentrated?',
  'The mesangium, within the central stalks of the lobules',
  ['Bowman space outside the tuft', 'The tubular epithelium', 'The subendothelial space of every capillary wall'],
  ['Clusters of nuclei with expanded purple matrix sit in the central stalks between capillary loops, the mesangioproliferative pattern.',
   'Bowman space is free of a cell mass here, so this is not a crescent.',
   'The tubular epithelium is not the proliferating compartment in this glomerular field.',
   'The capillary walls are mostly thin and open, so a diffuse subendothelial process along every wall does not fit.'],
  ['Cell clusters in central lobule stalks', 'Open capillary loops around expanded mesangium'], [33, 42], 'high',
  'The cell and matrix clusters in the central lobular stalks', crop=(0, 0.09, 1, 1),
  why='Label box naming the pattern cropped from the top edge; glomerulus pixels unchanged.')

# ---- R20 interstitial and infectious captures -----------------------------------------------------------------
Q('r20-bk-histology', 'R20/BK Nephropathy in the Allograft Kidney - Histology.png', 'BK nephropathy in allograft', 'Visual Interpretation', 'Histology',
  'A kidney transplant recipient has progressive graft dysfunction. Which process does this biopsy field most support?',
  'BK polyomavirus nephropathy',
  ['Light chain cast nephropathy', 'Xanthogranulomatous pyelonephritis', 'Acute pyelonephritis with bacterial colonies'],
  ['Tubular epithelial cells with enlarged nuclei containing smudged viral inclusions in an allograft indicate BK polyomavirus nephropathy.',
   'Light chain cast nephropathy shows dense fractured casts in tubule lumens rather than viral nuclear change.',
   'Xanthogranulomatous pyelonephritis is dominated by sheets of foamy macrophages, which are not seen here.',
   'Acute pyelonephritis shows neutrophils and bacterial colonies in tubules, not enlarged viral-infected nuclei.'],
  ['Enlarged hyperchromatic nuclei in tubular epithelium', 'Smudgy intranuclear inclusion-like change'], [34], 'medium',
  'The enlarged, smudged tubular epithelial nuclei in the interstitial field', crop=(0, 0, 1, 0.965),
  why='Tiny magnification caption strip at the bottom cropped; tissue pixels unchanged.')
Q('r20-bk-em', 'R20/BK Nephropathy Nuclear Viral Particles - EM.png', 'Nuclear viral particles by EM', 'Visual Identification', 'Electron microscopy',
  'What does the dense array of uniform round particles inside this nucleus represent?',
  'Polyomavirus particles',
  ['Glycogen granules', 'Intranuclear lipid droplets', 'Immune complex deposits'],
  ['Closely packed uniform particles filling the nucleus are virions, the nuclear viral particles of BK nephropathy.',
   'Glycogen granules are cytoplasmic and are not packed in a crystalline array within the nucleus.',
   'Lipid droplets are membrane-poor round clear or dense bodies of varying size, not uniform packed particles.',
   'Immune complexes deposit in basement membranes and mesangium as dense amorphous material, not as discrete particles inside a nucleus.'],
  ['Uniform dark round particles packed together', 'Located within a nuclear profile'], [34], 'high',
  'The uniform packed particles within the nucleus', crop=(0, 0.085, 1, 1),
  why='Slide caption banner naming the finding cropped; micrograph unchanged.')
Q('r20-thyroidization', 'R20/Chronic Pyelonephritis Thyroidization - Histology.png', 'Chronic pyelonephritis scarring', 'Visual Interpretation', 'Histology',
  'This low-power kidney section shows scarring with subcapsular tubules distended by dense pink material. Which chronic process is shown?',
  'Chronic pyelonephritis',
  ['Acute tubular necrosis', 'Light chain cast nephropathy', 'Renal infarction'],
  ['Cortical scarring with atrophic tubules distended by colloid-like casts, termed thyroidization, is characteristic of chronic pyelonephritis.',
   'Acute tubular necrosis shows injured epithelium with preserved architecture, not scarred parenchyma with colloid-like casts.',
   'Light chain cast nephropathy shows fractured casts with giant-cell reaction in a background of myeloma, not subcapsular colloid-like tubules in a scar.',
   'A renal infarct shows ghost-like coagulative necrosis of a wedge, not scarred tissue with distended tubules.'],
  ['Subcapsular tubules distended by pink material', 'Underlying interstitial scarring'], [40, 41], 'medium',
  'The dilated pink-filled subcapsular tubules within scarred parenchyma')
Q('r20-xgp', 'R20/Xanthogranulomatous Pyelonephritis - Histology.png', 'Xanthogranulomatous pyelonephritis macrophages', 'Visual Identification', 'Histology',
  'Which cell type predominates in this inflammatory infiltrate?',
  'Foamy macrophages',
  ['Neutrophils filling tubule lumens', 'Eosinophils within the interstitium', 'Lymphoid follicles with germinal centers'],
  ['Sheets of cells with pale foamy cytoplasm characterize xanthogranulomatous pyelonephritis, a form of chronic pyelonephritis dominated by foamy macrophages.',
   'Neutrophils in tubule lumens indicate acute pyelonephritis, but here the infiltrate is a diffuse sheet of pale histiocytic cells.',
   'Eosinophils would appear as bright pink-granulated cells in an interstitial infiltrate, which does not predominate here.',
   'Lymphoid follicles with germinal centers are organized nodules, not a diffuse sheet of foamy cells.'],
  ['Diffuse sheets of pale foamy cells', 'Mixed small round inflammatory cells in between'], [46, 47], 'medium',
  'The dominant sheets of foamy histiocytic cells')
Q('r20-light-chain-casts', 'R20/Light Chain Cast Nephropathy Tubular Injury and Inflammation - Histology.png', 'Light chain cast nephropathy', 'Visual Interpretation', 'Histology',
  'Which tubular lesion is shown in this biopsy?',
  'Light chain cast nephropathy (myeloma kidney)',
  ['Acute tubular necrosis from ischemia', 'BK polyomavirus nephropathy', 'Hypertensive nephrosclerosis'],
  ['Dense pink casts that fill and distend tubules with surrounding injury and inflammation are the light chain casts of myeloma kidney.',
   'Acute tubular necrosis shows sloughed injured epithelium, not dense obstructing casts in the lumens.',
   'BK nephropathy shows enlarged viral-infected epithelial nuclei rather than obstructing casts.',
   'Hypertensive nephrosclerosis is a vascular and glomerular sclerosis pattern, not tubules plugged by casts.'],
  ['Dense pink casts in dilated tubules', 'Inflammatory cells around the casts'], [52, 53], 'high',
  'The obstructing dense casts within the tubules', crop=(0, 0.12, 1, 1),
  why='Caption banner naming the cast type cropped; tissue pixels unchanged.')
Q('r20-pseudomonas', 'R20/Acute Pyelonephritis Pseudomonas aeruginosa - Histology.png', 'Bacterial colony in pyelonephritis', 'Visual Identification', 'Histology',
  'What fills the tubular lumen inside the white frame, surrounded by neutrophils?',
  'A bacterial colony',
  ['A light chain cast', 'Calcium oxalate crystals', 'Amyloid deposit'],
  ['A pale purple granular mass in a tubule lumen with surrounding neutrophils is a bacterial colony of acute pyelonephritis.',
   'A light chain cast is dense, pink and fractured rather than a granular purple mass of organisms.',
   'Calcium oxalate crystals are refractile angular or rosette-shaped crystals, not a granular purple mass.',
   'Amyloid is pink amorphous material in glomeruli or vessels and does not form a granular purple mass in a tubule lumen.'],
  ['Granular purple mass in a tubule lumen', 'Neutrophils crowd the surrounding interstitium'], [32], 'high',
  'The granular purple mass inside the framed tubule lumen', crop=(0, 0, 0.76, 0.925),
  why='Species-name caption bar and blank right margin cropped; framed field unchanged.')
Q('r20-abscess', 'R20/Renal Abscess - Histology.png', 'Renal abscess', 'Visual Identification', 'Histology',
  'Which lesion is shown in this renal tissue section?',
  'Renal abscess (a dense collection of neutrophils with tissue destruction)',
  ['Granulomatous interstitial nephritis', 'Renal infarct with coagulative necrosis', 'Lymphoplasmacytic chronic interstitial nephritis'],
  ['A dense aggregate of neutrophils replacing tissue is suppurative inflammation forming a renal abscess.',
   'Granulomatous nephritis shows epithelioid histiocytes and giant cells in organized nodules rather than sheets of neutrophils.',
   'An infarct shows ghosted tubules without a neutrophil collection in its center.',
   'Chronic interstitial nephritis shows lymphocytes and plasma cells around scarred tubules, not a dense neutrophilic collection.'],
  ['Dense aggregate of segmented inflammatory cells', 'Adjacent tubule and vessel spared at the edge'], [36, 37], 'high',
  'The dense neutrophil-rich collection in the center of the field')
# ---- R21 vascular captures --------------------------------------------------------------------------------------
Q('r21-hypoperfusion', 'R21/Glomerular Hypoperfusion and Sclerosis Arteriole and Glomerulus - Histology.png', 'Ischemic glomerular collapse', 'Visual Interpretation', 'Histology',
  'What best explains the shrunken, wrinkled tuft within an enlarged urinary space beside this thick-walled vessel?',
  'Ischemia from a narrowed supplying vessel',
  ['Immune complex deposition with crescent formation', 'Viral collapsing podocytopathy', 'Amyloid replacement of the mesangium'],
  ['A retracted wrinkled tuft with a widened urinary space next to a vessel with a thick laminated wall reflects glomerular hypoperfusion from vascular narrowing.',
   'Immune complex disease would show hypercellularity or deposits and crescents, whereas this tuft is shrunken and pale.',
   'Collapsing podocytopathy shows hypertrophic overlying podocytes, which are not the dominant finding next to this narrowed vessel.',
   'Amyloid would expand the mesangium with pink amorphous material rather than shrink the tuft.'],
  ['Retracted wrinkled tuft with wide urinary space', 'Adjacent artery with concentric wall thickening'], [13, 15, 20], 'medium',
  'The retracted tuft and the adjacent thick-walled vessel in one field')
Q('r21-renal-vein-thrombosis', 'R21/Renal Vein Thrombosis - CT.png', 'Renal vein thrombosis on CT', 'Visual Identification', 'CT',
  'In this contrast-enhanced coronal CT, what does the arrow indicate?',
  'Thrombus within the left renal vein',
  ['The normal left renal vein passing anterior to the aorta', 'An enlarged retroperitoneal lymph node', 'An obstructing ureteral stone'],
  ['The arrow marks the left renal vein, which is expanded by a filling defect consistent with thrombus.',
   'A normal renal vein would opacify smoothly rather than show a filling defect at the arrow.',
   'A lymph node would be a separate round soft-tissue mass rather than a tubular structure continuous with the vein.',
   'A ureteral stone is a dense calcified focus in the collecting system, not a filling defect in the renal vein.'],
  ['Arrow points to the left renal vein', 'Filling defect within an otherwise enhancing vein'], [24], 'medium',
  'The arrowed filling defect in the left renal vein', crop=(0, 0, 1, 0.955),
  why='Scan technique caption at the bottom edge cropped; CT pixels unchanged.')
Q('r21-pan', 'R21/Polyarteritis Nodosa Vessel Wall Inflammation - Histology.png', 'Polyarteritis nodosa vessel wall', 'Visual Identification', 'Histology',
  'Which vascular lesion is shown in these muscular arteries?',
  'Polyarteritis nodosa with necrotizing wall inflammation',
  ['Fibromuscular dysplasia', 'Atherosclerotic plaque', 'Cholesterol embolus'],
  ['Concentric inflammatory infiltrate and necrotizing thickening of the muscular artery walls fit polyarteritis nodosa, a medium-vessel vasculitis.',
   'Fibromuscular dysplasia produces fibrous or muscular wall thickening without a prominent inflammatory infiltrate.',
   'An atherosclerotic plaque is an eccentric lipid-rich intimal lesion, not concentric wall inflammation.',
   'A cholesterol embolus appears as needle-shaped clefts in a small vessel lumen, which is not seen here.'],
  ['Concentric inflammatory thickening of vessel walls', 'Inflammatory cells infiltrating the media and surrounding tissue'], [30, 31, 32], 'medium',
  'The inflamed concentrically thickened walls of the two arteries', crop=(0, 0, 1, 0.96),
  why='Faint book-citation watermark strip at the bottom cropped.')
Q('r21-hyalinosis-sclerosis', 'R21/Chronic Lesions Arteriolar Hyalinosis and Arterial Intimal Sclerosis - Histology.png', 'Chronic arteriolar and arterial lesions', 'Classification', 'Histology',
  'Comparing the narrow arteriole at left with the larger artery at right, which pair of chronic lesions is shown?',
  'Arteriolar hyalinosis and arterial intimal sclerosis',
  ['Arteriolar fibrin thrombi and arterial fibrinoid necrosis', 'Arteriolar cholesterol emboli and arterial granulomas', 'Arteriolar intimal sclerosis and arterial hyalinosis'],
  ['The small arteriole wall is replaced by glassy pink hyaline material and the larger artery has a thickened fibrotic intima, the chronic lesions of hyalinosis and intimal sclerosis.',
   'Fibrin thrombi and fibrinoid necrosis are acute lesions of thrombotic angiopathy, not the chronic changes shown.',
   'Cholesterol emboli and granulomas would show clefts or giant cells, which are absent here.',
   'The lesions are reversed in this option because hyalinosis characterizes the small arteriole and intimal sclerosis the larger artery.'],
  ['Glassy pink material in a narrow arteriole wall', 'Thickened fibrotic intima of the larger artery'], [15, 16], 'high',
  'The arteriole at left and the thick-intima artery at right',
  masks=[(0.08, 0.235, 0.40, 0.32), (0.59, 0.40, 0.95, 0.525)],
  why='Two translucent label boxes naming the lesions were filled with the local background color; vessel pixels are unchanged.')
Q('r21-renal-artery-atheroma', 'R21/Atherosclerotic Ischemic Renal Disease Renal Artery - Histology.png', 'Atherosclerotic renal artery narrowing', 'Visual Identification', 'Histology',
  'What process narrows the lumen of this renal artery near the arrow?',
  'Atherosclerotic plaque (ischemic renal disease)',
  ['Fibromuscular dysplasia', 'Thrombotic microangiopathy', 'Necrotizing vasculitis'],
  ['A thick eccentric intimal plaque encroaching on the lumen is the atherosclerotic lesion of ischemic renal artery disease.',
   'Fibromuscular dysplasia produces more circumferential fibromuscular wall change rather than one eccentric plaque.',
   'Thrombotic microangiopathy affects small arterioles and capillaries, not the lumen of a large artery.',
   'Necrotizing vasculitis shows inflammatory infiltrate and wall necrosis, which is not the main feature of this plaque.'],
  ['Eccentric thickened intima', 'Narrowed lumen with arrow at the plaque edge'], [20, 21], 'high',
  'The arrowed eccentric plaque narrowing the lumen')

# ---- R15 urine sediment captures --------------------------------------------------------------------------------
Q('r15-rte-cells', 'R15/Renal Tubular Epithelial Cells Urinary Findings.png', 'Renal tubular epithelial cells in sediment', 'Visual Identification', 'Urine Microscopy',
  'Which cellular element is clumped together in this urine sediment?',
  'Renal tubular epithelial cells',
  ['Neutrophils (white blood cells)', 'Dysmorphic red blood cells', 'Budding yeast'],
  ['Large polygonal cells with round nuclei clumped in sheets are desquamated renal tubular epithelial cells, seen in ATN, AIN and proliferative glomerulonephritis.',
   'Neutrophils are smaller round cells with multilobed nuclei and would not form large sheets of polygonal cells.',
   'Dysmorphic red blood cells are small, pink to colorless discs with membrane blebs, not large nucleated cells.',
   'Budding yeast are small oval refractile organisms with buds, not large polygonal nucleated cells.'],
  ['Large polygonal cells with round nuclei', 'Cells clump in a sheet'], [27], 'medium',
  'The clumped large nucleated polygonal cells')
Q('r15-wbc-sediment', 'R15/WBCs Urine Findings.png', 'White blood cells in sediment', 'Visual Identification', 'Urine Microscopy',
  'What do these round granular cells in the urine sediment represent?',
  'Neutrophils (white blood cells)',
  ['Eumorphic red blood cells', 'Renal tubular epithelial cells', 'Calcium oxalate crystals'],
  ['Uniform round granular cells with segmented nuclei are neutrophils, indicating inflammation in the tubulointerstitial compartment such as pyelonephritis.',
   'Eumorphic red blood cells are smooth pale discs without granular nuclear detail.',
   'Renal tubular epithelial cells are larger and more variable with round eccentric nuclei rather than uniform small granular cells.',
   'Calcium oxalate crystals are refractile envelope or dumbbell shapes, not clustered granular cells.'],
  ['Many uniform round granular cells', 'Multilobed nuclear detail in each cell'], [27], 'medium',
  'The uniform clustered granular round cells')
Q('r15-muddy-brown-cast', 'R15/Muddy brown granular urinary casts.png', 'Muddy brown cast in ATN', 'Visual Identification', 'Urine Microscopy',
  'Which urinary cast is shown, and what does it suggest?',
  'A coarse pigmented granular (muddy brown) cast suggesting acute tubular necrosis',
  ['A red blood cell cast suggesting glomerular bleeding', 'A waxy cast suggesting nephron stasis', 'A white blood cell cast suggesting pyelonephritis'],
  ['A cylindrical cast packed with coarse brown granules is the muddy brown cast characteristic of acute tubular necrosis.',
   'A red blood cell cast would show intact red cells forming a red-orange cylinder rather than coarse brown granules.',
   'A waxy cast is homogeneous and glassy with blunt ends, not packed with coarse granules.',
   'A white blood cell cast contains identifiable leukocytes, not a uniform field of coarse pigmented granules.'],
  ['Cylindrical cast filled with coarse brown granules', 'Rounded end of a cast in a clear background'], [28, 43], 'high',
  'The coarse pigmented granular cast', crop=(0.30, 0, 0.985, 1), masks=[(0.295, 0.41, 0.525, 0.495)],
  why='Left blank margin cropped and the overlaid answer text filled with local background color using a feathered edge; cast pixels otherwise unchanged.')
# ---- R28 renal tumor captures -----------------------------------------------------------------------------------
Q('r28-oncocytoma-gross', 'R28/Benign Neoplasms Cut Surface - Gross.png', 'Oncocytoma gross appearance', 'Visual Identification', 'Gross pathology',
  'Which benign renal neoplasm most likely produced this homogeneous tan cut surface with a pale center?',
  'Oncocytoma',
  ['Angiomyolipoma', 'Clear cell renal cell carcinoma', 'Reninoma (juxtaglomerular cell tumor)'],
  ['A uniform tan-brown mass with a pale central scar is the classic gross appearance of an oncocytoma.',
   'An angiomyolipoma contains visible fat and is typically yellow with variable color rather than uniformly tan.',
   'Clear cell carcinoma is typically golden yellow with hemorrhage and necrosis, not a homogeneous tan mass with a central scar.',
   'A reninoma is a small tumor presenting with hypertension and high renin, and is not usually a large tan mass with a central scar.'],
  ['Homogeneous tan-brown cut surface', 'Pale central scar'], [27, 28], 'medium',
  'The uniform tan cut surface with a pale central scar')
Q('r28-retinal-angioma', 'R28/Retinal Angiomas - Clinical Photo.png', 'Retinal angioma in VHL', 'Clinical Association', 'Clinical photograph',
  'A patient with multifocal renal tumors has this retinal finding. Which hereditary syndrome fits best?',
  'Von Hippel-Lindau disease',
  ['Birt-Hogg-Dube syndrome', 'Hereditary leiomyomatosis and renal cell cancer', 'Tuberous sclerosis complex'],
  ['Retinal angiomas accompany multifocal clear cell renal tumors, CNS hemangioblastomas and pheochromocytoma in Von Hippel-Lindau disease.',
   'Birt-Hogg-Dube syndrome features skin fibrofolliculomas, lung cysts with pneumothorax and renal oncocytic tumors, not retinal angiomas.',
   'Hereditary leiomyomatosis and renal cell cancer features cutaneous and uterine leiomyomas with papillary type II renal cancer.',
   'Tuberous sclerosis is associated with angiomyolipomas rather than the multifocal clear cell tumors paired with retinal angiomas.'],
  ['Retinal vessel abnormality with exudates', 'Fundus photograph'], [15], 'medium',
  'The retinal vascular lesion with surrounding exudate')
Q('r28-bhd-skin', 'R28/Birt Hogg Dube Syndrome Fibrofolliculomas - Clinical Photo.png', 'Fibrofolliculomas in Birt-Hogg-Dube', 'Clinical Association', 'Clinical photograph',
  'A patient with a spontaneous pneumothorax has these small skin papules on the face and trunk. Which syndrome fits best?',
  'Birt-Hogg-Dube syndrome',
  ['Von Hippel-Lindau disease', 'Tuberous sclerosis complex', 'Hereditary leiomyomatosis and renal cell cancer'],
  ['Skin fibrofolliculomas together with pneumothorax and renal oncocytic or chromophobe tumors define Birt-Hogg-Dube syndrome.',
   'Von Hippel-Lindau disease features retinal and CNS hemangioblastomas and clear cell renal tumors rather than fibrofolliculomas.',
   'Tuberous sclerosis shows facial angiofibromas and angiomyolipomas, not fibrofolliculomas with pneumothorax.',
   'Hereditary leiomyomatosis presents with smooth muscle tumors of skin and uterus and papillary type II renal cancer.'],
  ['Multiple small dome-shaped skin papules', 'Papules on nose, neck and trunk'], [29, 30, 31, 32], 'medium',
  'The clustered small dome-shaped skin papules')
Q('r28-papillary-ii', 'R28/Papillary Cell Carcinoma Type II Eosinophilic - Histology.png', 'Papillary renal cell carcinoma type II', 'Classification', 'Histology',
  'Which subtype and hereditary association best fit this papillary renal cell carcinoma?',
  'Type II (eosinophilic), hereditary leiomyomatosis (Reed) syndrome',
  ['Type I (basophilic), trisomy 7 and MET', 'Chromophobe carcinoma, Birt-Hogg-Dube syndrome', 'Clear cell carcinoma, VHL loss'],
  ['A papillary tumor lined by cells with abundant pink cytoplasm is type II, the subtype linked to hereditary leiomyomatosis (Reed) syndrome.',
   'Type I papillary carcinoma is basophilic with small cells and is associated with trisomy 7 and MET, which does not match this eosinophilic lining.',
   'Chromophobe carcinoma shows polygonal cells with perinuclear halos and not a papillary architecture.',
   'Clear cell carcinoma shows nests of clear cells, not fibrovascular papillae lined by eosinophilic cells.'],
  ['Papillary fronds with fibrovascular cores', 'Pink cytoplasm lining the papillae'], [20, 21], 'medium',
  'The papillae lined by pink-cytoplasm tumor cells')

# ---- R29 imaging captures ---------------------------------------------------------------------------------------
Q('r29-lung-mets', 'R29/Hematogenous Lung Mets CT - CT.png', 'Hematogenous lung metastases', 'Visual Interpretation', 'Chest CT',
  'This chest CT shows many well-defined round nodules in both lungs of a patient with a renal malignancy. By which route did they most likely arise?',
  'Hematogenous spread',
  ['Direct local invasion', 'Lymphatic spread to hilar nodes', 'Aspiration of tumor cells'],
  ['Multiple round nodules of varying size scattered through both lungs are the pattern of hematogenous metastases from renal cell carcinoma.',
   'Direct local invasion would involve a contiguous mass crossing tissue planes rather than scattered separate lung nodules.',
   'Lymphatic spread would favor hilar and mediastinal nodes or a linear interstitial pattern, not discrete scattered round nodules.',
   'Aspiration produces dependent airspace disease rather than well-defined bilateral round nodules.'],
  ['Many round nodules of varied size', 'Nodules in both lungs'], [22], 'high',
  'The bilateral scattered well-defined round lung nodules')
Q('r29-fat-ct', 'R29/Fat is Dark on CT - CT.png', 'Fat attenuation on CT', 'Visual Interpretation', 'CT',
  'What attenuation does the region indicated by the arrow have on this CT?',
  'Fat (about -100 to -200 HU)',
  ['Simple fluid (about +10 to +20 HU)', 'Soft tissue (about +40 to +100 HU)', 'Air (about -500 HU)'],
  ['Fat appears dark on CT at roughly -100 to -200 HU, and fat in a renal lesion favors a benign angiomyolipoma.',
   'Simple fluid is darker than soft tissue but much brighter than fat, around +10 to +20 HU.',
   'Soft tissue organs measure about +40 to +100 HU and appear much brighter than the arrowed region.',
   'Air would be essentially black at about -500 HU, as in bowel gas or lung, not the textured gray-black of fat.'],
  ['Arrow marks a dark region beside the kidney', 'Fine strands within the dark region'], [3, 4, 14], 'medium',
  'The dark fat-density region marked by the arrow')
Q('r29-fat-us', 'R29/Fat is Bright on US Ultrasound - Radiograph.png', 'Fat echogenicity on ultrasound', 'Visual Interpretation', 'Ultrasound',
  'On this ultrasound, which tissue most likely makes the arrowed round lesion bright?',
  'Fat, as in an angiomyolipoma',
  ['Simple cyst fluid', 'Gas with shadowing', 'Flowing blood on Doppler'],
  ['Fat is bright on ultrasound, and a bright rounded renal lesion is the typical appearance of a fat-containing angiomyolipoma.',
   'Simple cyst fluid is anechoic and appears black rather than bright.',
   'Gas would produce dirty shadowing behind the focus, which is not the main appearance here.',
   'Flowing blood is assessed with color Doppler and is not what makes a gray-scale lesion bright.'],
  ['Arrow marks a bright rounded lesion', 'Gray-scale image without Doppler'], [3, 4], 'medium',
  'The bright rounded lesion marked by the arrow')
Q('r29-bilateral-hydro-ivu', 'R29/Bilateral Hydronephrosis Radiograph - Radiograph.png', 'Bilateral hydroureteronephrosis on urogram', 'Visual Interpretation', 'Radiograph',
  'What does this excretory urogram show?',
  'Bilateral hydroureteronephrosis',
  ['Bilateral renal agenesis', 'Horseshoe kidney with fused lower poles', 'A unilateral duplicated collecting system'],
  ['Both collecting systems have blunted dilated calyces and both ureters are dilated and tortuous, indicating bilateral hydroureteronephrosis.',
   'Bilateral renal agenesis would show no kidneys or contrast excretion, but both kidneys excrete contrast here.',
   'A horseshoe kidney would show lower poles fused across the midline, which is not shown.',
   'A duplicated system would be unilateral with two ureters on one side, whereas both sides are dilated symmetrically.'],
  ['Dilated calyces in both kidneys', 'Both ureters dilated and tortuous'], [34, 36], 'high',
  'The symmetric dilatation of both collecting systems and ureters')
Q('r29-lytic-bone-met', 'R29/Lytic Bone Mets Hip CT - CT.png', 'Lytic bone metastasis', 'Visual Interpretation', 'CT',
  'In this hip CT from a patient with advanced renal cell carcinoma, what does the arrow indicate?',
  'A lytic bone metastasis',
  ['A sclerotic bone metastasis', 'A simple fracture without tumor', 'Avascular necrosis of the femoral head'],
  ['A well-defined area of bone destruction at the arrow is a lytic metastasis, a typical site of distant spread of renal cell carcinoma.',
   'A sclerotic metastasis would appear as dense white bone rather than a dark destroyed region.',
   'A simple fracture would show a thin lucent line with cortical break but not a destroyed region of bone.',
   'Avascular necrosis involves collapse and sclerosis of the femoral head, but the arrowed abnormality lies in the adjacent bone.'],
  ['Arrow marks a dark area of destroyed bone', 'Hip joint and femoral neck for orientation'], [22], 'medium',
  'The arrowed region of bone destruction')
# ---- R25 imaging captures ---------------------------------------------------------------------------------------
Q('r25-pelvic-ectopia', 'R25/Simple Renal Ectopia RK LK - CT.png', 'Simple renal ectopia', 'Visual Identification', 'CT',
  'Where is the kidney labeled LK located on this coronal CT?',
  'In the pelvis (simple renal ectopia)',
  ['In the normal left renal fossa', 'Fused across the midline as a horseshoe kidney', 'Crossed over to the right side'],
  ['The left kidney lies low near the bony pelvis because it failed to ascend, which is simple renal ectopia.',
   'The normal left renal fossa is high in the retroperitoneum beside the spine, not at this low pelvic level.',
   'A horseshoe kidney would show lower poles joined across the midline, which is not seen here.',
   'Crossed ectopia places the kidney on the opposite side of the midline, but this kidney stays on the left side.'],
  ['LK sits low near the pelvic bones', 'RK in the usual renal fossa for comparison'], [16], 'high',
  'The low pelvic position of the left kidney compared with the right')
Q('r25-renal-agenesis', 'R25/Unilateral Renal Agenesis Single Kidney - CT.png', 'Unilateral renal agenesis', 'Visual Interpretation', 'CT',
  'What does this axial CT show?',
  'A solitary right kidney with compensatory hypertrophy (unilateral renal agenesis)',
  ['A horseshoe kidney', 'Right-sided crossed fused ectopia', 'Bilateral renal agenesis'],
  ['One enlarged kidney is present on the right while the left renal fossa contains bowel, consistent with unilateral agenesis and compensatory hypertrophy.',
   'A horseshoe kidney would show an isthmus of renal tissue connecting two kidneys across the midline.',
   'Crossed fused ectopia would show two fused renal masses on one side, but only one kidney is seen.',
   'Bilateral agenesis is incompatible with this image because a functioning kidney is present.'],
  ['One enlarged kidney on the patient right', 'Bowel in the left renal fossa'], [42], 'medium',
  'The solitary enlarged right kidney with an empty left renal fossa', crop=(0.10, 0.24, 1, 1),
  why='Top strip carrying the overlaid diagnosis label and a fragment of a neighboring panel at the left edge cropped; arrowhead and anatomy unchanged.')
Q('r25-puv-vcug', 'R25/Posterior Urethral Valves VCUG Bladder Neck Posterior Urethra - Radiograph.png', 'Posterior urethral valves on VCUG', 'Visual Interpretation', 'Radiograph',
  'A male newborn has bilateral hydronephrosis and a weak urinary stream. Which diagnosis does this voiding cystourethrogram support?',
  'Posterior urethral valves',
  ['Isolated vesicoureteral reflux', 'A urethral stricture from catheterization', 'Neurogenic bladder'],
  ['A thick-walled bladder above a dilated posterior urethra that narrows abruptly more distally fits posterior urethral valves.',
   'Isolated reflux would show contrast refluxing up the ureters without a dilated posterior urethra with distal narrowing.',
   'A catheter stricture would not explain a congenital obstruction in a newborn with a dilated proximal urethra.',
   'A neurogenic bladder can look trabeculated, but it would not give a sharply tapered distal urethra below a dilated posterior urethra in a male newborn.'],
  ['Dilated posterior urethra above an abrupt narrowing', 'Irregular thick-walled bladder above'], [38], 'high',
  'The dilated posterior urethra with distal tapering below the bladder neck',
  crop=(0, 0, 0.445, 1),
  why='Right portion of the capture carrying printed structure labels and the diagnosis text cropped; the contrast column and short arrowheads are unchanged.')
Q('r25-us-biopsy', 'R25/Ultrasound Guided Renal Biopsy Transplant Kidney - Echo.png', 'Ultrasound-guided renal biopsy needle', 'Visual Identification', 'Ultrasound',
  'What do the arrows mark on this ultrasound-guided kidney biopsy image?',
  'The echogenic biopsy needle',
  ['A perinephric hematoma', 'The main renal artery', 'A staghorn calculus'],
  ['A bright linear echogenic structure entering the cortex marks the biopsy needle used under ultrasound guidance.',
   'A hematoma would be a hypoechoic or complex fluid collection around the kidney rather than a thin bright line.',
   'The renal artery would show a tubular anechoic channel with Doppler flow rather than a bright needle-like line.',
   'A staghorn calculus would be a branching bright focus in the collecting system with distal shadowing, not a thin line at the capsule.'],
  ['Arrows along a thin bright line', 'Line enters the kidney cortex'], [23, 30], 'medium',
  'The bright linear needle echo marked by the arrows')
Q('r25-small-echogenic-kidney', 'R25/Ultrasound in Renal Disease RK 4.9 cm - Echo.png', 'Small echogenic kidney in chronic disease', 'Visual Interpretation', 'Ultrasound',
  'Which finding best characterizes this right kidney on ultrasound?',
  'A small echogenic kidney with thin cortex from chronic renal disease',
  ['An enlarged kidney with preserved corticomedullary differentiation', 'A normal adult kidney of 10 to 12 cm', 'Hydronephrosis with a dilated pelvis'],
  ['The 4.9 cm kidney is small and brighter than the adjacent liver with a thin cortex, the pattern of chronic medical renal disease heading toward end-stage disease.',
   'An enlarged kidney with preserved differentiation is the opposite of this small, bright, poorly differentiated kidney.',
   'A normal adult kidney measures 10 to 12 cm, but this one is labeled 4.9 cm.',
   'Hydronephrosis would show an anechoic dilated pelvis, which is not seen here.'],
  ['Small kidney measuring 4.9 cm', 'Cortex brighter than liver with poor differentiation'], [28, 29], 'high',
  'The small bright thin-cortex kidney next to the liver')
Q('r25-mr-urogram-hydronephrosis', 'R25/Collecting Systems Hydronephrosis MR Urogram - Radiograph.png', 'Hydronephrosis on MR urogram', 'Visual Interpretation', 'MRI',
  'What do the arrows indicate on this MR urogram?',
  'Dilated calyces of hydronephrosis',
  ['Normal sharp minor calyces', 'A duplicated collecting system', 'Calyceal diverticula'],
  ['The arrows mark rounded, dilated calyces with blunted contour, the collecting-system dilatation of hydronephrosis.',
   'Normal minor calyces are small and cup-shaped with sharp fornices rather than rounded dilated pouches.',
   'A duplicated system would show two separate pelvises or ureters on one side, which is not the finding at the arrows.',
   'Calyceal diverticula are small outpouchings connected by a thin neck, not diffuse dilatation of calyces on both sides.'],
  ['Arrows at rounded dilated calyces', 'Both kidneys with dilated collecting systems'], [34], 'high',
  'The blunted dilated calyces marked by the arrows', crop=(0, 0, 1, 0.84),
  why='Answer text box across the lower image cropped; both kidneys and proximal ureters retained.')

assert len(SPECS) == 42 and len({s['key'] for s in SPECS}) == 42


def stage():
    (STAGE / 'assets').mkdir(parents=True, exist_ok=True)
    index = []
    for sp in SPECS:
        raw, im, tr, hx = build_variant(sp)
        im.save(STAGE / 'assets' / f'{hx}.png', optimize=True)
        im.save(STAGE / 'assets' / f'{hx}.webp', 'WEBP', quality=92, method=6)
        index.append(dict(key=sp['key'], path=sp['path'], hx=hx, size=list(im.size), transform=tr))
    (STAGE / 'index.json').write_text(json.dumps(index, indent=1))
    print('staged', len(index))


def commit():
    now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    index = {x['key']: x for x in json.loads((STAGE / 'index.json').read_text())}
    P = ROOT / 'data/pathology'
    bank = json.loads((P / 'question-bank.json').read_text())
    man = json.loads((P / 'source-manifest.json').read_text())
    queue = json.loads((P / 'review-queue.json').read_text())
    cov = json.loads((P / 'coverage.json').read_text())
    src_by_path = {s['relative_path']: s for s in man['sources']}
    added, used_ids = [], set()
    for n, sp in enumerate(SPECS):
        s = src_by_path[sp['path']]
        assert s['status'] == 'REFERENCE_ONLY' and (ROOT / s['original_asset']).exists(), sp['key']
        ix = index[sp['key']]
        hx = ix['hx']
        for ext in ('png', 'webp'):
            shutil.copyfile(STAGE / 'assets' / f'{hx}.{ext}', ROOT / 'assets' / f'{hx}.{ext}')
        pos = POS[n % len(POS)]
        options = list(sp['wrong'])
        rats = list(sp['rats'][1:])
        options.insert(pos, sp['correct'])
        rats.insert(pos, sp['rats'][0])
        lec = sp['path'].split('/')[0]
        cite = s['source_citation']
        rls = [dict(document=cite['document'], page=p, sha256=cite['sha256']) for p in sp['pages'][:3]]
        rls.append(dict(document=sp['path'], page=None, sha256=s['sha256']))
        basis = f"{lec} manual capture visually reviewed against course RLS p. {', '.join(str(p) for p in sp['pages'])}; confidence {sp['conf']}."
        var_id = 'var-' + hx
        tr = ix['transform']
        visual_review = dict(status='passed', checked_at=now, original_and_variant_compared=True,
                             answer_leakage='none observed in final scored variant', diagnostic_pixels_preserved=True)
        s.update(dict(status='USABLE', modality=sp['cat'], tested_concept=sp['concept'], source_citation=dict(cite, page=sp['pages'][0]),
                      review_reason='Distinct source-backed visual target with reviewed learner variant.', ground_truth_basis=basis,
                      batch_id=BATCH, variants=[dict(variant_id=var_id, image=f'assets/{hx}.webp', zoom_image=f'assets/{hx}.png',
                                                      transform=tr, visual_review='passed at native size against original')],
                      variant_review_complete=True, variant_id=var_id, image=f'assets/{hx}.webp', zoom_image=f'assets/{hx}.png',
                      transform=tr, visual_review=visual_review,
                      question_type_matrix=[dict(type=sp['qtype'], supported='YES', visual_target=sp['target'], full_image_required=True,
                                                 preserve=['all diagnostic pixels', 'source edges', 'scale and labels when present'],
                                                 reason='Course-backed target visible in the learner image.')]))
        qid = 'q-' + hashlib.sha1((s['source_id'] + '|' + sp['key']).encode()).hexdigest()[:20]
        assert qid not in used_ids
        used_ids.add(qid)
        added.append(dict(question_id=qid, asset_id=s['asset_id'], source_group_id=s['source_group_id'], source_id=s['source_id'],
                          variant_id=var_id, question_type=sp['qtype'], tested_concept=sp['concept'], stem=sp['stem'],
                          visual_target=sp['target'], joint_composite=False, options=options, correct_index=pos,
                          choice_rationales=rats, explanation=sp['rats'][0], visual_clues=sp['clues'],
                          ground_truth_confidence=sp['conf'], ground_truth_basis=basis, citations=rls, image=f'assets/{hx}.webp',
                          zoom_image=f'assets/{hx}.png', original_image=s['original_asset'], original_filename=sp['path'],
                          category=sp['cat'], collection=lec, source_origin='lecture', status='USABLE', case_context='',
                          accepted_synonyms=[]))
    bank['questions'].extend(added)
    bank['bank_version'] = BANK_VERSION
    done = {s['source_id'] for s in man['sources'] if s.get('batch_id') == BATCH}
    queue['items'] = [x for x in queue['items'] if x['source_id'] not in done]
    for lec in sorted({q['collection'] for q in added}, key=lambda t: float(t[1:])):
        qs = [q for q in bank['questions'] if q['collection'] == lec]
        total = sum(1 for s in man['sources'] if s['relative_path'].startswith(lec + '/'))
        old = cov['lectures'].get(lec, {})
        cov['lectures'][lec] = dict(
            status='Partial coverage', tested_summary=[q['tested_concept'] for q in qs],
            gaps=['Remaining captures stay reference-only because they carry answer-bearing labels, repeat a scored target, or lack a distinct leak-free task.'],
            next_capture=old.get('next_capture') or 'No additional capture required for the current scored set.',
            basis=f'{total} manual captures reviewed; {len(qs)} scored visual questions after the 2026-10-19 candidate review. Coverage remains partial.')
    for name, obj in [('question-bank.json', bank), ('source-manifest.json', man), ('review-queue.json', queue), ('coverage.json', cov)]:
        (P / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    print('added', len(added), 'questions; total', len(bank['questions']), '; queue', len(queue['items']))


if __name__ == '__main__':
    {'stage': stage, 'commit': commit}[sys.argv[1]]()
