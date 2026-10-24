#!/usr/bin/env python3
"""Add source-grounded, table-first lecture cases to the renal Visual Question banks.

The script is intentionally idempotent. It replaces only its own generation batch,
preserves all existing image questions and stable IDs, enriches the two pre-existing
R37 case questions, and writes the case-coverage ledger used for QA.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LECTURES = Path("/Users/chriselwell/Desktop/Renal/Lectures")
BATCH = "lecture-case-expansion-2026-10-24"


def digest(value: str, size: int = 20) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]


def file_sha(document: str) -> str:
    path = LECTURES / document
    if not path.is_file():
        raise FileNotFoundError(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def citation(document: str, page: int) -> dict[str, Any]:
    return {"document": document, "page": page, "sha256": file_sha(document)}


def case(
    case_id: str,
    collection: str,
    document: str,
    page: int,
    answer_page: int,
    scenario: str,
    rows: list[list[str]],
    lead_in: str,
    correct: str,
    distractors: list[str],
    explanation: str,
    exclusion: str,
    clues: list[str],
    difficulty: str = "advanced",
    reasoning_type: str = "clinical_integration",
    note: str | None = None,
    extra_citations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if len(distractors) != 4:
        raise ValueError(f"{case_id}: exactly four distractors required")
    raw_options = [correct, *distractors]
    raw_rationales = [
        explanation,
        *[
            f"{option} does not account for the complete displayed pattern. {exclusion}"
            for option in distractors
        ],
    ]
    bank_kind = "physiology" if collection in {"R3", "R9", "R12"} else "pathology"
    ordinal = sum(1 for item in DEFINITIONS if item.get("bank_kind") == bank_kind) if "DEFINITIONS" in globals() else 0
    target_index = ordinal % 5
    options = raw_options[1 : target_index + 1] + [raw_options[0]] + raw_options[target_index + 1 :]
    rationales = raw_rationales[1 : target_index + 1] + [raw_rationales[0]] + raw_rationales[target_index + 1 :]
    qid = f"q-case-{digest(case_id)}"
    identity = digest(case_id, 16)
    citations = [citation(document, page)]
    if answer_page != page:
        citations.append(citation(document, answer_page))
    for item in extra_citations or []:
        if item not in citations:
            citations.append(item)
    table_note = note or "Values and findings are transcribed or faithfully condensed from the cited lecture case."
    return {
        "question_id": qid,
        "asset_id": f"table-{identity}",
        "source_group_id": f"case-{identity}",
        "source_id": f"lecture-case-{identity}",
        "variant_id": f"table-v1-{identity}",
        "question_type": "Clinical Data Integration",
        "tested_concept": correct,
        "stem": f"{scenario} {lead_in}",
        "visual_target": "Integrate the primary clinical data table with the case context to select the only fully concordant conclusion.",
        "visual_kind": "table",
        "joint_composite": False,
        "options": options,
        "correct_index": target_index,
        "choice_rationales": rationales,
        "explanation": explanation,
        "visual_clues": clues,
        "ground_truth_confidence": "high",
        "ground_truth_basis": f"Lecture case and answer on {document}, pp. {page} and {answer_page}.",
        "citations": citations,
        "category": "Clinical Data Table",
        "collection": collection,
        "source_origin": "lecture-table",
        "status": "USABLE",
        "case_context": scenario,
        "accepted_synonyms": [],
        "format_version": "clinical-visual-v1",
        "scenario": scenario,
        "lead_in": lead_in,
        "context_table": {
            "placement": "primary",
            "title": f"{collection} case data",
            "columns": ["Finding", "Value"],
            "rows": rows,
            "note": table_note,
            "source": citation(document, page),
        },
        "reasoning_type": reasoning_type,
        "difficulty": difficulty,
        "generation_batch": BATCH,
        "case_id": case_id,
        "bank_kind": bank_kind,
    }


DEFINITIONS: list[dict[str, Any]] = []


def add(**kwargs: Any) -> None:
    question = case(**kwargs)
    DEFINITIONS.append(question)


R3 = "R3 Filtration & GFR (Physiology) RLS.pdf"
add(
    case_id="R3-beginner-impaired-filtration",
    collection="R3", document=R3, page=36, answer_page=37,
    scenario="Two patients are compared during an evaluation of renal filtration.",
    rows=[["Patient A", "GFR 45 mL/min; creatinine 4.3 mg/dL; BUN 47 mg/dL; urine protein 1.5 g/day"], ["Patient B", "GFR 125 mL/min; creatinine 1.2 mg/dL; BUN 10 mg/dL; urine protein 0.10 g/day"]],
    lead_in="Which interpretation best integrates the filtration marker, retained solutes, and protein excretion?",
    correct="Patient A has impaired kidney filtration",
    distractors=["Patient B has impaired kidney filtration", "Both patients have preserved filtration", "Patient A has isolated proteinuria with normal filtration", "Patient B has reduced filtration masked by low BUN"],
    explanation="Patient A combines a markedly lower GFR with higher creatinine, higher BUN, and greater protein excretion, the lecture pattern of impaired kidney function.",
    exclusion="The low GFR and parallel accumulation of creatinine and BUN identify Patient A, whereas Patient B has the preserved-filtration pattern.",
    clues=["GFR is 45 versus 125 mL/min", "Creatinine and BUN rise as filtration falls"],
    difficulty="intermediate", reasoning_type="interpretation",
)
add(
    case_id="R3-expert-unilateral-obstruction",
    collection="R3", document=R3, page=38, answer_page=39,
    scenario="A 51-year-old woman has persistent partial obstruction of the left ureter after repair of an operative injury.",
    rows=[["Anatomic problem", "Partial left ureteral obstruction"], ["Pressure consequence", "Pressure transmitted backward through the pelvis and nephron"], ["Filtration equation", "SNGFR = Kf × (Pgc − PT − πgc)"]],
    lead_in="Which paired change is expected in the left kidney?",
    correct="Increased tubular hydrostatic pressure with decreased GFR",
    distractors=["Decreased tubular hydrostatic pressure with increased GFR", "Increased glomerular capillary pressure with increased GFR", "Decreased glomerular capillary pressure with unchanged GFR", "Unchanged tubular pressure with unchanged GFR"],
    explanation="Obstruction raises tubular hydrostatic pressure upstream, opposing glomerular filtration and lowering GFR in the affected kidney.",
    exclusion="The obstructed ureter raises rather than lowers tubular back pressure, and that pressure opposes rather than augments filtration.",
    clues=["Ureteral obstruction transmits pressure upstream", "PT is subtracted in the filtration equation"],
)

R9 = "R9 Acid-Base Regulation (Physiology) RLS.pdf"
add(
    case_id="R9-DKA-acid-defense",
    collection="R9", document=R9, page=36, answer_page=41,
    scenario="A 9-year-old with untreated type 1 diabetes has confusion, fruity breath, glucose 400 mg/dL, and pH 7.25.",
    rows=[["Glucose", "400 mg/dL"], ["Arterial pH", "7.25"], ["Primary acid source", "Keto acids from fatty-acid metabolism"], ["Clinical clue", "Fruity breath"]],
    lead_in="Which coordinated response profile best follows from the primary disturbance?",
    correct="Hyperventilation, increased renal H⁺ excretion, increased NH₄⁺ generation, and increased HCO₃⁻ reclamation",
    distractors=["Hypoventilation, reduced H⁺ excretion, and urinary HCO₃⁻ wasting", "Hyperventilation with reduced NH₄⁺ generation and alkaline urine", "Increased pCO₂ with increased urinary HCO₃⁻ excretion", "No respiratory response with isolated phosphate loss"],
    explanation="Keto acids consume bicarbonate; the lungs lower pCO₂ while the kidneys increase H⁺ excretion, NH₄⁺ generation, titratable acid excretion, and bicarbonate reclamation.",
    exclusion="The lecture describes coordinated buffer, lung, and kidney defenses rather than retention of CO₂ or urinary loss of bicarbonate.",
    clues=["Low pH follows fixed keto-acid generation", "Lung and kidney responses both reduce the acid burden"],
)

R12 = "R12 Acid-Base Case Studies Beginners (Physiology) RLS.pdf"
add(
    case_id="R12-case-1-shock",
    collection="R12", document=R12, page=13, answer_page=17,
    scenario="A trauma patient is in profound shock after blood loss.",
    rows=[["pH", "7.00"], ["pCO₂", "20 mm Hg"], ["HCO₃⁻", "5.0 mEq/L"], ["Anion gap", ">16 mEq/L"], ["BUN / creatinine / glucose", "Normal"]],
    lead_in="Which diagnosis and source of the unmeasured anion best integrate the data?",
    correct="High-anion-gap metabolic acidosis from lactic acid with respiratory compensation",
    distractors=["Ketoacidosis from uncontrolled diabetes with respiratory compensation", "Uremic acidosis from retained phosphoric and sulfuric acids", "Primary respiratory alkalosis from pain without metabolic disease", "Normal-anion-gap metabolic acidosis from bicarbonate loss"],
    explanation="Severe hypoperfusion drives anaerobic lactic-acid production; very low bicarbonate identifies metabolic acidosis and low pCO₂ is respiratory compensation.",
    exclusion="Normal glucose and renal markers argue against ketoacid or uremic accumulation, while shock directly explains lactate generation.",
    clues=["Profound hypovolemic shock", "Very low HCO₃⁻ with low compensatory pCO₂"],
)
add(
    case_id="R12-case-2-vomiting",
    collection="R12", document=R12, page=19, answer_page=32,
    scenario="An unknown patient has several days of pyloric-obstruction vomiting and volume contraction.",
    rows=[["pH", "7.50"], ["pCO₂", "48 mm Hg"], ["HCO₃⁻", "36.2 mEq/L"], ["Key losses", "Gastric H⁺, Cl⁻, K⁺, and fluid"]],
    lead_in="Which integrated diagnosis and treatment is most consistent with the lecture case?",
    correct="Volume-contraction metabolic alkalosis with respiratory compensation; replace Na⁺, K⁺, and Cl⁻ containing fluid",
    distractors=["Respiratory acidosis; increase ventilatory rate only", "Metabolic acidosis; give bicarbonate without volume", "Respiratory alkalosis; reduce inspired oxygen", "Uncompensated metabolic alkalosis; restrict sodium and water"],
    explanation="Vomiting removes gastric acid and chloride, while contraction sustains renal bicarbonate reclamation; the elevated pCO₂ is compensation and electrolyte-containing saline corrects the driver.",
    exclusion="The high bicarbonate is the primary change, and the source explicitly ties correction to stopping vomiting plus restoring sodium, potassium, chloride, and volume.",
    clues=["Alkalemia with disproportionately high HCO₃⁻", "Vomiting produces chloride and volume depletion"],
    difficulty="intermediate",
)
add(
    case_id="R12-case-3-pulmonary",
    collection="R12", document=R12, page=33, answer_page=39,
    scenario="A patient with pulmonary dysfunction has hypoxemia and the following arterial measurements.",
    rows=[["pH", "7.32"], ["pCO₂", "63 mm Hg"], ["HCO₃⁻", "31.9 mEq/L"], ["pO₂", "60 mm Hg"]],
    lead_in="Which diagnosis and organ compensation best explain all four values?",
    correct="Respiratory acidosis from CO₂ retention with renal bicarbonate compensation",
    distractors=["Metabolic acidosis with pulmonary CO₂ retention", "Respiratory alkalosis with renal bicarbonate generation", "Metabolic alkalosis from gastric acid loss", "A fully compensated disorder with normal acid-base status"],
    explanation="The primary abnormality is marked CO₂ retention with acidemia; elevated bicarbonate reflects renal compensation, and low pO₂ supports a pulmonary cause.",
    exclusion="A high rather than low pCO₂ drives the acidemia, and the bicarbonate direction is compensatory rather than the source of alkalemia.",
    clues=["pCO₂ is 63 mm Hg", "HCO₃⁻ rises while pH remains acidemic"],
    difficulty="intermediate",
)
add(
    case_id="R12-case-4-ventilator",
    collection="R12", document=R12, page=40, answer_page=46,
    scenario="An ICU patient is receiving mechanical ventilation with an excessive respiratory rate.",
    rows=[["pH", "7.50"], ["pCO₂", "30 mm Hg"], ["HCO₃⁻", "22.6 mEq/L"], ["pO₂", "260 mm Hg"]],
    lead_in="Which intervention targets the primary disturbance?",
    correct="Reduce ventilator-driven minute ventilation to correct acute respiratory alkalosis",
    distractors=["Increase minute ventilation to eliminate retained CO₂", "Infuse bicarbonate for primary metabolic acidosis", "Give chloride-rich fluid for vomiting-induced alkalosis", "Restrict ventilation until pCO₂ exceeds 50 mm Hg"],
    explanation="Excess mechanical ventilation lowers pCO₂ and raises pH; adjusting the respirator downward addresses the primary acute respiratory alkalosis.",
    exclusion="The primary abnormality is excessive CO₂ removal, not CO₂ retention, bicarbonate loss, or gastric acid loss.",
    clues=["Alkalemia with low pCO₂", "Very high pO₂ and ventilator context"],
)
add(
    case_id="R12-case-5-CKD",
    collection="R12", document=R12, page=47, answer_page=53,
    scenario="A patient with chronic glomerulonephritis has bilaterally contracted kidneys and creatinine 6.8 mg/dL.",
    rows=[["pH", "7.30"], ["pCO₂", "30 mm Hg"], ["HCO₃⁻", "11.9 mEq/L"], ["Functional nephrons", "Approximately 10% remain"]],
    lead_in="Which mechanism best explains the acid-base disorder and expected gap?",
    correct="Reduced filtration and excretion of fixed acids plus impaired HCO₃⁻ handling cause high-anion-gap metabolic acidosis",
    distractors=["Excess distal H⁺ secretion causes normal-gap metabolic alkalosis", "Isolated pulmonary CO₂ retention causes respiratory acidosis", "Gastric HCl loss causes chloride-responsive metabolic alkalosis", "Increased ammonium generation in damaged nephrons causes alkalemia"],
    explanation="Advanced nephron loss impairs fixed-acid filtration and H⁺ excretion as well as bicarbonate reclamation and generation, producing metabolic acidosis with retained unmeasured anions.",
    exclusion="The source identifies broad loss of renal acid-handling capacity, not acid overexcretion, gastric loss, or an isolated lung disorder.",
    clues=["Creatinine 6.8 mg/dL with contracted kidneys", "Low HCO₃⁻ and compensatory low pCO₂"],
)
add(
    case_id="R12-case-6-Fanconi",
    collection="R12", document=R12, page=54, answer_page=61,
    scenario="A child has aminoaciduria, renal glycosuria, and normal serum creatinine.",
    rows=[["pH", "7.30"], ["pCO₂", "29 mm Hg"], ["HCO₃⁻", "13.8 mEq/L"], ["Na⁺ / Cl⁻", "139 / 116 mEq/L"], ["Anion gap", "9 mEq/L"], ["Urine pH", "7.0"]],
    lead_in="Which lesion unifies the solute losses and acid-base pattern?",
    correct="Proximal tubular dysfunction causing Fanconi syndrome with renal tubular acidosis",
    distractors=["Advanced glomerular failure with retention of fixed acids", "Vomiting with chloride-responsive metabolic alkalosis", "Primary respiratory acidosis from hypoventilation", "Diabetic ketoacidosis from insulin deficiency"],
    explanation="Normal filtration with glycosuria, aminoaciduria, bicarbonate loss, hyperchloremic normal-gap acidosis, and inappropriately alkaline urine identifies proximal tubular dysfunction and Fanconi-associated RTA.",
    exclusion="The normal creatinine and normal anion gap point away from glomerular failure or ketoacids, while the low bicarbonate excludes vomiting alkalosis.",
    clues=["Glycosuria and aminoaciduria despite normal creatinine", "Normal anion gap with bicarbonate loss"],
)
add(
    case_id="R12-case-7-salicylate",
    collection="R12", document=R12, page=63, answer_page=66,
    scenario="An 18-year-old takes a massive aspirin overdose and develops deep, rapid breathing.",
    rows=[["pH", "7.47"], ["pCO₂", "14 mm Hg"], ["HCO₃⁻", "9 mEq/L"], ["Anion gap", "27 mEq/L"]],
    lead_in="Which mixed disorder accounts for the direction and magnitude of all values?",
    correct="Respiratory alkalosis plus high-anion-gap metabolic acidosis from salicylate toxicity",
    distractors=["Pure respiratory alkalosis with appropriate bicarbonate compensation", "Pure high-anion-gap metabolic acidosis with appropriate hyperventilation", "Metabolic alkalosis plus respiratory acidosis", "Normal-gap metabolic acidosis plus chronic respiratory acidosis"],
    explanation="Salicylate stimulates ventilation, sharply lowering pCO₂, while organic-acid generation lowers bicarbonate and raises the anion gap; the alkalemic pH reflects the mixed process.",
    exclusion="Bicarbonate is far lower than expected for an isolated respiratory alkalosis, while the very low pCO₂ is too prominent for a lone metabolic acidosis.",
    clues=["pCO₂ 14 mm Hg indicates strong respiratory alkalosis", "HCO₃⁻ 9 mEq/L and gap 27 indicate added metabolic acidosis"],
)


R23 = "R23 Fluid Regulation Disorders (Pathophysiology) PQ.pdf"
add(
    case_id="R23-PQ-1-poor-intake",
    collection="R23", document=R23, page=1, answer_page=3,
    scenario="A 72-year-old has poor fluid intake, no gastrointestinal losses, and serum sodium 151 mEq/L.",
    rows=[["Fluid intake", "Poor"], ["GI losses", "None"], ["Serum Na⁺", "151 mEq/L"]],
    lead_in="Which compartment disturbance best explains this pattern?",
    correct="Free-water loss causing hypertonic volume contraction",
    distractors=["Isotonic sodium loss causing isosmotic contraction", "Hypotonic sodium loss causing hypotonic contraction", "Excess isotonic saline causing isosmotic expansion", "Pure intracellular solute gain without water loss"],
    explanation="Absent intake produces a water deficit relative to sodium, raising serum sodium and tonicity while contracting body water.",
    exclusion="The elevated sodium requires a relative water deficit rather than an isotonic loss or isotonic gain.",
    clues=["Serum sodium is 151 mEq/L", "Poor intake occurs without sodium-rich GI loss"],
    difficulty="intermediate", reasoning_type="interpretation",
)
add(
    case_id="R23-PQ-2-isotonic-diarrhea",
    collection="R23", document=R23, page=1, answer_page=3,
    scenario="A 24-year-old has acute watery diarrhea whose lost fluid is isotonic to plasma.",
    rows=[["Loss", "Isotonic diarrheal fluid"], ["ECF volume", "Falls"], ["Serum tonicity", "No primary change"]],
    lead_in="Which paired compartment response follows?",
    correct="ECF volume decreases while ICF volume and tonicity remain unchanged",
    distractors=["ECF and ICF volumes both decrease as tonicity rises", "ECF volume decreases while ICF expands from hypertonicity", "ECF expands while ICF contracts", "Both compartments expand despite the external fluid loss"],
    explanation="An isotonic loss removes volume from ECF without creating an osmotic gradient, so water does not redistribute across cell membranes.",
    exclusion="Without a change in effective osmolality, there is no reason for ICF water to shift.",
    clues=["The lost fluid is isotonic", "Only the extracellular compartment directly loses volume"],
    difficulty="intermediate", reasoning_type="mechanism",
)
add(
    case_id="R23-PQ-3-vomiting-low-urine-sodium",
    collection="R23", document=R23, page=1, answer_page=3,
    scenario="A patient with prolonged vomiting develops orthostasis and tachycardia but retains intact renal function.",
    rows=[["Loss", "Vomiting"], ["Hemodynamics", "Orthostasis and tachycardia"], ["Kidney function", "Intact"]],
    lead_in="Which urine sodium response and mechanism are expected?",
    correct="Low urine Na⁺ from increased tubular sodium reabsorption triggered by reduced effective arterial blood volume",
    distractors=["High urine Na⁺ from pressure natriuresis during volume expansion", "High urine Na⁺ because ADH directly blocks sodium reabsorption", "Unchanged urine Na⁺ because only water balance responds", "Low urine Na⁺ from reduced aldosterone secretion"],
    explanation="Volume contraction lowers effective arterial blood volume and activates sodium-retaining responses, producing low urinary sodium when the kidneys are intact.",
    exclusion="Orthostasis and tachycardia indicate contraction rather than expansion, and intact kidneys should conserve rather than waste sodium.",
    clues=["Orthostasis and tachycardia signal low effective volume", "Renal sodium conservation is intact"],
    difficulty="intermediate", reasoning_type="mechanism",
)
add(
    case_id="R23-PQ-4-urea-osmolality",
    collection="R23", document=R23, page=1, answer_page=3,
    scenario="A patient has normal serum sodium but a markedly elevated BUN and elevated measured serum osmolality.",
    rows=[["Serum Na⁺", "140 mEq/L"], ["BUN", "Markedly elevated"], ["Measured osmolality", "Elevated"]],
    lead_in="How should the elevated measured osmolality be interpreted?",
    correct="Hyperosmolality without equivalent hypertonicity because urea is an ineffective osmole",
    distractors=["Hypertonicity that must shrink cells because urea remains extracellular", "Hypotonicity caused by sodium dilution", "Normal osmolality because BUN never enters the calculation", "Pseudohyperosmolality caused by laboratory sodium error"],
    explanation="Urea raises measured osmolality but readily crosses cell membranes, so it contributes little sustained transcellular water gradient and is an ineffective osmole.",
    exclusion="Normal sodium and the identified urea elevation distinguish measured hyperosmolality from effective hypertonicity.",
    clues=["Sodium remains 140 mEq/L", "BUN is the added measured osmole"],
    difficulty="intermediate", reasoning_type="interpretation",
)
add(
    case_id="R23-PQ-5-water-deprivation",
    collection="R23", document=R23, page=2, answer_page=3,
    scenario="A healthy person is deprived of water long enough for serum sodium to rise from 140 to 152 mEq/L.",
    rows=[["Initial Na⁺", "140 mEq/L"], ["Later Na⁺", "152 mEq/L"], ["Water access", "None"]],
    lead_in="Which coordinated response best defends tonicity and volume?",
    correct="Increased thirst and ADH with reduced urine volume and increased urine concentration",
    distractors=["Suppressed thirst and ADH with dilute polyuria", "Increased ADH with increased free-water excretion", "Suppressed ADH with concentrated oliguria", "Increased aldosterone alone with no change in water handling"],
    explanation="Hypernatremia raises tonicity, stimulating thirst and ADH; collecting-duct water reabsorption rises, urine concentrates, and urine volume falls.",
    exclusion="The response must conserve water and increase intake rather than promote dilute water loss.",
    clues=["Sodium rises during water deprivation", "Tonicity-sensitive thirst and ADH act together"],
)
add(
    case_id="R23-PQ-6-prerenal-bun-creatinine",
    collection="R23", document=R23, page=2, answer_page=3,
    scenario="A patient with gastrointestinal fluid loss develops prerenal kidney injury and a high BUN-to-creatinine ratio.",
    rows=[["Volume status", "Contracted"], ["Renal state", "Prerenal injury"], ["BUN:creatinine", "Elevated"]],
    lead_in="Which tubular response most directly explains the disproportionate BUN rise?",
    correct="Increased proximal sodium and water reabsorption with increased passive urea reabsorption",
    distractors=["Reduced proximal sodium reabsorption with increased urea secretion", "Isolated creatinine reabsorption without urea handling", "Pressure natriuresis with reduced water reclamation", "Collecting-duct bicarbonate secretion causing urea trapping"],
    explanation="Low perfusion increases proximal sodium and water reclamation; urea follows and returns to blood, raising BUN disproportionately to creatinine.",
    exclusion="Prerenal conservation increases rather than decreases proximal reabsorption, and creatinine is not reclaimed in the same manner.",
    clues=["Volume contraction is prerenal", "Urea reabsorption accompanies water conservation"],
)
add(
    case_id="R23-PQ-7-maximal-urine-concentration",
    collection="R23", document=R23, page=2, answer_page=4,
    scenario="After water deprivation, urine osmolality approaches 1200 mOsm/kg.",
    rows=[["Water status", "Deprived"], ["Urine osmolality", "Approximately 1200 mOsm/kg"]],
    lead_in="Which collecting-duct change is required for this result?",
    correct="ADH-dependent increase in collecting-duct water permeability",
    distractors=["Suppression of aquaporin insertion in principal cells", "Complete loss of the medullary osmotic gradient", "Inhibition of urea recycling with reduced interstitial osmolality", "ADH-independent water secretion by intercalated cells"],
    explanation="Water deprivation increases ADH, which makes the collecting duct water permeable so tubular water can equilibrate with the hyperosmotic medulla.",
    exclusion="A concentrated urine requires preserved medullary gradient and increased, not decreased, ADH-dependent water permeability.",
    clues=["Urine reaches near-maximal osmolality", "Water deprivation stimulates ADH"],
)
add(
    case_id="R23-PQ-8-diarrhea-eabv",
    collection="R23", document=R23, page=2, answer_page=4,
    scenario="Severe diarrhea lowers blood pressure while serum sodium remains unchanged.",
    rows=[["Loss", "Severe diarrhea"], ["Blood pressure", "Decreased"], ["Serum Na⁺", "Unchanged"]],
    lead_in="Which homeostatic response is most appropriate despite the unchanged sodium concentration?",
    correct="Reduced effective arterial blood volume stimulates renal sodium retention",
    distractors=["Normal sodium suppresses all volume-regulatory pathways", "Pressure expansion triggers natriuresis", "High tonicity suppresses sodium reabsorption", "Increased effective arterial volume stimulates renin release"],
    explanation="Serum sodium is a concentration, not a direct volume measure; hypotension from ECF loss lowers effective arterial blood volume and activates sodium retention.",
    exclusion="The hemodynamic signal is contraction even though sodium concentration is normal.",
    clues=["Blood pressure falls", "Serum sodium can stay normal during isotonic loss"],
)
add(
    case_id="R23-PQ-9-nonosmotic-ADH",
    collection="R23", document=R23, page=2, answer_page=4,
    scenario="A patient has substantial ECF depletion, low plasma osmolality, and an elevated ADH level.",
    rows=[["ECF volume", "Substantially depleted"], ["Plasma osmolality", "Low"], ["ADH", "Elevated"]],
    lead_in="Why is ADH not suppressed by the low osmolality?",
    correct="A nonosmotic low-effective-volume signal overrides osmotic suppression of ADH",
    distractors=["Low osmolality directly stimulates hypothalamic osmoreceptors", "ADH secretion is independent of both volume and osmolality", "High effective arterial volume activates baroreceptor ADH release", "Aldosterone blocks ADH suppression at the collecting duct"],
    explanation="Severe effective-volume depletion is a powerful nonosmotic stimulus for ADH and can override the usual suppression expected at low plasma osmolality.",
    exclusion="Low osmolality alone would suppress ADH, so the severe volume signal is required to explain the discordance.",
    clues=["ADH is high despite low osmolality", "ECF depletion is substantial"],
)
add(
    case_id="R23-PQ-10-free-water-versus-isotonic-loss",
    collection="R23", document=R23, page=2, answer_page=4,
    scenario="Two patients lose the same volume, one as free water and the other as isotonic fluid.",
    rows=[["Patient 1", "Free-water loss"], ["Patient 2", "Equal-volume isotonic loss"]],
    lead_in="Which comparison best predicts the dominant consequences?",
    correct="Isotonic loss causes greater ECF and effective-volume depletion, while free-water loss raises tonicity and contracts cells",
    distractors=["Free-water loss causes greater isolated ECF depletion without changing tonicity", "Isotonic loss raises tonicity and causes intracellular contraction", "Both losses produce identical ECF and ICF changes", "Free-water loss expands cells while isotonic loss expands ECF"],
    explanation="Isotonic loss is confined to ECF and produces stronger orthostatic hemodynamic effects; free-water loss distributes across compartments, increases tonicity, and draws water from cells.",
    exclusion="Only free-water loss changes tonicity, while isotonic loss disproportionately reduces the vascular extracellular compartment.",
    clues=["Isotonic fluid is lost only from ECF", "Free-water loss increases extracellular tonicity"],
)


R24 = "R24 Electrolyte Disorders (Pathophysiology) PQs.pdf"
add(
    case_id="R24-PQ-1-vomiting-hyponatremia",
    collection="R24", document=R24, page=1, answer_page=3,
    scenario="A vomiting patient is hypotensive with sodium 121 mEq/L, glucose 92 mg/dL, and BUN:creatinine 24.",
    rows=[["BP", "94/58 mm Hg"], ["Na⁺", "121 mEq/L"], ["Glucose", "92 mg/dL"], ["BUN:creatinine", "24"]],
    lead_in="Which mechanism best integrates the hypotonic hyponatremia and volume findings?",
    correct="Sodium-containing fluid loss with volume-contraction–driven nonosmotic ADH retention of water",
    distractors=["Hyperglycemic water shift from ICF to ECF", "Pseudohyponatremia from excess plasma protein", "Primary polydipsia with maximally dilute urine", "Sodium gain with proportionally greater water loss"],
    explanation="Vomiting contracts ECF, and the low effective-volume signal sustains ADH-mediated water retention, lowering sodium despite ongoing sodium conservation.",
    exclusion="Normal glucose and evidence of contraction favor hypovolemic hypotonic hyponatremia rather than translocational or pseudohyponatremia.",
    clues=["BUN:creatinine 24 supports contraction", "Glucose is normal"],
    difficulty="intermediate",
)
add(
    case_id="R24-PQ-2-saline-treatment",
    collection="R24", document=R24, page=1, answer_page=3,
    scenario="The volume-contracted vomiting patient in question 1 requires correction of the stimulus sustaining ADH.",
    rows=[["Na⁺", "121 mEq/L"], ["Hemodynamics", "Hypotensive and volume contracted"], ["Primary driver", "Gastrointestinal sodium and water loss"]],
    lead_in="Which initial fluid best treats the underlying physiology?",
    correct="0.9% sodium chloride",
    distractors=["Free water by mouth alone", "D5W as the sole initial infusion", "3% sodium chloride for every case of Na⁺ 121", "Fluid restriction without volume replacement"],
    explanation="Isotonic saline restores effective arterial blood volume, removes the nonosmotic ADH stimulus, and replaces sodium-containing extracellular loss.",
    exclusion="The primary problem is hypovolemia, so free water or restriction fails to restore effective arterial volume, while routine hypertonic saline is not the source answer.",
    clues=["Volume contraction is the treatment target", "The loss originates in extracellular fluid"],
    difficulty="intermediate", reasoning_type="clinical_integration",
)
add(
    case_id="R24-PQ-3-hyperglycemic-hyponatremia",
    collection="R24", document=R24, page=1, answer_page=3,
    scenario="A hyperglycemic patient has sodium 128 mEq/L but elevated serum tonicity.",
    rows=[["Glucose", "Markedly elevated"], ["Na⁺", "128 mEq/L"], ["Serum tonicity", "Elevated"]],
    lead_in="Which water shift explains the sodium concentration?",
    correct="Glucose raises ECF tonicity, drawing water from ICF and diluting extracellular sodium",
    distractors=["Glucose lowers ECF tonicity, moving water into cells", "Protein displaces plasma water without changing tonicity", "Renal sodium loss is proven solely by the sodium value", "Urea traps water inside cells and raises intracellular volume"],
    explanation="Extracellular glucose is an effective osmole in this setting, pulling water out of cells and lowering measured sodium while overall tonicity remains high.",
    exclusion="The elevated tonicity rules out ordinary hypotonic hyponatremia and points to a transcellular water shift.",
    clues=["Hyponatremia coexists with high tonicity", "Marked hyperglycemia supplies an effective extracellular osmole"],
)
add(
    case_id="R24-PQ-4-myeloma-pseudohyponatremia",
    collection="R24", document=R24, page=1, answer_page=3,
    scenario="A patient with multiple myeloma has sodium 129 mEq/L and normal measured serum osmolality.",
    rows=[["Diagnosis", "Multiple myeloma"], ["Na⁺", "129 mEq/L"], ["Measured osmolality", "Normal"]],
    lead_in="Which classification best fits this sodium result?",
    correct="Isotonic pseudohyponatremia from increased nonaqueous plasma fraction",
    distractors=["Hypotonic hyponatremia from excess ADH", "Hypertonic hyponatremia from glucose", "True sodium depletion with obligatory low osmolality", "Hypernatremia masked by renal water loss"],
    explanation="High plasma protein can reduce the sampled plasma-water fraction and artifactually lower reported sodium while measured osmolality remains normal.",
    exclusion="True hypotonic or hypertonic disorders would not preserve normal measured osmolality in this source pattern.",
    clues=["Multiple myeloma implies high plasma protein", "Measured osmolality is normal"],
)
add(
    case_id="R24-PQ-5-CHF-hyponatremia",
    collection="R24", document=R24, page=2, answer_page=3,
    scenario="A patient with congestive heart failure has edema and sodium 126 mEq/L.",
    rows=[["Clinical state", "Congestive heart failure"], ["Edema", "Present"], ["Na⁺", "126 mEq/L"]],
    lead_in="Which statement correctly reconciles edema with the sodium concentration?",
    correct="Total body sodium is increased, but water is increased more because low effective arterial volume sustains ADH",
    distractors=["Total body sodium must be depleted whenever serum sodium is low", "Edema proves effective arterial volume is high and ADH is suppressed", "Serum sodium directly measures the total sodium content of the body", "Hyponatremia requires loss of both sodium and all extracellular water"],
    explanation="Heart failure can expand total ECF sodium and water while underfilling the effective arterial circulation; nonosmotic ADH adds proportionally more water and lowers sodium concentration.",
    exclusion="Edema reflects total extracellular expansion, whereas renal sensors respond to low effective arterial filling and serum sodium remains a concentration.",
    clues=["Edema indicates increased total extracellular content", "Heart failure lowers effective arterial filling"],
)
add(
    case_id="R24-PQ-6-sodium-concentration",
    collection="R24", document=R24, page=2, answer_page=4,
    scenario="A learner concludes that the edematous heart-failure patient must have low total body sodium because serum sodium is 128 mEq/L.",
    rows=[["Edema", "Present"], ["Serum Na⁺", "128 mEq/L"], ["Heart failure", "Present"]],
    lead_in="What is the key conceptual correction?",
    correct="Serum Na⁺ reports sodium relative to water, not total body sodium content",
    distractors=["Serum Na⁺ is a direct inventory of all exchangeable body sodium", "Edema occurs only when total body sodium is low", "Serum Na⁺ is determined only by aldosterone concentration", "Water balance cannot change serum Na⁺ unless sodium is excreted"],
    explanation="The concentration can be low even when total sodium is increased if total water has increased disproportionately, as in edematous heart failure.",
    exclusion="The displayed combination of edema and low sodium is possible precisely because concentration and total content are different quantities.",
    clues=["Edema indicates retained sodium and water", "The denominator of sodium concentration is body water"],
)
add(
    case_id="R24-PQ-7-low-solute-intake",
    collection="R24", document=R24, page=2, answer_page=4,
    scenario="A patient consumes tea and water with very little dietary solute and has no signs of volume contraction.",
    rows=[["Diet", "Tea, water, and very little solute"], ["Volume contraction", "Absent"], ["Serum Na⁺", "Low"]],
    lead_in="Which renal constraint allows water intake to produce hyponatremia?",
    correct="Low daily osmole excretion limits the maximum volume of dilute urine that can be excreted",
    distractors=["High solute intake prevents the kidney from diluting urine", "Volume contraction is required for every form of hyponatremia", "Aldosterone directly forces unlimited free-water retention", "High protein intake lowers the renal excretory water ceiling"],
    explanation="Even with dilute urine, excreting ingested water requires osmoles; a very low solute load caps daily water excretion and permits dilutional hyponatremia.",
    exclusion="The case explicitly lacks contraction and instead identifies limited solute as the bottleneck to free-water clearance.",
    clues=["Very low dietary solute", "No evidence of low effective arterial volume"],
)
add(
    case_id="R24-PQ-8-brain-swelling",
    collection="R24", document=R24, page=2, answer_page=4,
    scenario="A patient with severe hypotonic hyponatremia develops neurologic symptoms.",
    rows=[["Serum disorder", "Severe hypotonic hyponatremia"], ["Symptoms", "Neurologic"]],
    lead_in="Which immediate transcellular event produces the neurologic risk?",
    correct="Water moves from hypotonic ECF into brain cells, causing cellular swelling",
    distractors=["Water leaves brain cells because ECF tonicity is high", "Sodium enters neurons and directly contracts them", "Urea remains extracellular and causes isolated hypertonicity", "Water distribution stays fixed because sodium cannot affect tonicity"],
    explanation="Low effective extracellular osmolality drives water into cells; in the fixed cranial vault, brain swelling produces the neurologic danger.",
    exclusion="The direction of water movement must be into, not out of, cells when ECF is hypotonic.",
    clues=["The hyponatremia is explicitly hypotonic", "Neurologic symptoms point to brain-cell swelling"],
)
add(
    case_id="R24-PQ-9-D5W-distribution",
    collection="R24", document=R24, page=2, answer_page=4,
    scenario="One liter of D5W is infused and the glucose is metabolized, leaving free water.",
    rows=[["Infusate", "1 L D5W"], ["After metabolism", "Effectively free water"]],
    lead_in="How is the retained water distributed at equilibrium?",
    correct="Approximately two thirds enters ICF and one third remains in ECF",
    distractors=["All remains in the vascular compartment", "All remains in ECF because glucose was initially extracellular", "Approximately two thirds remains in ECF and one third enters ICF", "Equal one-half volumes enter ICF and ECF"],
    explanation="Once glucose is metabolized, the water distributes across total body water, approximately two thirds intracellular and one third extracellular.",
    exclusion="Free water is not confined to plasma or ECF and follows the normal relative sizes of ICF and ECF.",
    clues=["Metabolized D5W behaves as free water", "ICF is the larger body-water compartment"],
    difficulty="intermediate", reasoning_type="calculation",
)
add(
    case_id="R24-PQ-10-hypernatremia-two-axis",
    collection="R24", document=R24, page=2, answer_page=4,
    scenario="An older adult with decreased intake has sodium 154 mEq/L.",
    rows=[["Age", "Older adult"], ["Water intake", "Decreased"], ["Serum Na⁺", "154 mEq/L"]],
    lead_in="Which assessment framework avoids conflating tonicity with volume status?",
    correct="Classify the patient as hypertonic, then assess ECF volume independently from examination and losses",
    distractors=["Assume hypervolemia solely because sodium is high", "Assume hypovolemia solely because sodium is high", "Treat sodium concentration as a direct measure of total body sodium", "Ignore tonicity and classify only by edema"],
    explanation="Hypernatremia establishes hypertonicity, but ECF volume depends on the accompanying sodium and water balance and must be assessed separately.",
    exclusion="A sodium concentration alone does not uniquely determine total extracellular volume.",
    clues=["Na⁺ 154 mEq/L establishes hypertonicity", "Intake history suggests water deficit but volume still needs independent assessment"],
)


R27 = "R27 Fluid Imbalance Case Studies (Clinical) RLS.pdf"
add(
    case_id="R27-RLS-case-1-diarrhea",
    collection="R27", document=R27, page=2, answer_page=10,
    scenario="A patient with severe diarrhea has orthostasis and concentrated urine.",
    rows=[["Na⁺ / K⁺ / Cl⁻ / HCO₃⁻", "139 / 3.2 / 110 / 19 mEq/L"], ["BUN / creatinine", "22 / 1.2 mg/dL"], ["Urine osmolality", "800 mOsm/kg"], ["Urine Na⁺", "10 mEq/L"]],
    lead_in="Which integrated diagnosis and replacement plan best fits the case?",
    correct="Isotonic volume contraction with low-effective-volume sodium conservation, hyperchloremic acidosis, and potassium loss; give saline plus potassium",
    distractors=["SIADH with euvolemia; restrict water only", "Hypertonic dehydration from isolated free-water loss; give D5W only", "Primary mineralocorticoid excess; restrict sodium and potassium", "Nephrogenic diabetes insipidus; give desmopressin"],
    explanation="Diarrheal isotonic loss causes ECF contraction, low urine sodium and high urine osmolality; bicarbonate and potassium loss account for the hyperchloremic acidosis and hypokalemia.",
    exclusion="The urine shows intact volume conservation, while the serum chloride, bicarbonate, and potassium pattern follows gastrointestinal loss.",
    clues=["Urine Na⁺ 10 with urine osmolality 800", "HCO₃⁻ 19, Cl⁻ 110, and K⁺ 3.2"],
)
add(
    case_id="R27-RLS-case-2-heart-failure",
    collection="R27", document=R27, page=11, answer_page=18,
    scenario="A patient with decompensated heart failure has edema, jugular venous distention, rales, an S3, and low cardiac output.",
    rows=[["Serum Na⁺", "127 mEq/L"], ["Total ECF", "Expanded with edema"], ["Effective arterial volume", "Reduced by low cardiac output"], ["Exam", "JVD, rales, S3"]],
    lead_in="Which hormonal and body-content pattern reconciles the findings?",
    correct="Total sodium and water are increased, but low effective arterial volume activates RAAS and ADH so water gain exceeds sodium gain",
    distractors=["Total sodium and water are both depleted because edema proves intravascular loss", "High effective arterial volume suppresses RAAS while ADH alone causes edema", "Isolated sodium loss produces edema without water retention", "Primary polydipsia explains JVD, rales, and the S3"],
    explanation="Heart failure expands total extracellular content but underfills the effective arterial circulation, driving sodium-retaining RAAS and water-retaining ADH responses.",
    exclusion="The congestive exam proves total volume expansion, while low output explains why renal volume sensors still signal underfilling.",
    clues=["Congestive signs indicate expanded ECF", "Low cardiac output lowers effective arterial filling"],
)
add(
    case_id="R27-RLS-case-3-diarrhea-plus-water",
    collection="R27", document=R27, page=19, answer_page=24,
    scenario="A patient with diarrhea replaces losses with copious plain water and remains orthostatic.",
    rows=[["GI loss", "Diarrhea"], ["Replacement", "Copious free water"], ["Serum Na⁺", "130 mEq/L"], ["Hemodynamics", "Orthostatic"]],
    lead_in="Which diagnosis and initial therapy address the dominant physiology?",
    correct="Hypovolemic hypotonic hyponatremia; restore ECF with isotonic saline",
    distractors=["Euvolemic SIADH; restrict all sodium", "Hypervolemic hyponatremia; intensify free-water intake", "Hypertonic hyponatremia from glucose; give insulin only", "Pseudohyponatremia; no volume treatment is needed"],
    explanation="Diarrhea contracts ECF, while replacement with solute-free water lowers sodium; isotonic saline restores effective volume and removes the nonosmotic ADH drive.",
    exclusion="Orthostasis demonstrates true volume contraction, which is absent in SIADH and pseudohyponatremia.",
    clues=["Orthostasis identifies hypovolemia", "Free-water replacement dilutes sodium"],
)
add(
    case_id="R27-RLS-case-4-HHS",
    collection="R27", document=R27, page=26, answer_page=31,
    scenario="An obese patient with diabetes, fever, polyuria, and severe volume depletion presents with hyperosmolar hyperglycemia.",
    rows=[["Glucose", "1600 mg/dL"], ["Serum Na⁺", "135 mEq/L"], ["Serum osmolality", "368 mOsm/kg"], ["Volume status", "Severely depleted"]],
    lead_in="Which initial interpretation and treatment sequence is safest?",
    correct="Hypertonic volume depletion from HHS; begin isotonic saline before insulin",
    distractors=["True hypotonic hyponatremia; give free water before restoring circulation", "Pseudohyponatremia; withhold fluid because sodium is normal", "SIADH; restrict fluid and give no saline", "Primary hyperaldosteronism; start spironolactone before volume"],
    explanation="Extreme glucose raises effective osmolality and osmotic diuresis depletes volume; circulation is restored with saline before insulin shifts glucose and water.",
    exclusion="The measured sodium does not negate the severe hypertonicity and volume loss created by glucose and osmotic diuresis.",
    clues=["Glucose 1600 and osmolality 368", "Polyuria with severe volume depletion"],
)
add(
    case_id="R27-RLS-case-5-TB-SIADH",
    collection="R27", document=R27, page=32, answer_page=40,
    scenario="A patient with tuberculosis symptoms and confusion appears euvolemic.",
    rows=[["Serum osmolality", "250 mOsm/kg"], ["Serum tonicity", "248 mOsm/kg"], ["Urine osmolality", "750 mOsm/kg"], ["Volume exam", "Euvolemic"]],
    lead_in="Which diagnosis is supported by the urine response to the hypotonic plasma?",
    correct="SIADH with inappropriately concentrated urine",
    distractors=["Primary polydipsia with maximally dilute urine", "Central diabetes insipidus with dilute polyuria", "Hypovolemic sodium loss with orthostasis", "Pseudohyponatremia with normal tonicity"],
    explanation="True hypotonicity should suppress ADH and dilute urine; urine osmolality 750 in a clinically euvolemic patient is inappropriate and supports SIADH.",
    exclusion="The urine is concentrated rather than dilute, and measured tonicity confirms a true hypotonic disorder.",
    clues=["Tonicity 248 confirms hypotonicity", "Urine osmolality 750 is inappropriately high"],
)
add(
    case_id="R27-RLS-case-6-isotonic-versus-sweat",
    collection="R27", document=R27, page=41, answer_page=46,
    scenario="Two patients lose one liter, one through isotonic diarrhea and one through hypotonic sweat.",
    rows=[["Patient A", "1 L isotonic diarrheal fluid"], ["Patient B", "1 L hypotonic sweat"]],
    lead_in="Which comparison correctly identifies the compartment consequences?",
    correct="Patient A has greater isolated ECF and effective-volume loss; Patient B develops hypertonicity with water leaving cells",
    distractors=["Patient A develops hypertonicity and cellular contraction; Patient B loses only ECF", "Both patients have identical ECF, ICF, and tonicity changes", "Patient A has intracellular swelling; Patient B has isosmotic expansion", "Patient B has hypotonicity with intracellular swelling despite hypotonic fluid loss"],
    explanation="Isotonic diarrhea contracts only ECF, whereas hypotonic sweat removes proportionally more water, raises ECF tonicity, and draws water from ICF.",
    exclusion="The solute concentration of the lost fluid determines whether tonicity changes and whether ICF participates.",
    clues=["Diarrheal fluid is isotonic", "Sweat is hypotonic relative to plasma"],
)


R27N = "R27 Fluid Imbalance Case Studies (Clinical) Hyponatremia.pdf"
add(
    case_id="R27-hyponatremia-1-D5W",
    collection="R27", document=R27N, page=19, answer_page=20,
    scenario="A postoperative patient receives substantial D5W and remains clinically euvolemic.",
    rows=[["Infusate", "D5W"], ["Serum Na⁺", "124 mEq/L"], ["Serum osmolality", "249 mOsm/kg"], ["Volume exam", "Euvolemic"]],
    lead_in="Which exposure most directly created the electrolyte pattern?",
    correct="Excess electrolyte-free water delivered as metabolized D5W",
    distractors=["Hypertonic saline causing sodium dilution", "Isotonic saline causing free-water gain", "Loop diuretic causing isolated sodium retention", "Pseudohyponatremia from high plasma protein"],
    explanation="After dextrose metabolism, D5W supplies free water; sufficient administration dilutes extracellular sodium and osmolality without requiring a sodium deficit.",
    exclusion="The measured osmolality is genuinely low and the named infusion becomes free water rather than isotonic or hypertonic saline.",
    clues=["D5W becomes free water", "Na⁺ 124 with osmolality 249"],
)
add(
    case_id="R27-hyponatremia-2-vomiting",
    collection="R27", document=R27N, page=21, answer_page=22,
    scenario="A 22-year-old has several days of vomiting and is clinically volume depleted.",
    rows=[["Na⁺ / K⁺", "123 / 2.8 mEq/L"], ["Serum osmolality", "261 mOsm/kg"], ["HCO₃⁻", "37 mEq/L"], ["pH", "7.53"], ["Urine osmolality / Na⁺", "820 mOsm/kg / 18 mEq/L"]],
    lead_in="Which combined diagnosis best fits the serum and urine data?",
    correct="Hypovolemic hypotonic hyponatremia with vomiting-induced metabolic alkalosis",
    distractors=["Euvolemic SIADH with metabolic acidosis", "Hypertonic hyponatremia from glucose with respiratory alkalosis", "Pseudohyponatremia with normal acid-base status", "Nephrogenic diabetes insipidus with dilute urine"],
    explanation="Vomiting causes ECF loss, hypokalemic alkalosis, and a nonosmotic ADH signal; low urine sodium and concentrated urine show intact volume conservation.",
    exclusion="The physical contraction, alkalemia, high bicarbonate, and low urine sodium are not explained by SIADH or water diuresis.",
    clues=["pH 7.53 and HCO₃⁻ 37", "Urine Na⁺ 18 with osmolality 820"],
)
add(
    case_id="R27-hyponatremia-3-thiazide",
    collection="R27", document=R27N, page=23, answer_page=24,
    scenario="A patient taking hydrochlorothiazide develops sodium 128 mEq/L that normalizes after the drug is stopped.",
    rows=[["Drug", "Hydrochlorothiazide"], ["Serum Na⁺ on drug", "128 mEq/L"], ["After withdrawal", "Sodium normalizes"]],
    lead_in="Which causal interpretation is most strongly supported by the dechallenge?",
    correct="Thiazide-associated hyponatremia",
    distractors=["Persistent SIADH unrelated to medication", "Pseudohyponatremia from plasma protein", "Central diabetes insipidus", "Primary hyperaldosteronism"],
    explanation="The sodium abnormality appears during thiazide exposure and resolves when hydrochlorothiazide is removed, directly supporting drug-associated hyponatremia.",
    exclusion="The temporal reversal with medication withdrawal argues against a persistent endocrine or laboratory-artifact explanation.",
    clues=["Active thiazide exposure", "Normalization after the drug is stopped"],
    difficulty="intermediate", reasoning_type="clinical_integration",
)
add(
    case_id="R27-hyponatremia-4-vomiting-thiazide",
    collection="R27", document=R27N, page=25, answer_page=26,
    scenario="A chlorthalidone-treated patient develops prolonged vomiting and severe volume depletion.",
    rows=[["Na⁺ / K⁺", "118 / 2.3 mEq/L"], ["Serum osmolality", "253 mOsm/kg"], ["Urine osmolality", "650 mOsm/kg"], ["Exposures", "Chlorthalidone plus vomiting"]],
    lead_in="Which explanation best accounts for the severity of the disorder?",
    correct="Combined thiazide-associated sodium loss and vomiting-induced volume contraction sustain ADH and severe hypotonic hyponatremia",
    distractors=["Isolated water deprivation causing hypernatremia", "Primary polydipsia with maximally dilute urine", "Hyperglycemia causing translocational hyponatremia", "Pseudohyponatremia from high lipid concentration"],
    explanation="Both chlorthalidone and vomiting reduce sodium and effective volume, while nonosmotic ADH prevents free-water excretion; the concentrated urine confirms ongoing water retention.",
    exclusion="The urine is concentrated and the osmolality is truly low, which excludes primary polydipsia, hypertonic glucose effects, and pseudohyponatremia.",
    clues=["Two simultaneous sodium/volume-loss mechanisms", "Urine osmolality 650 despite hypotonicity"],
)
add(
    case_id="R27-hyponatremia-5-cerebral-salt-wasting",
    collection="R27", document=R27N, page=27, answer_page=28,
    scenario="A patient with subarachnoid hemorrhage is orthostatic and volume depleted.",
    rows=[["Na⁺", "120 mEq/L"], ["Serum osmolality", "255 mOsm/kg"], ["Urine osmolality", "445 mOsm/kg"], ["Urine Na⁺", "82 mEq/L"], ["Volume exam", "Hypovolemic"]],
    lead_in="Which diagnosis best explains high urinary sodium despite systemic contraction?",
    correct="Cerebral salt wasting",
    distractors=["SIADH with euvolemia", "Primary polydipsia", "Pseudohyponatremia", "Hypervolemic heart-failure hyponatremia"],
    explanation="Following intracranial injury, renal salt wasting produces high urine sodium and hypovolemia; the volume depletion distinguishes this pattern from SIADH.",
    exclusion="SIADH is usually clinically euvolemic, whereas the orthostasis and contraction here are central discriminators.",
    clues=["Subarachnoid hemorrhage", "Urine Na⁺ 82 despite hypovolemia"],
)
add(
    case_id="R27-hyponatremia-6-CHF",
    collection="R27", document=R27N, page=29, answer_page=30,
    scenario="After myocardial infarction, a patient develops heart failure with edema, JVD, and crackles.",
    rows=[["Na⁺", "120 mEq/L"], ["Serum osmolality", "259 mOsm/kg"], ["Urine osmolality / Na⁺", "325 mOsm/kg / 21 mEq/L"], ["Exam", "Edema, JVD, crackles"]],
    lead_in="Which volume and hormone pattern explains the hyponatremia?",
    correct="Hypervolemic hypotonic hyponatremia with low effective arterial volume and persistent ADH",
    distractors=["True total-body volume depletion without edema", "Euvolemic primary polydipsia with suppressed ADH", "Pseudohyponatremia with normal tonicity", "Nephrogenic diabetes insipidus with free-water loss"],
    explanation="Heart failure expands total sodium and water while lowering effective arterial filling; concentrated urine and low urine sodium reflect water and sodium conservation.",
    exclusion="Congestive findings exclude true euvolemia or isolated depletion, and the measured osmolality confirms true hypotonicity.",
    clues=["Edema, JVD, and crackles", "Urine remains concentrated at 325 mOsm/kg"],
)
add(
    case_id="R27-hyponatremia-7-tea-toast",
    collection="R27", document=R27N, page=31, answer_page=32,
    scenario="A euvolemic patient consumes mostly tea and water with little protein or salt.",
    rows=[["Na⁺", "129 mEq/L"], ["Serum osmolality", "260 mOsm/kg"], ["Urine osmolality / Na⁺", "100 mOsm/kg / 8 mEq/L"], ["Diet", "Very low solute"]],
    lead_in="Which mechanism is most consistent with the dilute, low-sodium urine?",
    correct="Low solute intake limits total free-water excretion despite appropriate urine dilution",
    distractors=["SIADH prevents urine dilution", "Cerebral salt wasting produces hypovolemia and high urine sodium", "Heart failure activates sodium and water retention with edema", "Hyperglycemia raises extracellular tonicity"],
    explanation="The kidney is diluting urine, but very low osmole excretion limits how much water can be cleared each day, permitting dilutional hyponatremia.",
    exclusion="Urine osmolality 100 argues against persistent ADH, and the low urine sodium plus diet identify low solute availability.",
    clues=["Urine osmolality is only 100", "Diet supplies very little osmole"],
)
add(
    case_id="R27-hyponatremia-8-polydipsia",
    collection="R27", document=R27N, page=33, answer_page=34,
    scenario="A patient with schizophrenia drinks excessive water and normalizes after water restriction.",
    rows=[["Na⁺", "122 mEq/L"], ["Serum osmolality", "247 mOsm/kg"], ["Urine osmolality / Na⁺", "124 mOsm/kg / 6 mEq/L"], ["Response", "Normalizes with restriction"]],
    lead_in="Which process best explains the findings?",
    correct="Psychogenic polydipsia overwhelming renal water excretory capacity",
    distractors=["SIADH with persistently concentrated urine", "Renal salt wasting after intracranial injury", "Pseudohyponatremia from hyperproteinemia", "Diabetes insipidus causing hypernatremia"],
    explanation="Excess water intake produces true hypotonic hyponatremia with appropriately dilute urine, and correction with restriction supports psychogenic polydipsia.",
    exclusion="SIADH would retain a more concentrated urine, while diabetes insipidus causes water loss rather than dilutional hyponatremia.",
    clues=["Excessive water intake", "Dilute urine and reversal with restriction"],
)
add(
    case_id="R27-hyponatremia-9-marathon",
    collection="R27", document=R27N, page=35, answer_page=36,
    scenario="A marathon runner loses hypotonic sweat and then drinks excessive distilled water.",
    rows=[["Na⁺", "129 mEq/L"], ["Serum osmolality", "261 mOsm/kg"], ["Urine osmolality / Na⁺", "212 mOsm/kg / 8 mEq/L"], ["Replacement", "Excess distilled water"]],
    lead_in="Which sequence best explains the final hypotonic hyponatremia?",
    correct="Sweat causes salt and volume loss, then disproportionate solute-free water replacement lowers serum sodium",
    distractors=["Sweat alone adds free water to ECF", "Distilled water increases serum tonicity", "Hyperglycemia draws water out of cells", "Plasma protein creates a laboratory sodium artifact"],
    explanation="Exercise removes hypotonic fluid and some sodium; replacing beyond the water deficit with distilled water dilutes extracellular sodium while low effective volume can sustain ADH.",
    exclusion="Distilled water lowers rather than raises tonicity, and measured hypo-osmolality rules out a laboratory artifact.",
    clues=["Hypotonic sweat loss precedes replacement", "Replacement contains water without solute"],
)
add(
    case_id="R27-hyponatremia-10-pseudohyponatremia",
    collection="R27", document=R27N, page=37, answer_page=39,
    scenario="A patient with cirrhosis and hepatitis C has a high total-protein concentration.",
    rows=[["Na⁺", "126 mEq/L"], ["Measured osmolality", "285 mOsm/kg"], ["Total protein", "Elevated"], ["Underlying disease", "Cirrhosis and hepatitis C"]],
    lead_in="Which interpretation best reconciles sodium with measured osmolality?",
    correct="Isotonic pseudohyponatremia from an increased nonaqueous protein fraction",
    distractors=["True hypotonic SIADH", "Hypertonic hyponatremia from glucose", "Hypovolemic sodium loss with obligatory low osmolality", "Diabetes insipidus with free-water loss"],
    explanation="A high nonaqueous protein fraction can artifactually lower reported sodium while measured osmolality remains normal, producing pseudohyponatremia.",
    exclusion="Measured osmolality 285 is not hypotonic, and the identified high protein supplies the source of the artifact.",
    clues=["Normal measured osmolality", "Elevated total protein"],
)
add(
    case_id="R27-hyponatremia-11-small-cell-SIADH",
    collection="R27", document=R27N, page=40, answer_page=41,
    scenario="A patient with small-cell lung cancer develops low sodium without signs of volume depletion or edema.",
    rows=[["Na⁺", "123 mEq/L"], ["Serum osmolality", "255 mOsm/kg"], ["Cancer", "Small-cell lung carcinoma"], ["Volume exam", "Euvolemic"]],
    lead_in="Which paraneoplastic mechanism best explains the electrolyte disorder?",
    correct="Ectopic ADH produces euvolemic hypotonic hyponatremia",
    distractors=["Ectopic aldosterone produces renal salt wasting", "PTH-related peptide directly causes pseudohyponatremia", "Insulin deficiency causes hypotonic water retention", "Renin suppression causes diabetes insipidus"],
    explanation="Small-cell carcinoma can drive inappropriate ADH action, retaining water and lowering sodium and osmolality without overt edema or contraction.",
    exclusion="The source links this cancer to ADH-mediated water retention, not mineralocorticoid, glucose, or water-loss physiology.",
    clues=["Small-cell lung carcinoma", "True hypotonicity with euvolemia"],
)


R27H = "R27 Fluid Imbalance Case Studies (Clinical) Study Guide Hypernatremia.pdf"
add(
    case_id="R27-hypernatremia-1-vomiting-no-water",
    collection="R27", document=R27H, page=11, answer_page=12,
    scenario="A 57-year-old has three days of vomiting and has taken no food or fluid.",
    rows=[["Na⁺ / K⁺", "151 / 3.4 mEq/L"], ["Serum osmolality", "318 mOsm/kg"], ["HCO₃⁻ / pH", "29 mEq/L / 7.48"], ["BUN / creatinine", "32 / 1.5 mg/dL"], ["Urine osmolality / Na⁺", "650 mOsm/kg / 19 mEq/L"]],
    lead_in="Why did this vomiting patient become hypernatremic rather than hyponatremic?",
    correct="Severe water deprivation and insensible loss exceeded sodium loss while volume contraction limited renal sodium and bicarbonate losses",
    distractors=["Copious free-water intake diluted sodium", "SIADH retained water out of proportion to sodium", "Hyperglycemia shifted water into ECF", "Aldosterone deficiency caused renal sodium wasting"],
    explanation="With no replacement water, vomiting plus ongoing insensible loss creates a net water deficit; severe contraction lowers filtration and promotes sodium conservation.",
    exclusion="The patient has absent rather than excessive water intake and shows concentrated, low-sodium urine from volume conservation.",
    clues=["No fluid intake for three days", "Na⁺ 151 with urine Na⁺ 19"],
)
add(
    case_id="R27-hypernatremia-2-enteral-water",
    collection="R27", document=R27H, page=13, answer_page=14,
    scenario="An intubated 72-year-old receives enteral nutrition with only 50 mL free-water flushes every six hours.",
    rows=[["Initial Na⁺", "142 mEq/L"], ["Three days later", "155 mEq/L"], ["Free-water access", "No independent access"], ["Flushes", "50 mL every 6 hours"]],
    lead_in="Which balance problem most directly explains the rising sodium?",
    correct="Insufficient prescribed free water plus ongoing insensible water loss",
    distractors=["Excess free-water delivery through the tube", "Acute sodium loss from diarrhea", "SIADH causing water retention", "Pseudohypernatremia from plasma protein"],
    explanation="The critically ill patient cannot drink, the flush volume is inadequate, and respiratory and skin losses continue, progressively concentrating serum sodium.",
    exclusion="The trajectory reflects net water loss rather than water excess or sodium depletion.",
    clues=["No independent water access", "Sodium rises progressively during inadequate flushes"],
    difficulty="intermediate", reasoning_type="clinical_integration",
)
add(
    case_id="R27-hypernatremia-3-hypercalcemic-NDI",
    collection="R27", document=R27H, page=15, answer_page=16,
    scenario="A woman with metastatic breast cancer has polyuria, polydipsia, confusion, and high circulating ADH.",
    rows=[["Na⁺", "160 mEq/L"], ["Serum osmolality", "320 mOsm/kg"], ["Urine osmolality / Na⁺", "150 mOsm/kg / 18 mEq/L"], ["Ca²⁺", "12.5 mg/dL"], ["ADH", "High"]],
    lead_in="Which lesion best explains the failure to concentrate urine?",
    correct="Hypercalcemia-induced nephrogenic diabetes insipidus with impaired renal response to ADH",
    distractors=["Central diabetes insipidus from absent ADH", "SIADH with excessive collecting-duct water permeability", "Primary hyperaldosteronism with intact urine concentration", "Pseudohypernatremia from laboratory interference"],
    explanation="High ADH excludes central deficiency, while hypercalcemia can reduce collecting-duct aquaporin-2 response and produce dilute polyuria with hypernatremia.",
    exclusion="The kidney fails to respond despite high ADH, and hypercalcemia is the supplied renal-resistance trigger.",
    clues=["ADH is high but urine osmolality is 150", "Calcium is 12.5 mg/dL"],
)
add(
    case_id="R27-hypernatremia-4-primary-aldosteronism",
    collection="R27", document=R27H, page=18, answer_page=20,
    scenario="A 42-year-old with resistant hypertension has weakness, palpitations, and a unilateral adrenal mass.",
    rows=[["BP", "168/102 mm Hg"], ["Na⁺ / K⁺", "146 / 2.8 mEq/L"], ["Serum osmolality", "305 mOsm/kg"], ["Renin / aldosterone", "Low / very high"], ["Adrenal imaging", "1.8 cm unilateral mass"]],
    lead_in="Which endocrine diagnosis and renal action unify the data?",
    correct="Primary hyperaldosteronism causing sodium retention, potassium loss, and volume-expanded hypertension",
    distractors=["Secondary hyperaldosteronism with high renin", "Adrenal insufficiency with sodium wasting and hyperkalemia", "SIADH with water retention and low osmolality", "Nephrogenic diabetes insipidus with dilute polyuria"],
    explanation="Autonomous adrenal aldosterone suppresses renin, increases distal sodium reabsorption and potassium excretion, and expands volume; aldosterone escape limits the sodium rise.",
    exclusion="The combination of low renin, high aldosterone, adrenal mass, hypertension, and hypokalemia is not compatible with secondary activation or aldosterone deficiency.",
    clues=["Low renin with very high aldosterone", "Adrenal mass plus hypokalemic hypertension"],
)
add(
    case_id="R27-hypernatremia-5-multifactorial-CKD",
    collection="R27", document=R27H, page=21, answer_page=22,
    scenario="A woman with stage 4 CKD takes a loop diuretic, has watery diarrhea, and restricts fluid because of edema.",
    rows=[["Na⁺", "153 mEq/L"], ["Serum osmolality", "310 mOsm/kg"], ["BUN / creatinine", "81 / 3.8 mg/dL"], ["Urine osmolality / Na⁺", "380 mOsm/kg / 18 mEq/L"], ["Exam", "Dry mucosa plus mild edema"]],
    lead_in="Which explanation best handles the apparently conflicting edema and contraction signs?",
    correct="Multifactorial water deficit from diarrhea, loop diuresis, fluid restriction, and impaired renal concentration superimposed on edematous CKD",
    distractors=["Isolated sodium loading with no water loss", "Pure SIADH producing dilutional hyponatremia", "Primary polydipsia with maximally dilute urine", "Adrenal insufficiency causing sodium wasting"],
    explanation="Edema can coexist with reduced effective circulating volume; several water-loss and intake-limiting mechanisms concentrate sodium, while CKD impairs adaptive handling.",
    exclusion="The source identifies simultaneous water losses, restricted intake, and renal impairment rather than a single sodium-load or water-retention disorder.",
    clues=["Na⁺ 153 with dry mucosa", "Diarrhea, loop diuretic, restriction, and CKD all contribute"],
)


R32 = "R32 Serum Potassium Regulation (Pathophysiology) RLS.pdf"
add(
    case_id="R32-case-1-DKA-hyperkalemia",
    collection="R32", document=R32, page=8, answer_page=8,
    scenario="A patient with diabetic ketoacidosis has severe hyperglycemia, ketones, and hyperkalemia.",
    rows=[["Glucose", "500 mg/dL"], ["K⁺", "6.3 mEq/L"], ["HCO₃⁻", "12 mEq/L"], ["Ketones", "Positive"]],
    lead_in="Which mechanism and treatment pairing best explains the serum potassium?",
    correct="Insulin deficiency and hyperosmolality shift K⁺ out of cells; insulin and volume treatment drive K⁺ back into cells",
    distractors=["Aldosterone excess shifts K⁺ out of cells; spironolactone is immediately corrective", "Respiratory alkalosis releases K⁺ from cells; bicarbonate is the sole therapy", "Pseudohyperkalemia from sample clotting; no repeat or treatment is needed", "Renal potassium wasting directly raises serum K⁺; give a loop diuretic only"],
    explanation="Insulin deficiency reduces cellular potassium uptake and marked hyperglycemia promotes an outward water and potassium shift; insulin reverses the transcellular component as volume is restored.",
    exclusion="The DKA context supplies a real transcellular mechanism, not mineralocorticoid excess, respiratory alkalosis, or potassium wasting.",
    clues=["Glucose 500 with ketones and HCO₃⁻ 12", "Insulin regulates cellular K⁺ uptake"],
)
add(
    case_id="R32-case-2-AKI-emergency-hyperkalemia",
    collection="R32", document=R32, page=9, answer_page=9,
    scenario="A patient with acute kidney injury has potassium 7.0 mEq/L and hyperacute T waves.",
    rows=[["K⁺", "7.0 mEq/L"], ["BUN / creatinine", "100 / 5 mg/dL"], ["ECG", "Hyperacute T waves"]],
    lead_in="Which immediate strategy addresses both cardiac risk and serum potassium?",
    correct="Give IV calcium for membrane stabilization, then shift K⁺ with insulin plus dextrose and other temporizing measures",
    distractors=["Wait for spontaneous renal excretion because ECG changes are benign", "Give potassium replacement before repeating the ECG", "Use sodium restriction alone without cardiac stabilization", "Treat only with oral bicarbonate over several days"],
    explanation="ECG-toxic hyperkalemia requires immediate myocardial stabilization with calcium followed by rapid intracellular shifting measures such as insulin with dextrose.",
    exclusion="Potassium 7.0 with ECG changes is an emergency and cannot safely await diet change or delayed therapy.",
    clues=["Hyperacute T waves show membrane toxicity", "Severe AKI limits potassium excretion"],
)
add(
    case_id="R32-case-3-pseudohyperkalemia",
    collection="R32", document=R32, page=26, answer_page=26,
    scenario="An asymptomatic patient at a routine visit has an isolated high potassium result and otherwise normal chemistries.",
    rows=[["K⁺", "6.8 mEq/L"], ["Creatinine", "1.0 mg/dL"], ["HCO₃⁻", "24 mEq/L"], ["Physical exam", "Normal"]],
    lead_in="Which first step and interpretation are most appropriate?",
    correct="Obtain an ECG and promptly repeat a properly collected sample for suspected pseudohyperkalemia",
    distractors=["Diagnose renal failure solely from the potassium value", "Assume primary aldosteronism and measure only renin", "Give chronic potassium supplements before confirmation", "Ignore the result because asymptomatic hyperkalemia is never dangerous"],
    explanation="An isolated unexpected value can be spurious, but ECG assessment rapidly screens immediate danger while repeat sampling confirms or refutes pseudohyperkalemia.",
    exclusion="Normal renal and acid-base data make the isolated result suspicious, but potential true hyperkalemia still requires immediate ECG triage.",
    clues=["Isolated K⁺ abnormality with normal creatinine", "ECG distinguishes urgent electrical toxicity"],
)
add(
    case_id="R32-case-4-CHF-digitalis-AKI",
    collection="R32", document=R32, page=27, answer_page=28,
    scenario="A 78-year-old treated for heart failure becomes weak and hyporeflexic on hospital day five while receiving digitalis, hydrochlorothiazide, and potassium replacement.",
    rows=[["K⁺", "5.9 mEq/L"], ["HCO₃⁻", "20 mEq/L"], ["BUN / creatinine", "32 / 1.9 mg/dL"], ["ECG", "Mild hyperkalemic effect"], ["Current context", "Cardiorenal AKI, digitalis, K⁺ replacement, severe Na⁺ restriction"]],
    lead_in="Which explanation and medication response best match the lecture conclusion?",
    correct="Digitalis in acute kidney injury with continued K⁺ supplementation contributes to hyperkalemia; hold both and address the cardiorenal state",
    distractors=["Hydrochlorothiazide alone causes potassium retention; increase the potassium dose", "Severe sodium restriction proves preserved renal perfusion; continue all therapy", "Primary hyperaldosteronism causes the hyperkalemia; add spironolactone", "Normal renal function excludes medication accumulation; no changes are needed"],
    explanation="Worsening renal function in cardiorenal syndrome impairs potassium clearance and digitalis handling while ongoing supplementation adds potassium; the lecture recommends holding digitalis and potassium.",
    exclusion="The creatinine rise and treatment history support medication and clearance effects rather than aldosterone excess or preserved perfusion.",
    clues=["Creatinine is elevated during heart-failure treatment", "Digitalis and potassium replacement continue as K⁺ rises"],
)
add(
    case_id="R32-case-5-resistant-hypertension",
    collection="R32", document=R32, page=29, answer_page=29,
    scenario="A 24-year-old has new resistant hypertension without orthostasis.",
    rows=[["BP", "185/110 mm Hg"], ["K⁺", "2.9 mEq/L"], ["HCO₃⁻", "30 mEq/L"], ["Creatinine", "1.0 mg/dL"]],
    lead_in="Which test pattern would support the leading mineralocorticoid mechanism?",
    correct="Low renin with high aldosterone, supporting primary hyperaldosteronism",
    distractors=["High renin with low aldosterone", "Low renin with low aldosterone from adrenal adenoma", "Normal renin and aldosterone with obligatory renal failure", "High renin with high aldosterone proving primary adrenal secretion"],
    explanation="Hypertension, hypokalemia, and metabolic alkalosis suggest mineralocorticoid excess; autonomous adrenal aldosterone suppresses renin.",
    exclusion="Primary aldosterone production is defined by high aldosterone despite suppressed renin, not parallel renin activation.",
    clues=["Resistant hypertension with K⁺ 2.9", "HCO₃⁻ 30 suggests mineralocorticoid-associated alkalosis"],
)


R36 = "R36 Treatment Pitfalls & AI Use Case Studies (Clinical) RLS.pdf"
add(
    case_id="R36-case-2-gentamicin",
    collection="R36", document=R36, page=5, answer_page=6,
    scenario="An 89-year-old in septic shock receives IV gentamicin for multidrug-resistant Pseudomonas.",
    rows=[["Baseline creatinine", "0.6 mg/dL"], ["Day 3 creatinine", "2.5 mg/dL"], ["Gentamicin trough", "5 mg/L; goal 1–2 mg/L"]],
    lead_in="Which renal lesion and monitoring failure best explain the AKI?",
    correct="Aminoglycoside proximal tubular toxicity causing acute tubular necrosis with a supratherapeutic trough",
    distractors=["Acute interstitial nephritis proven by the infection alone", "Thrombotic microangiopathy from therapeutic gentamicin", "Crystalline nephropathy caused by penicillin exposure", "Postrenal obstruction from normal saline resuscitation"],
    explanation="Gentamicin accumulates in proximal tubular cells and causes toxic ATN; the trough of 5 mg/L is well above the stated 1–2 mg/L goal.",
    exclusion="The drug class, rapid creatinine rise, and high trough specifically support aminoglycoside tubular toxicity.",
    clues=["Creatinine rises from 0.6 to 2.5 mg/dL", "Gentamicin trough is 5 mg/L"],
)
add(
    case_id="R36-case-3-amphotericin",
    collection="R36", document=R36, page=7, answer_page=8,
    scenario="A liver-kidney transplant recipient with candidemia develops arrhythmia after several days of IV antifungal therapy.",
    rows=[["K⁺", "2.9 mEq/L"], ["Mg²⁺", "0.9 mg/dL"], ["CO₂", "20 mEq/L"], ["Creatinine", "0.8 mg/dL"], ["Urine K⁺", "75 mEq/L"], ["Urine Mg / creatinine", "15 / 150 mg/dL"]],
    lead_in="Which medication and loss pathway best explain the simultaneous abnormalities?",
    correct="Amphotericin B causes renal tubular potassium and magnesium wasting",
    distractors=["Pantoprazole causes renal magnesium wasting with high fractional excretion", "Ondansetron causes distal sodium retention and hyperkalemia", "Fluconazole causes isolated gastrointestinal potassium gain", "Furosemide explains the antifungal-specific tubular membrane injury"],
    explanation="Amphotericin damages tubular cell membranes, producing renal potassium and magnesium loss and sometimes RTA; the urine values support renal rather than gastrointestinal wasting.",
    exclusion="The source distinguishes PPI-associated reduced GI magnesium absorption from the renal wasting pattern caused by amphotericin.",
    clues=["Profound hypokalemia and hypomagnesemia", "Urinary electrolyte loss persists despite low serum levels"],
)
add(
    case_id="R36-case-4-cisplatin",
    collection="R36", document=R36, page=9, answer_page=10,
    scenario="A patient receiving cisplatin, etoposide, vancomycin, and lithium develops acute kidney injury.",
    rows=[["K⁺ / Mg²⁺", "2.8 mEq/L / 1.1 mg/dL"], ["Cl⁻ / HCO₃⁻", "113 / 11 mEq/L"], ["pH / pCO₂", "7.30 / 30 mm Hg"], ["Creatinine", "2.0 mg/dL from 0.8"], ["Urine", "Granular cast and positive urine anion gap"], ["Vancomycin trough", "15"]],
    lead_in="Which exposure unifies the tubular injury, acidosis, and magnesium loss?",
    correct="Cisplatin tubular toxicity causing ATN, renal tubular acidosis, and magnesium wasting",
    distractors=["Therapeutic vancomycin causing isolated glomerulonephritis", "Etoposide causing nephrogenic diabetes insipidus", "Lithium causing acute immune-complex nephritis", "Pantoprazole causing obstructive nephropathy"],
    explanation="Cisplatin can injure tubules through proximal secretion, producing ATN, renal tubular acidosis, and urinary magnesium wasting in the same patient.",
    exclusion="The normal vancomycin trough and the combined RTA plus magnesium-wasting phenotype point to cisplatin.",
    clues=["Granular cast with creatinine rise", "Normal-gap acidosis and hypomagnesemia"],
)
add(
    case_id="R36-case-5-furosemide",
    collection="R36", document=R36, page=12, answer_page=13,
    scenario="A 78-year-old with pulmonary edema improves after furosemide 80 mg IV twice daily and loses 3–4 kg.",
    rows=[["Therapy", "Furosemide 80 mg IV twice daily"], ["Response", "3–4 kg weight loss and improved oxygen need"], ["Potential findings", "Hypotension/tachycardia, hypokalemia, WBC casts, hearing loss"]],
    lead_in="Which monitoring bundle captures the major lecture-listed adverse effects?",
    correct="Watch for overdiuresis with hypotension, hypokalemia, interstitial nephritis with WBC casts, and dose-related ototoxicity",
    distractors=["Monitor only for hyperkalemia and bradycardia", "Expect nephrotic proteinuria as the defining loop effect", "Assume WBC casts exclude a drug reaction", "Hearing loss is unrelated to high-dose loop therapy"],
    explanation="Loop diuretics can overdiurese, increase distal potassium loss, provoke sulfa-associated interstitial nephritis, and cause dose-dependent ototoxicity.",
    exclusion="The source explicitly lists all four effects after intensive loop diuresis.",
    clues=["High-dose IV loop exposure", "Large weight loss after decongestion"],
)
add(
    case_id="R36-case-6-gadolinium",
    collection="R36", document=R36, page=14, answer_page=15,
    scenario="A hemodialysis patient with ESRD is considered for gadolinium-enhanced MRI.",
    rows=[["Renal function", "ESRD on hemodialysis"], ["Proposed exposure", "Gadolinium MRI contrast"], ["Target condition", "Possible osteomyelitis"]],
    lead_in="Which delayed toxicity profile is the distinctive risk?",
    correct="Nephrogenic systemic fibrosis with skin thickening, indurated plaques or nodules, burning, and joint contractures",
    distractors=["Minimal change disease with isolated nephrotic proteinuria", "Anti-GBM disease with pulmonary hemorrhage", "Immediate calcium oxalate crystal obstruction", "Pseudohyponatremia from plasma protein"],
    explanation="Advanced kidney failure permits gadolinium-associated profibrotic tissue deposition, producing characteristic skin and soft-tissue fibrosis.",
    exclusion="The exposure-risk pairing in the source is ESRD plus gadolinium, with a fibrosing rather than glomerular or crystal syndrome.",
    clues=["ESRD greatly limits gadolinium clearance", "The toxicity is systemic soft-tissue fibrosis"],
)
add(
    case_id="R36-case-7-heroin-FSGS",
    collection="R36", document=R36, page=17, answer_page=18,
    scenario="A 28-year-old with heroin use has foamy urine, bilateral edema, and subnephrotic proteinuria.",
    rows=[["Protein dipstick", "3+"], ["24-hour urine protein", "2.0 g"], ["Edema", "2+ bilateral lower extremity"], ["Exposure", "Heroin"]],
    lead_in="Which biopsy diagnosis is most strongly linked to this exposure and protein pattern?",
    correct="Secondary focal segmental glomerulosclerosis",
    distractors=["Primary minimal change disease", "Membranous nephropathy from a subepithelial immune process", "Amyloidosis without an exposure relationship", "Postinfectious glomerulonephritis"],
    explanation="Heroin is a listed cause of secondary FSGS, which often presents with subnephrotic proteinuria and less extensive podocyte effacement than primary FSGS.",
    exclusion="The source specifically pairs heroin with secondary FSGS and notes the lower-grade proteinuria pattern.",
    clues=["Heroin exposure", "Protein excretion is 2.0 g/day"],
)
add(
    case_id="R36-case-8-contrast-risk",
    collection="R36", document=R36, page=19, answer_page=20,
    scenario="Several patients are being considered for contrast-enhanced imaging.",
    rows=[["Candidate A", "Age 22; eGFR 120; 50 mL IV iodinated contrast"], ["Candidate B", "Age 64; eGFR 50; NSAID use; hypotension/sepsis; 100 mL IV iodinated contrast"], ["Candidate C", "Age 77; eGFR 45; gadolinium MRI"], ["Candidate D", "Age 82; eGFR 60; vomiting/hypotension; oral CT contrast"]],
    lead_in="Who has the greatest source-defined risk for contrast-associated AKI?",
    correct="Candidate B because CKD, NSAIDs, hypotension, comorbidity, and a larger iodinated IV contrast dose converge",
    distractors=["Candidate A because young age is the dominant risk", "Candidate C because gadolinium MRI is the classic iodinated CT exposure", "Candidate D because oral contrast produces the greatest tubular dose", "All candidates have identical risk regardless of route or kidney function"],
    explanation="The highest-risk profile combines reduced baseline GFR, older age, NSAID exposure, active hypotension/sepsis, and 100 mL of iodinated IV contrast.",
    exclusion="Risk depends on kidney reserve, concurrent renal insults, iodinated IV route, and dose rather than age alone or noniodinated/oral exposure.",
    clues=["eGFR 50 plus hypotension and NSAIDs", "100 mL iodinated IV contrast"],
)
add(
    case_id="R36-case-9-lithium-NDI",
    collection="R36", document=R36, page=21, answer_page=25,
    scenario="After cardiac surgery, a lithium-treated patient produces 6 L of urine in 24 hours and becomes hypernatremic.",
    rows=[["Urine output", "6 L/24 h"], ["Na⁺", "154 mEq/L"], ["Urine osmolality", "120 mOsm/L"], ["After desmopressin", "Urine osmolality unchanged"], ["Long-term drug", "Lithium"]],
    lead_in="Which diagnosis and cause best fit the failed desmopressin response?",
    correct="Lithium-associated nephrogenic diabetes insipidus",
    distractors=["Central diabetes insipidus from absent ADH response to desmopressin", "Primary polydipsia with hypernatremia", "SIADH with dilute polyuria", "Osmotic diuresis proven by concentrated urine"],
    explanation="Very dilute polyuria with hypernatremia indicates water diuresis; failure to concentrate after desmopressin shows renal ADH resistance, and lithium is the supplied chronic cause.",
    exclusion="Central DI should increase urine osmolality after desmopressin, whereas this urine does not respond.",
    clues=["Urine osmolality stays 120 after desmopressin", "Longstanding lithium exposure"],
)
add(
    case_id="R36-case-10-NSAID-MCD",
    collection="R36", document=R36, page=26, answer_page=27,
    scenario="A 39-year-old with lymphoma in remission develops abrupt edema after a back injury; biopsy shows minimal change disease with 95% podocyte effacement.",
    rows=[["Weight gain", "20 lb in 2 weeks"], ["24-hour protein", "15 g"], ["GFR", "Normal"], ["Biopsy", "Minimal change disease; 95% foot-process effacement"], ["Recent event", "Back injury with likely regular analgesic use"]],
    lead_in="Which medication class is the source-linked trigger to identify?",
    correct="NSAIDs",
    distractors=["SGLT2 inhibitors", "Calcium-channel blockers", "Platinum chemotherapeutic agents", "Loop diuretics"],
    explanation="The lecture identifies NSAID use and lymphoma as adult minimal-change associations; the recent back injury directs attention to regular NSAID exposure.",
    exclusion="The source specifically asks for the medication class associated with minimal change disease and keys NSAIDs.",
    clues=["Abrupt nephrotic syndrome with diffuse foot-process effacement", "Recent back injury suggests analgesic exposure"],
)
add(
    case_id="R36-case-11-ertapenem-AIN",
    collection="R36", document=R36, page=28, answer_page=30,
    scenario="A 67-year-old with CKD develops AKI three weeks into a planned four-week course of IV ertapenem.",
    rows=[["Creatinine", "1.5 to 3.3 mg/dL"], ["Temperature", "100.4°F"], ["Skin", "Maculopapular rash after one week"], ["Urine", "WBCs and WBC casts"], ["New drug", "Ertapenem"]],
    lead_in="Which diagnosis and culprit best integrate timing, rash, and sediment?",
    correct="Ertapenem-induced acute interstitial nephritis",
    distractors=["Furosemide-induced ATN after years of stable use", "Topiramate-induced postrenal obstruction", "Amlodipine-induced immune-complex glomerulonephritis", "Ascending cholangitis causing nephrogenic diabetes insipidus"],
    explanation="AKI after a new antibiotic, with fever, rash, WBCs, and WBC casts, is the classic source pattern for drug-induced AIN; the temporal culprit is ertapenem.",
    exclusion="The other drugs were chronic and the sediment is interstitial rather than granular, glomerular, or obstructive.",
    clues=["New antibiotic precedes AKI", "Rash, fever, and WBC casts"],
)


R37 = "R37 Clinical Nephrology Case Studies SEA Session RLS.pdf"
add(
    case_id="R37-case-1-rhabdomyolysis",
    collection="R37", document=R37, page=2, answer_page=13,
    scenario="A patient develops acute kidney injury after a muscle-injury syndrome with pigmenturia.",
    rows=[["Dominant injury", "Skeletal-muscle breakdown"], ["Urine clue", "Pigment positive with myoglobin-related sediment"], ["Renal pattern", "Acute tubular injury"]],
    lead_in="Which mechanism best explains the renal lesion?",
    correct="Myoglobin-mediated pigment nephropathy causing acute tubular necrosis",
    distractors=["Anti-GBM antibodies causing crescentic glomerulonephritis", "PPI hypersensitivity causing interstitial nephritis", "Minimal change disease causing nephrotic edema", "Chronic obstruction causing hydronephrosis"],
    explanation="Rhabdomyolysis releases myoglobin, which contributes direct tubular toxicity and intratubular pigment obstruction, producing acute tubular injury.",
    exclusion="The muscle-injury and pigment pattern localize the injury to tubules rather than glomeruli, interstitium, or collecting-system obstruction.",
    clues=["Muscle breakdown precedes AKI", "Pigmenturia points to myoglobin"],
)
add(
    case_id="R37-case-2-pulmonary-renal",
    collection="R37", document=R37, page=14, answer_page=20,
    scenario="A patient presents with pulmonary hemorrhage and rapidly progressive nephritic kidney injury.",
    rows=[["Pulmonary finding", "Hemorrhage / hemoptysis"], ["Renal finding", "Rapidly progressive glomerulonephritis"], ["Unifying target", "Basement membranes"]],
    lead_in="Which diagnosis and immunofluorescence pattern best unify both organs?",
    correct="Anti-GBM disease with linear IgG staining along glomerular basement membranes",
    distractors=["Postinfectious GN with isolated subepithelial humps", "Minimal change disease with negative immunofluorescence", "Acute interstitial nephritis with WBC casts", "Diabetic nephropathy with no pulmonary process"],
    explanation="Antibodies directed against basement-membrane antigen can injure glomerular and alveolar capillaries, producing a pulmonary-renal syndrome and linear IgG staining.",
    exclusion="The simultaneous pulmonary hemorrhage and rapidly progressive nephritis require a shared basement-membrane process.",
    clues=["Pulmonary hemorrhage plus RPGN", "Linear rather than granular immune staining"],
)
add(
    case_id="R37-case-3-PPI-AIN",
    collection="R37", document=R37, page=21, answer_page=26,
    scenario="A patient taking pantoprazole develops acute kidney injury with inflammatory urine sediment.",
    rows=[["Drug exposure", "Pantoprazole"], ["Urine sediment", "WBCs and WBC casts"], ["Renal course", "Acute decline"]],
    lead_in="Which compartment and process are most likely injured?",
    correct="Drug-induced acute interstitial nephritis affecting the tubulointerstitium",
    distractors=["Immune-complex glomerulonephritis limited to glomeruli", "Myoglobin-induced acute tubular necrosis", "Postrenal obstruction of both ureters", "Minimal change podocytopathy"],
    explanation="A proton-pump inhibitor can provoke hypersensitivity-mediated interstitial inflammation, and WBC casts localize the process to the renal tubulointerstitium.",
    exclusion="The inflammatory white-cell sediment is not the red-cell, pigment, obstructive, or nephrotic pattern expected from the alternatives.",
    clues=["Pantoprazole is a recognized AIN exposure in the lecture", "WBC casts localize inflammation within the kidney"],
)


R38 = "R38 Nephrology Clinical Case Discussion RLS.pdf"
add(
    case_id="R38-longitudinal-multiple-hit-ATN",
    collection="R38", document=R38, page=2, answer_page=12,
    scenario="A 70-year-old with heart failure receives diuretics and an ACE inhibitor, then naproxen, gentamicin, iodinated contrast, and later develops septic shock.",
    rows=[["Na⁺ / K⁺ / HCO₃⁻", "141 / 7 / 14 mEq/L"], ["BUN / creatinine", "93 / 4.6 mg/dL"], ["pH / pCO₂", "7.28 / 28 mm Hg"], ["Urine Na⁺ / osmolality", "50 mEq/L / 300 mOsm/kg"], ["FENa", "3%"], ["Sediment", "Muddy brown casts"]],
    lead_in="Which final renal lesion best explains the intrinsic-injury indices after the cumulative insults?",
    correct="Ischemic and nephrotoxic acute tubular necrosis culminating during septic shock",
    distractors=["Pure prerenal azotemia with intact tubular sodium conservation", "Acute glomerulonephritis with red-cell casts", "Postrenal obstruction with hydronephrosis", "Minimal change disease with selective proteinuria"],
    explanation="FENa 3%, urine sodium 50, poorly concentrated urine, and muddy brown casts show established tubular injury after hemodynamic, drug, contrast, and septic insults.",
    exclusion="Prerenal physiology would conserve sodium and concentrate urine, while the sediment here is tubular rather than glomerular.",
    clues=["FENa 3% and urine Na⁺ 50", "Muddy brown casts after shock and nephrotoxins"],
)


R30 = "R30 Acid-Base Balance RLS.pdf"
R35_CONT = "R35 cont. Acid-Base Case Studies Advanced (Clinical) Lecture Slides.pdf"
add(
    case_id="R30-RTA-classic-distal-type-1",
    collection="R30", document=R30, page=39, answer_page=43,
    scenario="A patient has a persistent normal-anion-gap metabolic acidosis without gastrointestinal bicarbonate loss.",
    rows=[["Serum K⁺", "Low"], ["Urine pH", "Persistently >6.0"], ["Urine anion gap", "Positive"], ["Distal H⁺ secretion", "Impaired"]],
    lead_in="Which renal tubular acidosis profile best integrates these findings?",
    correct="Classic distal type 1 RTA from failure of distal H⁺ secretion",
    distractors=["Proximal type 2 RTA from impaired HCO₃⁻ reclamation", "Type 4 RTA from low aldosterone and impaired NH₄⁺ buffering", "Voltage-mediated distal type 1 RTA with impaired H⁺ and K⁺ excretion", "Appropriate renal response to an extrarenal bicarbonate loss"],
    explanation="Classic distal type 1 RTA combines failure to acidify the urine with a persistently high urine pH, a positive urine anion gap reflecting low NH₄⁺ excretion, and hypokalemia.",
    exclusion="Proximal RTA has urine pH that varies with serum bicarbonate, type 4 and voltage-mediated distal RTA are hyperkalemic, and an appropriate response to extrarenal bicarbonate loss increases urinary NH₄Cl rather than leaving a positive urine anion gap.",
    clues=["Urine pH remains above 6.0", "Positive urine anion gap with low serum K⁺"],
    reasoning_type="clinical_integration",
    note="This diagnostic profile is a source-grounded synthesis of the cited lecture's RTA mechanism and comparison slides.",
)
add(
    case_id="R30-RTA-proximal-type-2",
    collection="R30", document=R30, page=38, answer_page=43,
    scenario="A patient with a normal-anion-gap metabolic acidosis is evaluated at two different serum bicarbonate concentrations.",
    rows=[["Serum K⁺", "Low"], ["Urine pH while serum HCO₃⁻ is relatively high", ">5.5"], ["Urine pH after serum HCO₃⁻ falls", "<5.5"], ["Urine anion gap", "Variable"]],
    lead_in="Which tubular defect best explains the changing urine pH?",
    correct="Proximal type 2 RTA from impaired HCO₃⁻ reclamation",
    distractors=["Classic distal type 1 RTA from failure of distal H⁺ secretion", "Type 4 RTA from low aldosterone and impaired NH₄⁺ buffering", "Voltage-mediated distal type 1 RTA with impaired H⁺ and K⁺ excretion", "Appropriate renal response to an extrarenal bicarbonate loss"],
    explanation="In proximal type 2 RTA, bicarbonate spills into urine while the filtered load exceeds the reduced reclamation threshold, but the intact distal nephron can lower urine pH once serum bicarbonate falls. The lecture also associates type 2 RTA with hypokalemia.",
    exclusion="Persistently alkaline urine favors distal acidification failure, hyperkalemia favors type 4 or voltage-mediated disease, and an extrarenal bicarbonate loss does not create a proximal reclamation threshold pattern.",
    clues=["Urine pH changes with serum bicarbonate", "Hypokalemia with a variable urine anion gap"],
    reasoning_type="mechanism",
    note="This diagnostic profile is a source-grounded synthesis of the cited lecture's RTA mechanism and comparison slides.",
    extra_citations=[citation(R35_CONT, 27)],
)
add(
    case_id="R30-RTA-type-4",
    collection="R30", document=R30, page=41, answer_page=43,
    scenario="A patient with a normal-anion-gap metabolic acidosis has evidence of reduced aldosterone activity.",
    rows=[["Serum K⁺", "High"], ["Aldosterone effect", "Low"], ["Urine pH", "Usually <5.5"], ["Urine anion gap", "Positive"]],
    lead_in="Which mechanism best explains the acidosis despite the acidic urine pH?",
    correct="Type 4 RTA with hyperkalemia reducing NH₃ availability and therefore NH₄⁺ excretion",
    distractors=["Classic distal type 1 RTA from failure of distal H⁺ secretion", "Proximal type 2 RTA from impaired HCO₃⁻ reclamation", "Voltage-mediated distal type 1 RTA with loss of the negative lumen potential", "Appropriate renal response to an extrarenal bicarbonate loss"],
    explanation="Type 4 RTA is hyperkalemic and linked to low aldosterone activity. High potassium reduces ammonia buffering, so net ammonium excretion is low and the urine anion gap stays positive even though free H⁺ can lower urine pH below 5.5.",
    exclusion="Classic distal RTA has persistently high urine pH, proximal RTA has variable urine pH with hypokalemia, voltage-mediated distal RTA also impairs luminal H⁺ secretion, and an appropriate extrarenal response increases NH₄Cl excretion.",
    clues=["High serum K⁺ with low aldosterone effect", "Acidic urine but a positive urine anion gap"],
    reasoning_type="clinical_integration",
    note="This diagnostic profile is a source-grounded synthesis of the cited lecture's RTA mechanism and comparison slides.",
)
add(
    case_id="R30-RTA-voltage-mediated-distal-type-1",
    collection="R30", document=R30, page=40, answer_page=43,
    scenario="A patient develops a normal-anion-gap metabolic acidosis after loss of the normal negative electrical potential in the distal tubular lumen.",
    rows=[["Distal electrical gradient", "Negative lumen potential lost"], ["Serum K⁺", "High"], ["Urine pH", "Persistently >6.0"], ["Urine anion gap", "Positive"], ["Potential causes", "ENaC blockade, poor distal Na⁺ flow, or toxin injury"]],
    lead_in="Which RTA subtype and transport consequence best fit this pattern?",
    correct="Voltage-mediated distal type 1 RTA with impaired H⁺ and K⁺ excretion",
    distractors=["Classic distal type 1 RTA with hypokalemia from isolated H⁺ pump failure", "Proximal type 2 RTA from impaired HCO₃⁻ reclamation", "Type 4 RTA with preserved ability to lower urine pH", "Appropriate renal response to an extrarenal bicarbonate loss"],
    explanation="Loss of the negative distal lumen potential removes the electrical drive for both H⁺ and K⁺ secretion. The result is hyperkalemic distal type 1 RTA with persistently alkaline urine and a positive urine anion gap.",
    exclusion="Classic pump failure is usually hypokalemic, proximal RTA has bicarbonate-dependent urine pH, type 4 RTA usually retains the ability to lower urine pH below 5.5, and extrarenal loss should increase urinary NH₄Cl excretion.",
    clues=["Loss of the negative distal lumen potential", "Both H⁺ and K⁺ excretion are impaired"],
    reasoning_type="mechanism",
    note="This diagnostic profile is a source-grounded synthesis of the cited lecture's RTA mechanism and comparison slides.",
)


R39 = "R39 Renal Mystery Illness Questions for Discussion RLS.pdf"
add(
    case_id="R39-mystery-primary-aldosteronism",
    collection="R39", document=R39, page=2, answer_page=6,
    scenario="A 32-year-old with weakness and cramps has severe hypertension and renal potassium wasting.",
    rows=[["BP", "178/102 mm Hg"], ["pH / pCO₂", "7.50 / 48 mm Hg"], ["Na⁺ / K⁺ / HCO₃⁻ / Cl⁻", "142 / 2.9 / 36 / 98 mEq/L"], ["Urine K⁺", "46 mEq/L"], ["Plasma renin activity", "0.28; low"], ["Aldosterone", "35; high"]],
    lead_in="Which diagnosis explains the pressure, acid-base, and potassium findings?",
    correct="Primary hyperaldosteronism causing renal K⁺ and H⁺ loss with volume-expanded hypertension",
    distractors=["Secondary hyperaldosteronism with high renin", "Adrenal insufficiency with hyperkalemic acidosis", "SIADH with dilutional hyponatremia", "Renal tubular acidosis with low bicarbonate"],
    explanation="Autonomous aldosterone raises distal sodium reabsorption and potassium and hydrogen secretion, producing low-renin hypertension, hypokalemia, and metabolic alkalosis.",
    exclusion="The high aldosterone despite suppressed renin establishes primary rather than secondary mineralocorticoid excess.",
    clues=["Low renin with high aldosterone", "Hypokalemic metabolic alkalosis with hypertension"],
)


R41 = "R41 Renal Gross Specimen Review RLS.pdf"
R41T = "R41 Renal Gross Specimen Review Trran.pdf"
add(
    case_id="R41-case-1-postinfectious-GN",
    collection="R41", document=R41, page=5, answer_page=8,
    scenario="A child develops edema and hypertension after a sore throat.",
    rows=[["BP", "140/80 mm Hg"], ["Complement C3", "Low"], ["Urine protein", "4+"], ["Sediment", "Dysmorphic RBCs and RBC casts"]],
    lead_in="Which glomerular diagnosis best integrates timing, complement, and sediment?",
    correct="Postinfectious glomerulonephritis",
    distractors=["Minimal change disease", "Anti-GBM disease", "Acute interstitial nephritis", "Ischemic acute tubular necrosis"],
    explanation="A recent pharyngeal infection followed by nephritic sediment, hypertension, edema, and low complement is the lecture pattern of postinfectious GN.",
    exclusion="The red-cell casts and complement consumption indicate immune glomerular inflammation rather than podocyte, interstitial, or tubular injury.",
    clues=["Recent sore throat with low C3", "Dysmorphic RBCs and RBC casts"],
)
add(
    case_id="R41-case-2-anti-GBM",
    collection="R41", document=R41, page=10, answer_page=14,
    scenario="A patient has hemoptysis and rapidly progressive renal failure with normal complement.",
    rows=[["Pulmonary finding", "Hemoptysis"], ["Complement", "Normal"], ["Urine protein", "2+"], ["Sediment", "Dysmorphic RBCs and RBC casts"]],
    lead_in="Which diagnosis and staining pattern are expected?",
    correct="Anti-GBM disease with linear glomerular IgG",
    distractors=["Postinfectious GN with granular subepithelial deposits", "Minimal change disease with negative immunofluorescence", "Lupus nephritis with full-house granular staining", "Acute pyelonephritis with WBC casts"],
    explanation="Pulmonary hemorrhage plus rapidly progressive nephritic injury and normal complement supports anti-GBM disease, which produces linear IgG along the GBM.",
    exclusion="The pulmonary-renal combination and normal complement distinguish anti-GBM disease from immune-complex nephritides.",
    clues=["Hemoptysis plus nephritic sediment", "Complement is normal"],
)
add(
    case_id="R41-case-3-lupus-nephritis",
    collection="R41", document=R41, page=16, answer_page=30,
    scenario="A patient with systemic lupus features develops combined nephritic and nephrotic renal findings.",
    rows=[["Systemic context", "Systemic lupus erythematosus"], ["Renal pattern", "Nephritic plus nephrotic features"], ["Serologic activity markers", "Anti-dsDNA and complement"], ["Expected IF", "Multiple immunoglobulins and complement"]],
    lead_in="Which renal immune-deposit pattern most strongly supports the diagnosis?",
    correct="Lupus nephritis with granular full-house immunofluorescence",
    distractors=["Anti-GBM disease with isolated linear IgG", "Minimal change disease with negative immunofluorescence", "FSGS with no immune deposits", "Acute tubular necrosis with muddy brown casts"],
    explanation="Lupus nephritis is an immune-complex glomerulonephritis with broad immunoglobulin and complement deposition, producing the characteristic full-house granular pattern.",
    exclusion="The systemic autoimmune context and combined nephritic-nephrotic presentation require immune-complex glomerular disease rather than podocyte or tubular injury.",
    clues=["Systemic lupus context", "Broad immunoglobulin and complement deposition"],
)
add(
    case_id="R41-case-4-crush-ATN",
    collection="R41", document=R41, page=31, answer_page=33,
    scenario="A 48-year-old is pinned under a wall for four hours, arrives with BP 70/40 mm Hg, and produces only 300 mL urine in 24 hours; biopsy is obtained ten days later.",
    rows=[["Ischemic exposure", "Crush injury with prolonged shock"], ["BP", "70/40 mm Hg"], ["Urine output", "300 mL/24 h"], ["Biopsy timing", "Day 10"]],
    lead_in="Which biopsy phase and near-term complication should be anticipated?",
    correct="Regenerating acute tubular injury with mitoses and casts, followed by a diuretic phase that risks volume and electrolyte loss",
    distractors=["Anti-GBM crescent formation followed by pulmonary hemorrhage", "Minimal change disease followed by selective proteinuria", "Chronic pyelonephritis followed by persistent obstruction", "Membranous nephropathy followed by renal-vein thrombosis"],
    explanation="Severe ischemia causes ATN; by day ten, regenerating tubular epithelium and residual debris may precede a high-output recovery phase with hypovolemia, hyponatremia, and hypokalemia risk.",
    exclusion="The shock, oliguria, and delayed biopsy timing fit ischemic tubular injury and regeneration rather than glomerular or chronic infectious disease.",
    clues=["Profound hypotension and oliguria", "Biopsy occurs ten days after injury"],
)
add(
    case_id="R41-case-5-staghorn-pyelonephritis",
    collection="R41", document=R41, page=34, answer_page=36,
    scenario="A dissected kidney contains irregular concretions in upper-pole calyces, including a branching calculus, with acute renal inflammation microscopically.",
    rows=[["Gross finding", "Irregular calyceal concretions"], ["Stone shape", "Branching staghorn calculus"], ["Microscopy", "Acute pyelonephritis"], ["Confirmatory urine findings", "Bacterial culture, WBCs, and WBC casts"]],
    lead_in="Which stone composition and infection mechanism best unify the gross and microscopic findings?",
    correct="Struvite stone from urease-producing infection with obstruction promoting acute pyelonephritis",
    distractors=["Uric-acid stone from acidic urine with sterile interstitium", "Calcium oxalate stone that proves anti-GBM disease", "Cystine stone caused by ADH excess", "Drug crystal causing isolated minimal change disease"],
    explanation="A branching staghorn calculus is classically magnesium ammonium phosphate precipitated in alkaline urine from urease-producing organisms; obstruction favors ascending renal infection.",
    exclusion="The source’s branching morphology and associated acute inflammation specifically link infection, struvite, obstruction, and pyelonephritis.",
    clues=["Branching staghorn configuration", "Acute pyelonephritis accompanies obstruction"],
    extra_citations=[citation(R41T, 9)],
)


EXISTING_CASES = [
    ("R34-case-1-necrotizing-GN", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 9, ["q-b21d1bcaf3310ceb5569", "q-e70623b485e8e4a95c15"]),
    ("R34-case-2-anti-GBM", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 19, ["q-fd22f86ddf4750e6325c"]),
    ("R34-case-3-IgA-HSP", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 32, ["q-672602ad9d5565605b09", "q-d45f770a4496a2dd08b1"]),
    ("R34-case-4-infection-associated-GN", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 44, ["q-f290e94d070ee4fd554f", "q-9f4a1afba93ef6573132"]),
    ("R34-case-5-membranous", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 56, ["q-8625c08a2b15cb762fdd", "q-4c58f00612b3d8a15cc4"]),
    ("R34-case-6-diabetic-nephropathy", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 68, ["q-0620eadaa903a2c679c3"]),
    ("R34-case-7-FSGS", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 76, ["q-bf1ce6935c89ace36e15"]),
    ("R34-case-8-thrombotic-microangiopathy", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 83, ["q-4cd4a14eaed3f26c1cac"]),
    ("R34-case-9-AIN", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 92, ["q-7016a3c7c13ac68418e7"]),
    ("R34-case-10-amyloid", "R34", "R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 98, ["q-71b1a77f6ffa95d60249"]),
    ("R35-case-1-anion-gap", "R35", "R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 3, ["q-e52d22b456a257746aac"]),
    ("R35-case-2-metabolic-alkalosis", "R35", "R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 6, ["q-b08baae7cecf3848b138"]),
    ("R35-case-3-post-hypercapnic-alkalosis", "R35", "R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 10, ["q-75dfa33316ce61fc7a4c"]),
    ("R35-case-4-osmolal-gap", "R35", "R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 14, ["q-a8c841ad485aa9f2e905"]),
    ("R36-case-1-ACE-inhibitor", "R36", R36, 2, ["q-fe8dc32336f7e8cbf2d1"]),
    ("R36-case-12-protease-crystals", "R36", R36, 31, ["q-6eab30c02d7f29ba72c9"]),
    ("R36-case-13-urinary-retention", "R36", R36, 33, ["q-89681f79c60c5ff4d9b0"]),
    ("R37-case-4-minimal-change", "R37", R37, 27, ["q-0118822fc4b7e1e6126e"]),
    ("R37-case-5-advanced-CKD", "R37", R37, 33, ["q-45bb041ac08246335e66"]),
]


def append_unique(values: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if item not in values:
        values.append(item)


def add_context(
    question: dict[str, Any],
    case_id: str,
    scenario: str,
    title: str,
    rows: list[list[str]],
    document: str,
    page: int,
    lead_in: str | None = None,
) -> None:
    source = citation(document, page)
    question["case_id"] = case_id
    question["case_enrichment_batch"] = BATCH
    question["scenario"] = scenario
    question["case_context"] = scenario
    question["context_table"] = {
        "placement": "additional",
        "title": title,
        "columns": ["Finding", "Value"],
        "rows": rows,
        "note": "Clinical context is transcribed or faithfully condensed from the cited lecture case.",
        "source": source,
    }
    append_unique(question["citations"], source)
    if lead_in:
        question["lead_in"] = lead_in
        question["stem"] = f"{scenario} {lead_in}"
    question["difficulty"] = "advanced"
    question["reasoning_type"] = "clinical_integration"


def enrich_existing(bank: dict[str, Any]) -> None:
    by_id = {question["question_id"]: question for question in bank["questions"]}
    add_context(
        by_id["q-fe8dc32336f7e8cbf2d1"],
        "R36-case-1-ACE-inhibitor",
        "One week after starting lisinopril for heart failure, a 57-year-old develops dry cough, mild lip swelling, K⁺ 5.3 mEq/L, and a small creatinine rise.",
        "ACE inhibitor treatment context",
        [["New drug", "Lisinopril 5 mg daily"], ["Symptoms", "Dry cough and mild lip swelling"], ["K⁺", "5.3 mEq/L"], ["Creatinine", "0.9 to 1.1 mg/dL"]],
        R36, 2,
        "Which visible finding most directly represents the bradykinin-associated adverse effect that requires stopping the culprit drug?",
    )
    add_context(
        by_id["q-6eab30c02d7f29ba72c9"],
        "R36-case-12-protease-crystals",
        "A 27-year-old with HIV develops a creatinine rise from 0.8 to 2.0 mg/dL after starting tenofovir alafenamide, atazanavir, and efavirenz; urine sediment contains the displayed crystals.",
        "HAART-associated kidney injury",
        [["Creatinine", "0.8 to 2.0 mg/dL"], ["Protease inhibitor", "Atazanavir"], ["Urine", "Crystals on sediment microscopy"]],
        R36, 31,
        "Which morphology in the displayed sediment supports protease-inhibitor crystalline nephropathy?",
    )
    add_context(
        by_id["q-89681f79c60c5ff4d9b0"],
        "R36-case-13-urinary-retention",
        "An 82-year-old taking oxybutynin receives oxycodone after lumbar surgery and then has no urine output for 12 hours.",
        "Postoperative urinary retention context",
        [["Chronic drug", "Oxybutynin"], ["Postoperative analgesic", "Oxycodone"], ["Urine output", "None for 12 hours"]],
        R36, 33,
        "Which visible ultrasound finding supports medication-associated urinary retention with postrenal obstruction?",
    )
    add_context(
        by_id["q-0118822fc4b7e1e6126e"],
        "R37-case-4-minimal-change",
        "A 10-year-old with atopy has abrupt edema, albumin 1.8 g/dL, cholesterol 450 mg/dL, 7.6 g/day proteinuria, normal complement, and no hematuria.",
        "Nephrotic syndrome case data",
        [["Albumin", "1.8 g/dL"], ["Cholesterol", "450 mg/dL"], ["24-hour protein", "7.6 g"], ["Urine sediment", "0–3 RBC/HPF; oval fat bodies and fatty casts"], ["Complement / ANA", "Normal / negative"]],
        R37, 28,
        "Which ultrastructural change in the displayed biopsy confirms the most likely diagnosis?",
    )
    add_context(
        by_id["q-45bb041ac08246335e66"],
        "R37-case-5-advanced-CKD",
        "A 55-year-old with 16 years of proteinuria now has hypertension, edema, small kidneys, creatinine 5.0 mg/dL, BUN 90 mg/dL, anemia, and broad casts.",
        "Advanced chronic kidney disease context",
        [["BP", "170/90 mm Hg"], ["BUN / creatinine", "90 / 5.0 mg/dL"], ["Hemoglobin", "8.8 g/dL"], ["Kidney ultrasound", "Bilaterally small kidneys"], ["Sediment", "Broad granular and hyaline casts"]],
        R37, 33,
        "For counseling this patient approaching ESRD, which onset-year cohort has the highest adjusted survival throughout the displayed comparison?",
    )


def update_coverage(path: Path, additions: list[dict[str, Any]]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in additions:
        grouped[question["collection"]].append(question)
    for lecture, questions in grouped.items():
        payload["lectures"][lecture] = {
            "status": "Case coverage complete for identified lecture cases",
            "tested_summary": [question["tested_concept"] for question in questions],
            "gaps": ["Non-case lecture objectives may remain outside the scored visual bank."],
            "next_capture": "No additional capture is required for the identified table-first case set.",
            "basis": f"{len(questions)} distinct lecture cases converted to source-cited primary data-table Visual Questions in {BATCH}.",
        }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_ledger(all_questions: list[dict[str, Any]]) -> dict[str, Any]:
    active_ids = {question["question_id"] for question in all_questions}
    cases: list[dict[str, Any]] = []
    for question in DEFINITIONS:
        cases.append({
            "case_id": question["case_id"],
            "lecture": question["collection"],
            "document": question["context_table"]["source"]["document"],
            "pages": sorted({item["page"] for item in question["citations"] if item["document"].endswith(".pdf")}),
            "disposition": "new_table_visual_question",
            "question_ids": [question["question_id"]],
            "duplicate_resolution": "Repeated case and answer slides were consolidated into one scored case record.",
        })
    for case_id, lecture, document, page, question_ids in EXISTING_CASES:
        missing = [qid for qid in question_ids if qid not in active_ids]
        if missing:
            raise ValueError(f"{case_id}: missing mapped question IDs {missing}")
        cases.append({
            "case_id": case_id,
            "lecture": lecture,
            "document": document,
            "pages": [page],
            "disposition": "existing_image_visual_question_enriched_or_confirmed",
            "question_ids": question_ids,
            "duplicate_resolution": "The canonical case is represented by the listed existing image question or questions; repeated answer views were not duplicated.",
        })
    cases.sort(key=lambda row: (int(row["lecture"][1:]), row["case_id"]))
    return {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "generation_batch": BATCH,
        "scope": "User-supplied PDFs in the local Renal/Lectures folder only. No internet or outside medical sources used.",
        "method": "All lecture PDFs were inventoried, case-like pages were text-screened, repeated prompt/answer slides were consolidated by case, and each distinct defensible case was mapped to an existing or new Visual Question.",
        "summary": {
            "lecture_pdfs_inventoried": len(list(LECTURES.glob("*.pdf"))),
            "distinct_cases": len(cases),
            "new_table_visual_questions": len(DEFINITIONS),
            "existing_case_mappings": len(EXISTING_CASES),
            "unmapped_distinct_cases": 0,
        },
        "cases": cases,
        "not_scored_as_visual_cases": [
            {
                "document": "R13 Physiologist and Physician Mini-Case Study Review (Physiology) Quiz.pdf",
                "items": 10,
                "reason": "This file is a text-only micturition quiz rather than a clinical case set; the user stated that text-only questions are maintained elsewhere.",
            },
            {
                "document": "RX.1 Exam Review Questions (Clinical) RLS.pdf",
                "items": 154,
                "reason": "This is a text-question review bank. It was retained as reference material and not duplicated into the visual quiz, consistent with the user's text-question boundary.",
            },
        ],
    }


def markdown_ledger(ledger: dict[str, Any]) -> str:
    summary = ledger["summary"]
    lines = [
        "# Renal lecture case coverage ledger",
        "",
        f"Audit date {ledger['audit_date']}",
        "",
        ledger["scope"],
        "",
        "## Summary",
        "",
        f"- Lecture PDFs inventoried: {summary['lecture_pdfs_inventoried']}",
        f"- Distinct cases represented: {summary['distinct_cases']}",
        f"- New primary-table Visual Questions: {summary['new_table_visual_questions']}",
        f"- Existing case mappings retained or enriched: {summary['existing_case_mappings']}",
        f"- Unmapped distinct cases: {summary['unmapped_distinct_cases']}",
        "",
        "Repeated prompt, discussion, and answer slides were consolidated into one case entry. Text-only review banks remain outside the visual quiz as documented below.",
        "",
        "## Case mappings",
        "",
        "| Case ID | Lecture | Source pages | Disposition | Question IDs |",
        "|---|---:|---:|---|---|",
    ]
    for row in ledger["cases"]:
        lines.append(
            f"| {row['case_id']} | {row['lecture']} | {row['document']}, pp. {', '.join(map(str, row['pages']))} | {row['disposition']} | {', '.join(row['question_ids'])} |"
        )
    lines.extend(["", "## Documented exclusions", ""])
    for row in ledger["not_scored_as_visual_cases"]:
        lines.append(f"- {row['document']} ({row['items']} items). {row['reason']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(DEFINITIONS) != 81:
        raise ValueError(f"expected 81 new case questions, found {len(DEFINITIONS)}")
    physiology_additions = [question for question in DEFINITIONS if question["bank_kind"] == "physiology"]
    pathology_additions = [question for question in DEFINITIONS if question["bank_kind"] == "pathology"]
    if (len(physiology_additions), len(pathology_additions)) != (10, 71):
        raise ValueError("unexpected bank split")

    bank_specs = [
        (ROOT / "data/question-bank.json", physiology_additions, "2026-10-24-case-complete-v4-physiology"),
        (ROOT / "data/pathology/question-bank.json", pathology_additions, "2026-10-24-case-complete-v4-pathology"),
    ]
    written_questions: list[dict[str, Any]] = []
    for path, additions, version in bank_specs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["questions"] = [question for question in payload["questions"] if question.get("generation_batch") != BATCH]
        if path.name == "question-bank.json" and path.parent.name == "pathology":
            enrich_existing(payload)
        clean_additions = []
        for question in additions:
            output = dict(question)
            output.pop("bank_kind", None)
            clean_additions.append(output)
        payload["questions"].extend(clean_additions)
        payload["bank_version"] = version
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written_questions.extend(payload["questions"])

    update_coverage(ROOT / "data/coverage.json", physiology_additions)
    update_coverage(ROOT / "data/pathology/coverage.json", pathology_additions)
    ledger = build_ledger(written_questions)
    (ROOT / "reports/case-coverage-ledger-2026-10-24.json").write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "reports/case-coverage-ledger-2026-10-24.md").write_text(markdown_ledger(ledger), encoding="utf-8")

    all_new = physiology_additions + pathology_additions
    advanced = sum(question["difficulty"] == "advanced" for question in all_new)
    positions = Counter(question["correct_index"] for question in all_new)
    print(json.dumps({
        "new_questions": len(all_new),
        "physiology": len(physiology_additions),
        "pathology": len(pathology_additions),
        "new_advanced": advanced,
        "correct_positions": dict(sorted(positions.items())),
        "ledger_cases": ledger["summary"]["distinct_cases"],
    }, indent=2))


if __name__ == "__main__":
    main()
