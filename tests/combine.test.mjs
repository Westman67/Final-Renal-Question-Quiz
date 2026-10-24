import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {resolveSelection,configFor,COMBINED,BANKS,SELECTION_KEY} from '../bank-config.js';
import {empty,filtered,session,see,answer,validateImport} from '../engine.js';
import {bankIndex,combineBanks,mergeProgress,splitProgress,combinedSessionPayload} from '../combine.js';
const load=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url)));
const phys={bank:load('data/question-bank.json').questions,manifest:load('data/source-manifest.json'),coverage:load('data/coverage.json')};
const path={bank:load('data/pathology/question-bank.json').questions,manifest:load('data/pathology/source-manifest.json'),coverage:load('data/pathology/coverage.json')};
const parts={physiology:phys,pathology:path};
test('bank selection prefers the address, then the saved choice, then physiology',()=>{
 assert.equal(resolveSelection('?bank=both','pathology'),'both');assert.equal(resolveSelection('','pathology'),'pathology');assert.equal(resolveSelection('',null),'physiology');assert.equal(resolveSelection('?bank=nope','also-nope'),'physiology');
 assert.equal(configFor('both').id,'both');assert.equal(configFor('pathology').progressKey,BANKS.pathology.progressKey);assert.equal(SELECTION_KEY.includes('selection'),true);
});
test('the two banks never share question, group, source, or progress keys',()=>{
 const ids=new Set(phys.bank.map(q=>q.question_id));assert(path.bank.every(q=>!ids.has(q.question_id)));
 const groups=new Set(phys.bank.map(q=>q.source_group_id));assert(path.bank.every(q=>!groups.has(q.source_group_id)));
 const sources=new Set(phys.manifest.sources.map(s=>s.source_id));assert(path.manifest.sources.every(s=>!sources.has(s.source_id)));
 assert.notEqual(BANKS.physiology.progressKey,BANKS.pathology.progressKey);assert.notEqual(COMBINED.sessionKey,BANKS.physiology.progressKey);assert.notEqual(COMBINED.sessionKey,BANKS.pathology.progressKey);
});
test('combined bank is the exact union and lecture filters span both banks',()=>{
 const c=combineBanks(parts);assert.equal(c.bank.length,phys.bank.length+path.bank.length);assert.equal(c.sources.length,phys.manifest.sources.length+path.manifest.sources.length);
 assert.equal(filtered(c.bank,empty(),{collection:['R1','R17']}).length,phys.bank.filter(q=>q.collection==='R1').length+path.bank.filter(q=>q.collection==='R17').length);
 const s=session(c.bank,'learn','all');assert.equal(s.items.length,c.bank.length);
 const byId=Object.fromEntries(c.bank.map(q=>[q.question_id,q]));assert(s.items.some(i=>phys.bank.includes(byId[i.id])));assert(s.items.some(i=>path.bank.includes(byId[i.id])));
});
test('merging then splitting returns each bank only its own progress',()=>{
 const index=bankIndex(parts),c=combineBanks(parts),pa=empty(),pb=empty();
 const qa=phys.bank[0],qb=path.bank[0],byId=Object.fromEntries(c.bank.map(q=>[q.question_id,q]));
 const ia=session([qa],'learn','all').items[0];ia.draft=qa.correct_index;see(pa,qa,ia);answer(pa,qa,ia);pa.flags[qa.question_id]={question_id:qa.question_id,status:'open',note:'x'};
 const {merged,origin}=mergeProgress({physiology:pa,pathology:pb});
 const sess=session([qa,qb],'learn','all');merged.session=sess;
 const ib=sess.items.find(i=>i.id===qb.question_id);ib.draft=(qb.correct_index+1)%5;see(merged,qb,ib);answer(merged,qb,ib);
 merged.flags[qb.question_id]={question_id:qb.question_id,status:'open',note:'y'};
 const out=splitProgress(merged,{physiology:empty(),pathology:empty()},index,origin);
 assert.deepEqual(Object.keys(out.physiology.questions),[qa.question_id]);assert.deepEqual(Object.keys(out.pathology.questions),[qb.question_id]);
 assert.deepEqual(Object.keys(out.physiology.flags),[qa.question_id]);assert.deepEqual(Object.keys(out.pathology.flags),[qb.question_id]);
 assert.equal(out.pathology.questions[qb.question_id].incorrect_count,1);assert.equal(out.physiology.questions[qa.question_id].correct_count,1);
 assert(out.physiology.concepts[qa.tested_concept]&&!out.physiology.concepts[qb.tested_concept]);assert(out.pathology.concepts[qb.tested_concept]);
 assert.equal(out.physiology.session,null);assert.equal(out.pathology.session,null);
 const payload=combinedSessionPayload(merged);assert.doesNotThrow(()=>validateImport({...empty(),session:payload.session,exams:payload.exams},c.bank));
});
test('progress saved under the wrong bank is routed to the bank that owns the question',()=>{
 const index=bankIndex(parts),moved=path.bank.find(q=>q.collection==='R23'),pa=empty();
 pa.questions[moved.question_id]={times_seen:1,times_answered:1,correct_count:1,incorrect_count:0,last_result:'correct',marked:false};pa.groups[moved.source_group_id]={times_seen:1};pa.concepts[moved.tested_concept]={correct:1,incorrect:0};
 const {merged,origin}=mergeProgress({physiology:pa,pathology:empty()});const out=splitProgress(merged,{physiology:empty(),pathology:empty()},index,origin);
 assert(out.pathology.questions[moved.question_id]);assert(!out.physiology.questions[moved.question_id]);assert(out.pathology.groups[moved.source_group_id]);assert(out.pathology.concepts[moved.tested_concept]);
});
test('blocked R17 diuretic table variant is wired to its question',()=>{
 const q=path.bank.find(x=>x.legacy_question_id==='q-b162e3a354041916d035'),s=path.manifest.sources.find(x=>x.source_id===q.source_id),v=s.variants.find(x=>x.variant_id===q.variant_id);
 assert(v);assert.equal(v.transform.type,'mask');assert.equal(v.transform.masks.length,12);assert(q.stem.includes('masked')||q.legacy_stem.includes('hidden'));assert.equal(q.image,v.image);assert.equal(q.zoom_image,v.zoom_image);
 for(const k of ['image','zoom_image'])assert(fs.existsSync(new URL('../'+q[k],import.meta.url)));
 const fix=load('data/pathology/flag-remediation.json');assert(fix.flagged_question_ids.includes(q.legacy_question_id));
});
