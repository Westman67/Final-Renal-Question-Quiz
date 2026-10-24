import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {BANK_OPTIONS,resolveBankConfig} from '../bank-config.js';
import {empty,filtered,session,answer,canReveal} from '../engine.js';

const load=path=>JSON.parse(fs.readFileSync(new URL('../'+path,import.meta.url)));
const pathBank=load('data/pathology/question-bank.json');
const pathManifest=load('data/pathology/source-manifest.json');
const physBank=load('data/question-bank.json');

test('two bank routes isolate data and browser storage',()=>{
 const pathology=resolveBankConfig('?bank=pathology'),physiology=resolveBankConfig('');
 assert.equal(pathology.dataRoot,'./data/pathology');assert.equal(physiology.dataRoot,'./data');
 assert.notEqual(pathology.progressKey,physiology.progressKey);assert.notEqual(pathology.preferencesKey,physiology.preferencesKey);
 assert.equal(resolveBankConfig('?bank=unknown').id,'physiology');
});

test('physiology, pathology, and both are selectable',()=>{
 assert.deepEqual(BANK_OPTIONS.map(item=>item.id),['physiology','pathology','both']);
 assert(BANK_OPTIONS.every(item=>item.label.length>3&&item.detail.length>10));
});

test('expanded banks remain isolated and preserve all 955 image-source captures',()=>{
 assert.equal(physBank.questions.length,109);assert.equal(pathBank.questions.length,211);assert.equal(pathManifest.sources.length,852);
 const collections=[...new Set(pathBank.questions.map(question=>question.collection))];
 for(const lecture of ['R14','R23','R24','R27','R32','R34','R35','R36','R37','R38','R39','R41'])assert(collections.includes(lecture),lecture);
});

test('pathology images and independent table visuals satisfy their distinct contracts',()=>{
 const byId=new Map(pathManifest.sources.map(source=>[source.source_id,source]));let contextTables=0,tableOnly=0;
 for(const question of pathBank.questions){
  assert.equal(question.options.length,5);assert.equal(new Set(question.options).size,5);
  assert.equal(question.choice_rationales.length,5);assert(question.choice_rationales.every(value=>value.length>25));
  assert(question.choice_rationales.every(value=>!/supported in the source bank|not the relationship or target tested|not the target tested/i.test(value)));
  assert.equal(question.format_version,'clinical-visual-v1');assert(['foundational','intermediate','advanced'].includes(question.difficulty));
  assert(['recognition','interpretation','mechanism','calculation','clinical_integration'].includes(question.reasoning_type));
  assert(question.scenario&&question.lead_in&&question.visual_target);
  if(question.context_table){contextTables++;assert(['primary','additional'].includes(question.context_table.placement));assert(question.context_table.rows.every(row=>row.length===question.context_table.columns.length));assert.match(question.context_table.source.document,/\.pdf$/);assert(question.context_table.source.page>0);}
  if(question.visual_kind==='table'){
   tableOnly++;assert.equal(question.source_origin,'lecture-table');assert.equal(question.context_table.placement,'primary');assert(question.case_id&&question.generation_batch);
   for(const key of ['image','zoom_image','original_image'])assert.equal(question[key],undefined);
  }else{
   const source=byId.get(question.source_id);assert(source);assert.equal(source.status,'USABLE');assert.equal(source.variant_review_complete,true);assert(source.variants.some(variant=>variant.variant_id===question.variant_id));assert(question.legacy_question_id);
   for(const key of ['image','zoom_image','original_image']){assert.match(question[key],/^assets\/[a-f0-9]{24}\.(webp|png)$/);assert(fs.existsSync(new URL('../'+question[key],import.meta.url)));}
  }
 }
 assert.equal(tableOnly,71);assert.equal(contextTables,90);
});

test('case-heavy lecture counts and shared Learn/Exam behavior are correct',()=>{
 const bank=pathBank.questions,progress=empty();
 const expected={R23:12,R24:12,R27:22,R30:5,R32:5,R34:14,R35:4,R36:13,R37:5,R38:1,R39:1,R41:5};
 for(const [lecture,count] of Object.entries(expected))assert.equal(filtered(bank,progress,{collection:[lecture]}).length,count,lecture);
 const learn=session(bank,'learn','10'),question=bank.find(item=>item.question_id===learn.items[0].id);learn.items[0].draft=question.correct_index;assert.equal(canReveal(learn,learn.items[0]),false);answer(progress,question,learn.items[0]);assert.equal(canReveal(learn,learn.items[0]),true);
 const exam=session(bank,'exam','10'),examQuestion=bank.find(item=>item.question_id===exam.items[0].id);exam.items[0].draft=examQuestion.correct_index;answer(progress,examQuestion,exam.items[0]);assert.equal(canReveal(exam,exam.items[0]),false);exam.complete=true;assert.equal(canReveal(exam,exam.items[0]),true);
});

test('advanced questions exceed twenty percent and answer positions stay balanced',()=>{
 const all=[...physBank.questions,...pathBank.questions],advanced=all.filter(question=>question.difficulty==='advanced').length;
 assert(advanced/all.length>=0.20,{advanced,total:all.length});
 for(const bank of [physBank.questions,pathBank.questions]){
  const counts=[0,1,2,3,4].map(index=>bank.filter(question=>question.correct_index===index).length);
  assert(Math.max(...counts)-Math.min(...counts)<=1,counts);
 }
});

test('R30 explicitly distinguishes the four renal tubular acidosis profiles',()=>{
 const rta=pathBank.questions.filter(question=>question.case_id?.startsWith('R30-RTA-'));
 assert.equal(rta.length,4);
 assert.deepEqual(new Set(rta.map(question=>question.case_id)),new Set([
  'R30-RTA-classic-distal-type-1',
  'R30-RTA-proximal-type-2',
  'R30-RTA-type-4',
  'R30-RTA-voltage-mediated-distal-type-1',
 ]));
 assert(rta.every(question=>question.visual_kind==='table'&&question.difficulty==='advanced'));
 assert(rta.every(question=>question.citations.some(source=>source.document==='R30 Acid-Base Balance RLS.pdf'&&source.page>=38&&source.page<=43)));
 const joined=rta.map(question=>[question.stem,question.explanation,...question.visual_clues,JSON.stringify(question.context_table)].join(' ')).join(' ').toLowerCase();
 for(const marker of ['persistently >6.0','variable urine anion gap','usually <5.5','negative distal lumen potential'])assert(joined.includes(marker),marker);
});

test('case ledger maps every distinct case to a live question and records the text-only boundary',()=>{
 const ledger=load('reports/case-coverage-ledger-2026-10-24.json'),ids=new Set([...physBank.questions,...pathBank.questions].map(question=>question.question_id));
 assert.equal(ledger.summary.distinct_cases,100);assert.equal(ledger.summary.unmapped_distinct_cases,0);assert.equal(ledger.summary.new_table_visual_questions,81);
 for(const row of ledger.cases)for(const id of row.question_ids)assert(ids.has(id),`${row.case_id}: ${id}`);
 assert.deepEqual(ledger.not_scored_as_visual_cases.map(row=>row.items),[10,154]);
});
