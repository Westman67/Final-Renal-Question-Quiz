export const SELECTION_KEY='renal-picture-quiz-bank-selection-v2';
export const BANKS={
 physiology:{
  id:'physiology',dataRoot:'./data',progressKey:'renal-picture-quiz-v2',preferencesKey:'renal-picture-quiz-preferences-v2',exportName:'renal-progress.json',title:'Renal · Visual Questions',brand:'VISUAL QUESTIONS',eyebrow:'Renal · Clinical visual practice',description:'Apply renal anatomy, physiology, fluid balance, acid-base, and dialysis concepts to reviewed course visuals and clinical data.',footer:'Renal course physiology · Manual visuals · Local study tool · Not clinical guidance',homeUrl:'./'
 },
 pathology:{
  id:'pathology',dataRoot:'./data/pathology',progressKey:'renal-pathology-picture-quiz-v2',preferencesKey:'renal-pathology-picture-quiz-preferences-v2',exportName:'renal-pathology-progress.json',title:'Renal Pathology & Related · Visual Questions',brand:'PATHOLOGY VISUAL QUESTIONS',eyebrow:'Renal · Clinical pathology practice',description:'Apply renal pathology, urinalysis, urologic oncology, and imaging concepts to reviewed course visuals and clinical data.',footer:'Renal course pathology and imaging · Manual visuals · Local study tool · Not clinical guidance',homeUrl:'?bank=pathology'
 }
};
export const COMBINED={
 id:'both',progressKey:null,sessionKey:'renal-combined-picture-quiz-session-v2',preferencesKey:'renal-combined-picture-quiz-preferences-v2',exportName:'renal-progress.json',title:'Renal · Visual Questions (both banks)',brand:'VISUAL QUESTIONS · BOTH BANKS',eyebrow:'Renal · Integrated clinical visual practice',description:'Apply renal physiology and pathology together using reviewed course visuals and clinical data.',footer:'Renal course physiology and pathology · Manual visuals · Local study tool · Not clinical guidance',homeUrl:'?bank=both'
};
export const BANK_OPTIONS=[
 {id:'physiology',label:'Physiology',detail:'Anatomy, physiology, fluid and acid-base'},
 {id:'pathology',label:'Pathology',detail:'Pathology, urinalysis, oncology, imaging'},
 {id:'both',label:'Both',detail:'Mixed physiology and pathology'}
];
export function normalizeSelection(value){return BANK_OPTIONS.some(x=>x.id===value)?value:null;}
export function resolveSelection(search='',saved=null){
 return normalizeSelection(new URLSearchParams(search).get('bank'))||normalizeSelection(saved)||'physiology';
}
export function configFor(selection){return selection==='both'?COMBINED:BANKS[selection]||BANKS.physiology;}
export function resolveBankConfig(search='',saved=null){return configFor(resolveSelection(search,saved));}
