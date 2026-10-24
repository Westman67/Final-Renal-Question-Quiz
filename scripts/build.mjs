import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dist=path.join(root,'dist');
const webpQuality=90;
const webpMethod=4;
const maxPublishedBytes=1_000_000_000;
const cwebp=process.env.CWEBP||'cwebp';
const manifestFiles=['data/source-manifest.json','data/pathology/source-manifest.json'];
const bankFiles=['data/question-bank.json','data/pathology/question-bank.json'];
const canonicalDataFiles=[
  'data/coverage.json',
  'data/flag-remediation.json',
  'data/preflight-manifest.json',
  'data/question-bank.json',
  'data/review-queue.json',
  'data/pathology/coverage.json',
  'data/pathology/flag-remediation.json',
  'data/pathology/import-hashes.json',
  'data/pathology/question-bank.json',
  'data/pathology/review-queue.json',
  'reports/case-coverage-ledger-2026-10-24.json',
  'reports/case-coverage-ledger-2026-10-24.md',
  'reports/lecture-grounding-audit-2026-10-24.json'
];

const readJson=relative=>JSON.parse(fs.readFileSync(path.join(root,relative),'utf8'));
const manifests=new Map(manifestFiles.map(relative=>[relative,readJson(relative)]));
const banks=bankFiles.map(readJson);
const exactAssets=new Set();
const conversions=new Map();

function addAsset(relative,context){
  if(!relative)return;
  if(typeof relative!=='string'||!relative.startsWith('assets/'))throw new Error(`Invalid asset path in ${context}: ${relative}`);
  const source=path.join(root,relative);
  if(!fs.existsSync(source))throw new Error(`Missing source asset in ${context}: ${relative}`);
  exactAssets.add(relative);
}

for(const bank of banks){
  for(const q of bank.questions){
    addAsset(q.image,q.question_id);
    addAsset(q.zoom_image,q.question_id);
    addAsset(q.original_image,q.question_id);
  }
}

for(const [manifestPath,manifest] of manifests){
  for(const source of manifest.sources){
    if(source.status==='USABLE'){
      addAsset(source.original_asset,source.source_id);
    }else{
      const input=source.original_asset;
      if(!input||!fs.existsSync(path.join(root,input)))throw new Error(`Missing review source for ${source.source_id}: ${input}`);
      if(path.extname(input).toLowerCase()==='.webp'){
        source.display_asset=input;
        exactAssets.add(input);
      }else{
        const output=`assets/review/${path.basename(input,path.extname(input))}.webp`;
        source.display_asset=output;
        source.display_asset_transform={
          purpose:'GitHub Pages review derivative',
          source_original_asset:input,
          source_sha256:source.sha256,
          format:'WebP',
          quality:webpQuality,
          method:webpMethod,
          dimensions_preserved:true,
          source_original_in_hosted_build:false
        };
        conversions.set(input,output);
      }
    }
    for(const variant of source.variants||[]){
      addAsset(variant.image,`${manifestPath}:${source.source_id}`);
      addAsset(variant.zoom_image,`${manifestPath}:${source.source_id}`);
    }
  }
}

function copy(relative,targetRelative=relative){
  const target=path.join(dist,targetRelative);
  fs.mkdirSync(path.dirname(target),{recursive:true});
  fs.copyFileSync(path.join(root,relative),target);
}

function runCwebp(input,output){
  return new Promise((resolve,reject)=>{
    fs.mkdirSync(path.dirname(path.join(dist,output)),{recursive:true});
    const args=['-quiet','-q',String(webpQuality),'-m',String(webpMethod),'-sharp_yuv',path.join(root,input),'-o',path.join(dist,output)];
    const child=spawn(cwebp,args,{stdio:['ignore','ignore','pipe']});
    let stderr='';
    child.stderr.on('data',chunk=>stderr+=chunk);
    child.on('error',reject);
    child.on('close',code=>code===0?resolve():reject(new Error(`cwebp failed for ${input}: ${stderr.trim()||`exit ${code}`}`)));
  });
}

function directorySize(directory){
  let total=0;
  for(const entry of fs.readdirSync(directory,{withFileTypes:true})){
    const item=path.join(directory,entry.name);
    total+=entry.isDirectory()?directorySize(item):fs.statSync(item).size;
  }
  return total;
}

const probe=spawnSync(cwebp,['-version'],{encoding:'utf8'});
if(probe.status!==0)throw new Error('The optimized build requires cwebp. Install the WebP tools package or set CWEBP to its executable path.');

fs.rmSync(dist,{recursive:true,force:true});
fs.mkdirSync(dist,{recursive:true});
for(const file of ['index.html','styles.css','app.js','engine.js','bank-config.js','combine.js'])copy(file);
for(const file of canonicalDataFiles)copy(file);
for(const [relative,manifest] of manifests){
  const target=path.join(dist,relative);
  fs.mkdirSync(path.dirname(target),{recursive:true});
  fs.writeFileSync(target,`${JSON.stringify(manifest,null,2)}\n`);
}
for(const asset of exactAssets)copy(asset);

const jobs=[...conversions.entries()];
let cursor=0,completed=0;
const workerCount=Math.max(1,Math.min(Number(process.env.WEBP_JOBS)||4,os.availableParallelism(),jobs.length));
async function worker(){
  while(cursor<jobs.length){
    const current=cursor++;
    const [input,output]=jobs[current];
    await runCwebp(input,output);
    completed++;
    if(completed%50===0||completed===jobs.length)console.log(`Optimized ${completed}/${jobs.length} review images`);
  }
}
await Promise.all(Array.from({length:workerCount},worker));

fs.writeFileSync(path.join(dist,'.nojekyll'),'');
const required=[...exactAssets,...conversions.values()];
for(const relative of required){
  if(!fs.existsSync(path.join(dist,relative)))throw new Error(`Hosted build is missing ${relative}`);
}
const builtBytes=directorySize(dist);
const report={
  schema_version:1,
  build_type:'github-pages-optimized',
  byte_limit:maxPublishedBytes,
  built_bytes:builtBytes,
  built_megabytes:Number((builtBytes/1_000_000).toFixed(2)),
  exact_assets:exactAssets.size,
  optimized_review_assets:conversions.size,
  webp_quality:webpQuality,
  webp_method:webpMethod,
  dimensions_preserved:true
};
fs.writeFileSync(path.join(dist,'build-report.json'),`${JSON.stringify(report,null,2)}\n`);
const finalBytes=directorySize(dist);
if(finalBytes>=maxPublishedBytes)throw new Error(`Hosted build is ${(finalBytes/1_000_000).toFixed(2)} MB, exceeding the 1 GB limit.`);
console.log(`Optimized static folder created at ${dist}`);
console.log(`Final size ${(finalBytes/1_000_000).toFixed(2)} MB with ${required.length} validated runtime assets`);
