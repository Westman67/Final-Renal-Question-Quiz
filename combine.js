import {empty,VERSION} from './engine.js?v=20261024cases2';
const KEYS=['questions','groups','concepts','flags','decisions'];
const clone=v=>JSON.parse(JSON.stringify(v));
export function bankIndex(banks){
 const index={questions:{},groups:{},concepts:{},decisions:{},order:Object.keys(banks)};
 for(const [id,s] of Object.entries(banks)){
  for(const q of s.bank){index.questions[q.question_id]??=id;index.groups[q.source_group_id]??=id;index.concepts[q.tested_concept]??=id;}
  for(const src of s.manifest.sources)index.decisions[src.source_id]??=id;
 }
 index.flags=index.questions;
 return index;
}
export function combineBanks(banks){
 return {bank:Object.values(banks).flatMap(s=>s.bank),sources:Object.values(banks).flatMap(s=>s.manifest.sources),coverage:{lectures:Object.assign({},...Object.values(banks).map(s=>s.coverage?.lectures||{}))}};
}
export function mergeProgress(parts,combined=null){
 const merged=empty(),origin={questions:{},groups:{},concepts:{},flags:{},decisions:{}},batches=new Set();
 for(const [id,p] of Object.entries(parts)){
  for(const key of KEYS)for(const [name,value] of Object.entries(p[key]||{})){
   if(!(name in merged[key])){merged[key][name]=clone(value);origin[key][name]=id;}
   else if(key==='concepts'){merged.concepts[name].correct+=value.correct;merged.concepts[name].incorrect+=value.incorrect;}
   else if(key==='questions'){const m=merged.questions[name];for(const f of ['times_seen','times_answered','correct_count','incorrect_count'])m[f]+=value[f];}
  }
  for(const b of p.applied_remediation_batches||[])batches.add(b);
 }
 merged.applied_remediation_batches=[...batches];
 merged.exams=Array.isArray(combined?.exams)?clone(combined.exams):[];
 merged.session=combined?.session?clone(combined.session):null;
 return {merged,origin};
}
export function splitProgress(merged,parts,index,origin={}){
 const first=index.order[0];
 for(const id of Object.keys(parts))for(const key of KEYS)parts[id][key]={};
 for(const key of KEYS)for(const [name,value] of Object.entries(merged[key]||{})){
  const id=index[key][name]||origin[key]?.[name]||first;
  parts[id][key][name]=value;
 }
 return parts;
}
export function combinedSessionPayload(p){return {schema_version:VERSION,session:p.session,exams:p.exams};}
