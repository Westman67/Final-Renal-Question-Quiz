"""Reproduce only approved R1 derivatives. Originals remain read-only. Requires Pillow."""
import hashlib, json, shutil, argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

APP=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); parser.add_argument('--source',type=Path,required=True); parser.add_argument('--font',default='/System/Library/Fonts/Helvetica.ttc'); args=parser.parse_args()
manifest=json.loads((APP/'data/preflight-manifest.json').read_text())
font=ImageFont.truetype(args.font,24)
# Coordinates always refer to the immutable screenshot, never an intermediate crop.
recipes={
2:{'masks':[[689,85,916,345],[632,357,916,534]],'letters':[['A',700,90],['B',700,139],['C',700,207],['D',700,250],['E',700,299],['F',645,367],['G',645,410],['H',645,456],['I',645,498]]},
3:{'masks':[]},
7:{'masks':[[1490,441,1828,952]]},
8:{'masks':[]},
12:{'masks':[[328,103,382,146]],'letters':[['X',343,109]]},
14:{'masks':[[853,69,1334,599],[238,550,1334,710]]},
15:{'masks':[[1728,376,2110,467]],'fill':'black'}
}
sources=[]
for r in manifest['sources']:
    p=args.source/r['relative_path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],p
    n=r['capture_number']; raw=r['sha256'][:24]; orig=f'assets/{raw}.png'
    shutil.copyfile(p,APP/orig)
    r['original_asset']=orig
    # Remove local account paths from portable metadata. Keep original filename and hash.
    r.pop('original_path',None); r['source_citation'].pop('path',None)
    if n in recipes:
        recipe=recipes[n]; recipe['input_dimensions']=[r['width'],r['height']]; recipe['coordinate_basis']='immutable_original_pixels'
        recipe['normalized_masks']=[[v/(r['width'] if j%2==0 else r['height']) for j,v in enumerate(box)] for box in recipe['masks']]
        recipe['method']='Opaque label masks only, no generated pixels, no anatomy replacement'
        key=hashlib.sha256((r['sha256']+json.dumps(recipe,sort_keys=True)).encode()).hexdigest()[:24]
        with Image.open(p) as inp:
            im=inp.convert('RGB'); draw=ImageDraw.Draw(im)
            for b in recipe['masks']: draw.rectangle((b[0],b[1],b[2]-1,b[3]-1),fill=recipe.get('fill','white'))
            for label,x,y in recipe.get('letters',[]): draw.text((x,y),label,font=font,fill='black')
            im.save(APP/f'assets/{key}.png')
            im.save(APP/f'assets/{key}.webp',quality=90,method=6)
        r.update(status='USABLE',variant_id='var-'+key,image=f'assets/{key}.webp',zoom_image=f'assets/{key}.png',transform=recipe,variant_review_complete=False)
        r['question_type_matrix']=[{'type':'Structure or visual comparison','supported':'YES','reason':'Approved restricted target, source-backed and retained in full.'}]
    else:
        r['variant_review_complete']=True
    sources.append(r)
manifest.update(source_directory='../Renal/Manual/R1',stage='Candidate variants generated; final QA required',sources=sources)
(APP/'data/source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Created 7 candidate variants and 16 immutable teaching copies.')
