#!/usr/bin/env python3
"""Migrate both renal visual banks to the approved five-choice clinical format.

The script uses only the existing source-grounded banks, the approved calibration
artifact, and exact case data transcribed from the cited lecture pages. It does
not read or modify the source lecture directory or any source image.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


APP = Path(__file__).resolve().parents[1]
CALIBRATION_PATH = APP / "reports/clinical-format-calibration-2026-10-23.json"
BANK_PATHS = (
    APP / "data/question-bank.json",
    APP / "data/pathology/question-bank.json",
)
REPORT_JSON = APP / "reports/clinical-format-migration-2026-10-23.json"
REPORT_MD = APP / "reports/clinical-format-migration-2026-10-23.md"
FORMAT_VERSION = "clinical-visual-v1"
BANK_VERSION = "2026-10-23-clinical-visual-v2"

DIFFICULTIES = {"foundational", "intermediate", "advanced"}
REASONING_TYPES = {"recognition", "interpretation", "mechanism", "calculation", "clinical_integration"}


def citation(document: str, page: int) -> dict[str, Any]:
    return {"document": document, "page": page}


TABLES: dict[str, dict[str, Any]] = {
    "q-0b27b50d3768e55deb80": {
        "title": "Case 1 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "3.5 mg/dL, baseline 1.9"],
            ["BUN", "40 mg/dL"],
            ["Urinalysis", "20–30 RBC/HPF, previously 10–15"],
            ["Urine protein/creatinine", "2.5 g/g"],
            ["Serology", "cANCA and anti-PR3 positive"],
            ["Anti-GBM", "Negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 9),
    },
    "q-2e38d0d490d56f79ceba": {
        "title": "Case 2 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "14 mg/dL"],
            ["BUN", "150 mg/dL"],
            ["Urinalysis", "100 RBC/HPF"],
            ["Urine protein/creatinine", "3.2 g/g"],
            ["Anti-GBM", "Positive"],
            ["ANCA", "Negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 19),
    },
    "q-8f2f17ee13acfee0ba82": {
        "title": "Case 3 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "2.5 mg/dL, baseline 1.1"],
            ["BUN", "30 mg/dL"],
            ["Urinalysis", "20 RBC/HPF"],
            ["Urine protein/creatinine", "1.5 g/g"],
            ["Serology", "ANA and ANCA negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 32),
    },
    "q-ec9f98a4f22d55a2d666": {
        "title": "Case 4 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "4.2 mg/dL"],
            ["BUN", "60 mg/dL"],
            ["Urinalysis", "80 RBC/HPF, protein 3+"],
            ["Complement", "C3 decreased, C4 normal"],
            ["Serology", "ANA, ANCA, and anti-GBM negative"],
            ["Infection testing", "HBV and HCV negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 44),
    },
    "q-598b696f645f4af99667": {
        "title": "Case 5 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "2.29 mg/dL"],
            ["BUN", "28 mg/dL"],
            ["Urinalysis", "0–5 RBC and WBC/HPF"],
            ["Urine protein/creatinine", "3.1 g/g"],
            ["Serology", "C3, C4, ANA, ANCA, anti-GBM, HBV, and HCV normal or negative"],
            ["Examination", "Edema"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 56),
    },
    "q-bfe5f4128f4b2a8c16bf": {
        "title": "Case 6 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "2.5 mg/dL"],
            ["BUN", "30 mg/dL"],
            ["Urinalysis", "0–5 RBC and WBC/HPF"],
            ["Urine protein/creatinine", "3.5 g/g"],
            ["Serology", "C3, C4, ANA, ANCA, anti-GBM, anti-PLA2R, HBV, and HCV normal or negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 68),
    },
    "q-170c158f2f1c57d9d8a8": {
        "title": "Case 7 nephrotic presentation",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "1.1 mg/dL"],
            ["BUN", "10 mg/dL"],
            ["Serum albumin", "1.4 g/dL"],
            ["Urinalysis", "0–5 RBC and WBC/HPF"],
            ["Urine protein/creatinine", "9.5 g/g"],
            ["Serology", "C3, C4, ANA, ANCA, anti-GBM, HBV, and HCV normal or negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 76),
    },
    "q-92c2b64905147517cf11": {
        "title": "Case 8 laboratory data",
        "placement": "additional",
        "columns": ["Test", "Result"],
        "rows": [
            ["Serum creatinine", "1.6 mg/dL"],
            ["BUN", "17 mg/dL"],
            ["Urinalysis", "5 RBC/HPF, 0 WBC/HPF"],
            ["Urine protein/creatinine", "2.5 g/g"],
            ["Clinical course", "Renal decline and proteinuria over 6 months during bevacizumab treatment"],
            ["Serology", "C3, C4, ANA, ANCA, anti-GBM, HBV, and HCV normal or negative"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 83),
    },
    "q-a1fe52e89d8b98e9cb80": {
        "title": "Case 9 laboratory data",
        "placement": "additional",
        "columns": ["Feature", "Finding"],
        "rows": [
            ["Recent treatment", "One week of antibiotics after abscess drainage"],
            ["Serum creatinine", "2.9 mg/dL"],
            ["BUN", "25 mg/dL"],
            ["Urinalysis", "0–5 RBC/HPF and 5 WBC/HPF"],
            ["Urine protein/creatinine", "0.3 g/g"],
            ["CBC", "Eosinophilia"],
            ["Examination", "Rash"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 92),
    },
    "q-d07ebe2b055205325736": {
        "title": "Case 10 laboratory data",
        "placement": "additional",
        "columns": ["Feature", "Finding"],
        "rows": [
            ["Clinical history", "Recent diagnosis of multiple myeloma"],
            ["Serum creatinine", "1.3 mg/dL"],
            ["BUN", "13 mg/dL"],
            ["Urinalysis", "0–5 RBC and WBC/HPF"],
            ["Urine protein/creatinine", "5.3 g/g"],
            ["SPEP and IFE", "Free lambda light-chain monoclonal protein"],
        ],
        "source": citation("R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf", 98),
    },
    "q-abe4d54f7689d70f2a52": {
        "title": "Admission chemistry and blood gas",
        "placement": "primary",
        "columns": ["Test", "Result", "Lecture reference"],
        "rows": [
            ["Na+", "150 mEq/L", "135–145"],
            ["K+", "5.0 mEq/L", "3.5–5.2"],
            ["Cl−", "115 mEq/L", "96–106"],
            ["HCO3−", "12 mEq/L", "24"],
            ["BUN", "36 mg/dL", "7–23"],
            ["Creatinine", "1.2 mg/dL", "0.6–1.2"],
            ["Glucose", "700 mg/dL", "70–100"],
            ["ABG", "pH 7.28, pCO2 26 mmHg", "pH 7.35–7.45, pCO2 40"],
        ],
        "note": "Urinalysis shows glucose 3+ and ketones 2+.",
        "source": citation("R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 3),
    },
    "q-710f408c5b8b9fa833d8": {
        "title": "Admission chemistry and blood gas",
        "placement": "primary",
        "columns": ["Test", "Result", "Lecture reference"],
        "rows": [
            ["Na+", "138 mEq/L", "135–145"],
            ["K+", "2.3 mEq/L", "3.5–5.2"],
            ["Cl−", "90 mEq/L", "96–106"],
            ["HCO3−", "36 mEq/L", "22–28"],
            ["BUN", "34 mg/dL", "7–23"],
            ["Creatinine", "1.4 mg/dL", "0.6–1.2"],
            ["ABG", "pH 7.48, pCO2 47 mmHg", "pH 7.35–7.45, pCO2 36–44"],
            ["Urine", "Osmolality 300 mOsm/kg, pH 5", "Specific gravity 1.010"],
        ],
        "source": citation("R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 6),
    },
    "q-8ff1018d10271a0c9da6": {
        "title": "Serial chemistry and blood-gas data",
        "placement": "primary",
        "columns": ["Test", "Day 1", "Day 4", "Day 6"],
        "rows": [
            ["Na+", "135", "137", "135 mEq/L"],
            ["K+", "4.7", "3.9", "4.0 mEq/L"],
            ["Cl−", "92", "85", "95 mEq/L"],
            ["HCO3−", "38", "43", "31 mEq/L"],
            ["pH", "7.26", "7.50", "7.42"],
            ["pCO2", "80", "54", "45 mmHg"],
            ["pO2", "40", "53", "65 mmHg"],
        ],
        "source": citation("R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 10),
    },
    "q-21b8f4b53120003060f7": {
        "title": "Case 4 chemistry and blood gas",
        "placement": "primary",
        "columns": ["Test", "Result", "Lecture reference"],
        "rows": [
            ["Na+", "140 mEq/L", "135–145"],
            ["K+", "5.5 mEq/L", "3.5–5.2"],
            ["Cl−", "105 mEq/L", "96–106"],
            ["HCO3−", "6 mEq/L", "22–28"],
            ["BUN", "30 mg/dL", "7–23"],
            ["Creatinine", "1.5 mg/dL", "0.6–1.2"],
            ["Glucose", "90 mg/dL", "70–100"],
            ["ABG", "pH 7.05, pCO2 16 mmHg", "pH 7.35–7.45, pCO2 36–44"],
            ["Measured osmolality", "340 mOsm/kg", "Blood ketones trace positive"],
        ],
        "source": citation("R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf", 14),
    },
    "q-10c43640a081a7dbe4d8": {
        "title": "HAART case timeline",
        "placement": "additional",
        "columns": ["Feature", "Course data"],
        "rows": [
            ["Age", "27 years"],
            ["Recent treatment", "Tenofovir alafenamide, atazanavir, and efavirenz"],
            ["Baseline creatinine", "0.8 mg/dL"],
            ["Follow-up creatinine", "2.0 mg/dL"],
            ["Urinalysis", "Crystals present"],
        ],
        "source": citation("R36 Treatment Pitfalls & AI Use Case Studies (Clinical) RLS.pdf", 31),
    },
    "q-b2f79cb7bb6d9908c0c6": {
        "title": "Postoperative case context",
        "placement": "additional",
        "columns": ["Feature", "Course data"],
        "rows": [
            ["Age", "82 years"],
            ["Procedure", "L2–L3 laminectomy and fusion"],
            ["Postoperative treatment", "IV ceftriaxone for UTI and oxycodone for pain"],
            ["Chronic medication", "Oxybutynin for overactive bladder"],
            ["Urine output", "No urination for 12 hours"],
            ["Urinalysis", "Protein 2+"],
        ],
        "source": citation("R36 Treatment Pitfalls & AI Use Case Studies (Clinical) RLS.pdf", 33),
    },
}


CALIBRATION_PROMPTS: dict[str, tuple[str, str]] = {
    "q-a6afe0b1b490ac5016e5": (
        "An experimental maneuver causes isolated moderate constriction of the efferent arteriole.",
        "Using the masked hemodynamic table, which complete pattern is most likely?",
    ),
    "q-50974bb5a3c9a279897d": (
        "A patient receives an acute H+ or HCO3− load at time zero.",
        "At approximately two hours, which defense process in the graph is most nearly complete?",
    ),
    "q-82c1141df8042112c8e6": (
        "A hospitalized patient receiving antiviral therapy has an abnormal urine sediment.",
        "Which substance most likely produced the displayed crystals?",
    ),
    "q-b162e3a354041916d035": (
        "An adult begins one of the diuretic classes listed in the masked comparison table. Follow-up urine studies show increased sodium excretion but decreased calcium excretion.",
        "Which class was most likely prescribed?",
    ),
    "q-81fd2def73af26c57610": (
        "A young man has persistent hematuria, progressive kidney disease, sensorineural hearing loss, and a family history of renal failure.",
        "Which ultrastructural finding is illustrated by the electron micrograph?",
    ),
    "q-ec9f98a4f22d55a2d666": (
        "A 7-year-old boy develops acute kidney injury and hematuria two weeks after Streptococcus pyogenes pharyngitis.",
        "Which immunofluorescence pattern is shown in the IgG image?",
    ),
    "q-abe4d54f7689d70f2a52": (
        "A 30-year-old man presents after three days of lethargy, fever, and diarrhea. He is thirsty and orthostatic, and urinalysis shows glucosuria and ketonuria.",
        "Using the admission values, what is his serum anion gap in mEq/L?",
    ),
    "q-6af74487eae4c4383e53": (
        "A male newborn has bilateral hydronephrosis and a weak urinary stream.",
        "Which diagnosis is most consistent with the voiding cystourethrogram?",
    ),
    "q-6b1834e1b412467dda3d": (
        "A patient with multifocal renal tumors has the accompanying retinal lesion.",
        "Which molecular abnormality best unifies these findings?",
    ),
    "q-bb5e1efc969b05264bb4": (
        "A patient with a renal malignancy undergoes staging.",
        "Which metastatic pattern is present on the chest CT?",
    ),
}


MANUAL_FIFTH: dict[str, tuple[str, str, dict[str, Any] | None]] = {
    "q-3bde81ca5b28287df5ec": (
        "Juxtaglomerular cells",
        "Juxtaglomerular cells occupy the arteriolar wall rather than the position identified by leader line A.",
        None,
    ),
    "q-335788742cee7918e165": (
        "Juxtaglomerular cells",
        "Juxtaglomerular cells are located in the afferent arteriolar wall, not at the region marked by leader line B.",
        None,
    ),
    "q-475de70225eeef23855f": (
        "Juxtaglomerular cells",
        "Juxtaglomerular cells are part of the vascular-pole apparatus and do not form the labeled capsule layer.",
        None,
    ),
    "q-3e509a58fcb1574b2268": (
        "Cortex at both edges, with medulla limited to the center",
        "The displayed field shows a cortex-to-medulla transition across the image rather than cortex returning at the opposite edge.",
        None,
    ),
    "q-05e3d3bf0d917b9ef796": (
        "Proximal tubule",
        "A proximal tubule is not the labeled medullary profile whose wall contains the most conspicuous elongated mitochondrial profiles.",
        None,
    ),
    "q-39406668183120b7e6e1": (
        "Macula densa",
        "The macula densa is the specialized distal tubular plaque at the vascular pole, not the vessel identified by leader line C.",
        None,
    ),
    "q-ea092b490867e3c79ea2": (
        "Macula densa",
        "The macula densa is a specialized tubular cell group and does not correspond to the vessel identified by leader line D.",
        None,
    ),
    "q-52e9573e732419dd243d": (
        "The lateral border between adjacent proximal-tubule cells",
        "The lateral cell border is distinct from the projecting luminal surface that marks the apical face.",
        None,
    ),
    "q-a7bcc9d78974450b3134": (
        "RPF unchanged; Pgc unchanged",
        "The displayed efferent-arteriolar response changes both renal plasma flow and glomerular capillary pressure rather than leaving both unchanged.",
        None,
    ),
    "q-ad64185b2ff11188e740": (
        "RPF unchanged; Pgc unchanged",
        "The displayed afferent-arteriolar response changes renal plasma flow and glomerular capillary pressure rather than leaving both unchanged.",
        None,
    ),
    "q-14b655ba17ab05463b8f": (
        "RPF unchanged; Pgc unchanged",
        "The displayed efferent-arteriolar response changes both renal plasma flow and glomerular capillary pressure rather than leaving both unchanged.",
        None,
    ),
    "q-755ce2a85a3b42196812": (
        "RPF unchanged; Pgc unchanged",
        "The displayed afferent-arteriolar response changes renal plasma flow and glomerular capillary pressure rather than leaving both unchanged.",
        None,
    ),
    "q-ba53855a7abca217a1f0": (
        "3 Cl⁻",
        "NKCC2 cotransports two chloride ions at the labeled site, so three chloride ions is not the displayed stoichiometry.",
        None,
    ),
    "q-6fc85708e5faaab2db56": (
        "β-intercalated cell",
        "A β-intercalated cell uses acid-base transport with the opposite polarization of an α-intercalated cell rather than the NCC-only pattern shown here.",
        citation("R7 Countercurrent Mechanism, Distal Tubule & Collecting Duct (Physiology) RLS.pdf", 16),
    ),
    "q-08c4c6210127989f7e5f": (
        "β-intercalated cell",
        "A β-intercalated cell uses acid-base transport rather than the combined apical NCC and ENaC pattern shown here.",
        citation("R7 Countercurrent Mechanism, Distal Tubule & Collecting Duct (Physiology) RLS.pdf", 16),
    ),
    "q-41417d74547700290012": (
        "It widens initially and then returns to baseline despite continued acid accumulation",
        "Continued fixed-acid accumulation expands the displayed unmeasured-anion span rather than returning it to baseline.",
        None,
    ),
    "q-56c3332ad4899df12189": (
        "No residual contour change after pressure is released",
        "The photograph shows a persistent indentation after pressure, not immediate restoration of the skin contour.",
        None,
    ),
    "q-9fca121cb3e5cc78eb2d": (
        "It plateaus after a small initial rise",
        "The plotted relationship continues to rise across the displayed GFR range rather than reaching an early plateau.",
        None,
    ),
    "q-782f64afdebc3e7de4b5": (
        "Corticomedullary junction",
        "The corticomedullary junction is an internal boundary, not the continuous outer band marked C.",
        None,
    ),
    "q-88887ad51cf5d36c5c91": (
        "Atazanavir",
        "The R15 lecture assigns the displayed sunburst or plate-like needle pattern to indinavir rather than atazanavir.",
        citation("R36 Treatment Pitfalls & AI Use Case Studies (Clinical) RLS.pdf", 31),
    ),
    "q-7b49801deb314fa94358": (
        "Atazanavir",
        "The R15 lecture assigns the shocks-of-wheat or shell-shaped pattern to sulfadiazine rather than atazanavir.",
        citation("R36 Treatment Pitfalls & AI Use Case Studies (Clinical) RLS.pdf", 31),
    ),
    "q-f782a278dd8834e013ef": (
        "Uric acid",
        "Uric acid forms angular rhomboids or needles rather than the radiating rosette of elongated prisms shown here.",
        citation("R15 Urinalysis RLS.pdf", 32),
    ),
    "q-f17377a720996291edb9": (
        "Red blood cell cast",
        "A red blood cell cast contains recognizable erythrocytes rather than the dense coarse granules visible in this cast.",
        citation("R15 Urinalysis RLS.pdf", 23),
    ),
    "q-5465f03675e8bc97a5c6": (
        "Subendothelial electron-dense deposits",
        "Subendothelial deposits lie on the endothelial side of the glomerular basement membrane rather than forming a continuous dense ribbon within it.",
        citation("R18 Renal Pathology - Glomerular Diseases (Part 1) (Nephritic Diseases) (Pathology) RLS.pdf", 58),
    ),
    "q-710f408c5b8b9fa833d8": (
        "Mixed metabolic alkalosis and primary respiratory acidosis",
        "The measured pCO₂ is appropriate compensation for the metabolic alkalosis rather than evidence of an additional primary respiratory acidosis.",
        None,
    ),
    "q-8ff1018d10271a0c9da6": (
        "Chronic respiratory acidosis with appropriate renal compensation",
        "The alkalemic day-4 values and marked bicarbonate elevation do not fit isolated chronic respiratory acidosis with appropriate compensation.",
        None,
    ),
    "q-1fef41f50349faa42368": (
        "No net H⁺ secretion or bicarbonate reabsorption",
        "The displayed alpha-intercalated-cell transporters mediate apical hydrogen secretion and basolateral bicarbonate exit rather than no net transport.",
        None,
    ),
    "q-c7dad792051d8afa32aa": (
        "Monitor; 4+",
        "The G4 and A3 color category maps to referral rather than monitoring at the highest follow-up frequency.",
        None,
    ),
    "q-f66197b322f379f5ac25": (
        "Monitor; 3",
        "The low-risk G2 and A1 cell indicates annual monitoring rather than three visits per year.",
        None,
    ),
    "q-3cd6baa7e6b44fa3e133": (
        "Monitor; 3",
        "The G3a and A1 cell maps to the lower monitoring frequency shown by its color, not three visits per year.",
        None,
    ),
    "q-beb8c5de3fd2bb59901e": (
        "Refer; 2",
        "The G3b and A3 color category requires the higher referral frequency shown in the table rather than referral twice yearly.",
        None,
    ),
    "q-ce7f4e2a31d55c620f47": (
        "Monitor; 4+",
        "The G5 and A1 category is a referral cell, so monitoring alone does not match the retained color code.",
        None,
    ),
    "q-47527c6b863be8ce5803": (
        "About 300 mOsm/kg",
        "The shaded thirst zone begins near 295 mOsm/kg on the x-axis, before 300 mOsm/kg.",
        None,
    ),
    "q-01b7c5fed40309655f6f": (
        "Symmetric perioral erythema without swelling",
        "The photograph shows marked lower-lip swelling rather than isolated redness with preserved lip contour.",
        None,
    ),
    "q-50a2ba6efde89040617e": (
        "The 2005 and 2015 cohorts are tied for highest survival",
        "At 36 months the 2015 curve remains above the 2005 curve, so those cohorts are not tied.",
        None,
    ),
    "q-a74667d9787b195b1d47": (
        "No circles",
        "The loop-diuretic cell shows the greatest relative diuresis rather than no diuretic effect.",
        None,
    ),
    "q-dcd494abd0d9afd12719": (
        "15%",
        "The lecture table gives a higher maximum fraction of filtered sodium excreted for loop diuretics than 15%.",
        None,
    ),
    "q-063e286c74c08367b456": (
        "Afferent arteriole",
        "The afferent arteriole enters at the vascular pole and is distinct from the intraglomerular mesangial region marked E.",
        None,
    ),
    "q-0d716ad30cd75400c495": (
        "Efferent arteriole",
        "The efferent arteriole exits the vascular pole and is not the network of capillary loops identified by leader line H.",
        None,
    ),
    "q-7eef182317a688e4cd57": (
        "Fenestrated endothelium",
        "Fenestrated endothelium lines the capillary, whereas region D is the lumen that contains circulating blood.",
        None,
    ),
    "q-8012d83a0df314856317": (
        "Endothelial cell",
        "An endothelial cell forms the capillary lining, while the marked region contains a blood cell within the lumen.",
        None,
    ),
    "q-151080dedf0eb5fbc074": (
        "Isotonic volume contraction",
        "The displayed hypertonic expansion increases extracellular volume and osmolality rather than producing isotonic contraction.",
        None,
    ),
    "q-1fa7083ab6bff16fda88": (
        "Isotonic volume contraction",
        "The displayed hypotonic expansion increases extracellular volume and lowers osmolality rather than producing isotonic contraction.",
        None,
    ),
    "q-532612d732c68bb725bb": (
        "Isotonic volume contraction",
        "The displayed compartment change is isotonic expansion, not a reduction in extracellular volume with unchanged osmolality.",
        None,
    ),
    "q-2d9bd6494307d74925ea": (
        "Basolateral membrane infoldings",
        "Basolateral infoldings surround the elongated mitochondria but are not the dark intracellular profiles indicated by the yellow arrows.",
        None,
    ),
    "q-300672cdf3ccd12a6fe6": (
        "Tubular basement membrane",
        "The tubular basement membrane lies along the basal surface, not along the luminal border marked by the red arrows.",
        None,
    ),
    "q-c8a44df01bdcf3f15f3a": (
        "Renin",
        "Renin initiates the upstream cascade, whereas the central mediator branching to the displayed target organs is angiotensin II.",
        None,
    ),
    "q-d697c9ec879eabf6ea04": (
        "H⁺ and HCO₃⁻",
        "Luminal carbonic anhydrase produces carbon dioxide and water for entry rather than transporting hydrogen and bicarbonate together across the apical membrane.",
        None,
    ),
    "q-030275d9ade752ee5929": (
        "One NH₄⁺ toward lumen and one new HCO₃⁻ toward blood",
        "The diagram shows two ammonium ions entering the lumen and two newly generated bicarbonate ions entering blood, not one of each.",
        None,
    ),
    "q-e864a03270bd14bd2c2c": (
        "White blood cell casts",
        "White blood cell casts contain leukocytes, whereas the displayed elongated aggregates are composed of red blood cells.",
        None,
    ),
    "q-f4edb6a88dfb7adf4594": (
        "HCO₃⁻ secretion into the lumen",
        "The pictured apical exchanger secretes hydrogen ions while supporting bicarbonate reclamation rather than bicarbonate secretion.",
        None,
    ),
    "q-722b7858e5a92ddc1e7f": (
        "Paracellular phosphate reabsorption",
        "The lumen-positive voltage shown drives paracellular calcium and magnesium reabsorption, not the proposed phosphate pathway.",
        None,
    ),
    "q-32f1fc21d8369a1ed2a5": (
        "More water entry from the tubular lumen",
        "V2-receptor antagonism reduces apical AQP2 insertion and therefore decreases, rather than increases, water entry from the lumen.",
        None,
    ),
    "q-a27d1fc8468293e22e48": (
        "Numerous small cysts confined to the medulla",
        "The gross specimen shows variably sized cysts replacing an enlarged kidney rather than small cysts limited to the medulla.",
        None,
    ),
    "q-5c57c8f4a76e05157c43": (
        "Three collecting pathways from one kidney",
        "The diagram demonstrates duplication with two collecting pathways, not three separate drainage systems.",
        None,
    ),
    "q-a410a40ddd2f6de035fa": (
        "A duplicated collecting system",
        "A duplicated collecting system creates two drainage pathways, whereas the CT shows a midline parenchymal isthmus.",
        None,
    ),
    "q-3e5339319b5077e47675": (
        "Pleural thickening without pleural air",
        "The CT shows pleural air with lung collapse rather than isolated pleural thickening.",
        None,
    ),
    "q-e87f5f4ce7ab83f990d5": (
        "Intermediate signal in both A and B",
        "Simple fluid shows the displayed dark-to-bright T1/T2 reversal rather than intermediate signal in both panels.",
        None,
    ),
    "q-a39cf3bf7feed2f220c8": (
        "About 290 mOsm/kg",
        "The red ADH curve begins its sustained rise near 280 mOsm/kg, before 290 mOsm/kg.",
        None,
    ),
    "q-7d62284417c20b1ff7f3": (
        "Nonpitting edema",
        "The persistent depressions demonstrate pitting edema rather than swelling that retains no indentation.",
        None,
    ),
    "q-0d555a4ccc759df76976": (
        "Unilateral basilar air-space opacity",
        "The radiograph shows diffuse bilateral air-space opacity rather than a unilateral basilar process.",
        None,
    ),
    "q-128c465df059f88c355a": (
        "Isolated wrist drop",
        "The hand posture is a carpopedal spasm pattern rather than isolated weakness producing wrist drop.",
        None,
    ),
    "q-29173580e3bf505e1952": (
        "Continuous ambulatory peritoneal dialysis manual exchange",
        "The pictured cycler setup represents automated peritoneal dialysis rather than a manual continuous ambulatory exchange.",
        None,
    ),
    "q-e00a00e1b65c1d22e087": (
        "Type I with eosinophilic cells and hereditary leiomyomatosis syndrome",
        "The displayed type II papillary tumor is eosinophilic and associated with hereditary leiomyomatosis, not the proposed type I combination.",
        None,
    ),
    "q-10c43640a081a7dbe4d8": (
        "Radial sunburst cluster",
        "The HAART-case sediment shows long narrow needles rather than a radial sunburst arrangement.",
        None,
    ),
    "q-b2f79cb7bb6d9908c0c6": (
        "A simple cortical cyst",
        "The asterisk marks branching collecting-system dilation rather than a discrete simple cyst in the cortex.",
        None,
    ),
}


def normalize(text: str) -> str:
    text = text.casefold().replace("−", "-").replace("–", "-")
    text = text.replace("mesangial", "mesangium")
    text = re.sub(r"[^a-z0-9+\-]+", " ", text)
    return " ".join(text.split())


def option_shape(text: str) -> str:
    norm = normalize(text)
    if "→" in text:
        return "sequence"
    if re.fullmatch(r"(?:about )?\d+(?:\.\d+)?(?: \w+(?:/\w+)?)?", norm):
        return "numeric"
    if re.search(r"\b(afferent|efferent|arteriole)\b", norm):
        return "intervention"
    if any(token in text for token in ("↑", "↓", "↔", "→")) or re.search(
        r"\b(increase|decrease|unchanged|rises|falls|dilates|constricts)\b", norm
    ):
        return "direction"
    if ";" in text or " and " in norm or "," in text:
        return "composite"
    return "entity"


def majority_shape(options: list[str]) -> str:
    counts = Counter(option_shape(option) for option in options)
    return counts.most_common(1)[0][0]


def too_similar(candidate: str, options: list[str]) -> bool:
    cand = set(normalize(candidate).split())
    if not cand:
        return True
    for option in options:
        other = set(normalize(option).split())
        candidate_norm = normalize(candidate)
        option_norm = normalize(option)
        if candidate_norm == option_norm:
            return True
        if len(candidate_norm) > 3 and len(option_norm) > 3 and (
            f" {candidate_norm} " in f" {option_norm} " or f" {option_norm} " in f" {candidate_norm} "
        ):
            return True
        union = cand | other
        if union and len(cand & other) / len(union) >= 0.72:
            return True
    return False


def context_for(question: dict[str, Any]) -> str:
    existing = question.get("case_context", "").strip()
    if existing:
        return existing
    category = question.get("category", "").casefold()
    qtype = question.get("question_type", "").casefold()
    if category in {"ct", "mri", "ultrasound", "radiograph", "chest ct", "chest radiograph", "ct reconstruction", "imaging"}:
        return "A patient undergoes renal or urinary tract imaging as part of a focused diagnostic evaluation."
    if "histology" in category or category in {"electron microscopy", "em", "tem", "sem", "immunofluorescence", "gross pathology"}:
        return "A renal specimen is reviewed to correlate the displayed morphology with the clinical differential."
    if "urine" in category:
        return "A urine-sediment specimen is examined during the evaluation of a renal or urinary disorder."
    if "clinical photo" in category or "clinical photograph" in category:
        return "A patient with a renal or systemic disorder has the accompanying clinical finding."
    if "graph" in category:
        return "A renal physiology study records the relationship displayed in the graph."
    if "table" in category:
        return "A clinician uses the accompanying course table to compare renal findings or treatment effects."
    if any(word in qtype for word in ("structure", "cell", "localization", "view", "orientation")):
        return "A renal micrograph or schematic is being used to orient the nephron and glomerular filtration apparatus."
    return "A renal physiology problem is analyzed using the accompanying course diagram."


def lead_in_for(question: dict[str, Any], scenario: str) -> str:
    # The source bank's precise visual question remains the safest non-leaking
    # lead-in. Clinical calibration items receive their separately authored
    # vignette and lead-in in CALIBRATION_PROMPTS.
    stem = question["stem"].strip()
    if scenario and stem.casefold().startswith(scenario.casefold()):
        remainder = stem[len(scenario):].lstrip(" .:;")
        if remainder:
            return remainder[:1].upper() + remainder[1:]
    return stem


def first_pdf_citation(question: dict[str, Any]) -> dict[str, Any] | None:
    for item in question.get("citations", []):
        if str(item.get("document", "")).casefold().endswith(".pdf") and item.get("page") is not None:
            return copy.deepcopy(item)
    return None


def modality_family(category: str) -> str:
    value = category.casefold()
    if any(word in value for word in ("ct", "mri", "ultrasound", "radiograph", "imaging")):
        return "imaging"
    if any(word in value for word in ("histology", "microscopy", "tem", "sem", "immunofluorescence", "em", "gross pathology", "urine")):
        return "microscopy"
    if "table" in value:
        return "table"
    if "graph" in value:
        return "graph"
    if "diagram" in value:
        return "diagram"
    if "clinical" in value:
        return "clinical"
    return value


def question_family(qtype: str) -> str:
    value = qtype.casefold()
    if any(word in value for word in ("structure", "cell", "localization", "identification", "finding", "morphology", "pattern", "classification", "ultrastructural")):
        return "recognition"
    if any(word in value for word in ("mechanism", "pathway", "transporter", "route", "physiologic")):
        return "mechanism"
    if any(word in value for word in ("direction", "hemodynamic", "graph", "table", "comparison", "interpretation", "calculation")):
        return "interpretation"
    if "association" in value:
        return "association"
    return value


def choose_fifth(question: dict[str, Any], all_questions: list[dict[str, Any]]) -> tuple[str, str, dict[str, Any]]:
    current = list(question["options"])
    target_shape = majority_shape(current)
    candidates: list[tuple[int, dict[str, Any], str]] = []
    for other in all_questions:
        if other["question_id"] == question["question_id"] or other.get("source_group_id") == question.get("source_group_id"):
            continue
        if other.get("bank_id") != question.get("bank_id"):
            continue
        if modality_family(other.get("category", "")) != modality_family(question.get("category", "")):
            continue
        if question_family(other.get("question_type", "")) != question_family(question.get("question_type", "")):
            continue
        option = other["options"][other["correct_index"]]
        if option_shape(option) != target_shape or too_similar(option, current):
            continue
        score = 0
        score += 16 if other.get("collection") == question.get("collection") else 0
        score += 10 if other.get("question_type") == question.get("question_type") else 0
        score += 8 if other.get("category") == question.get("category") else 0
        score -= abs(len(option.split()) - round(sum(len(value.split()) for value in current) / len(current)))
        candidates.append((score, other, option))
    if candidates:
        candidates.sort(key=lambda item: (-item[0], normalize(item[2]), item[1]["question_id"]))
        _, source, option = candidates[0]
        source_clue = source.get("visual_clues", [source.get("tested_concept", "the alternate finding")])[0]
        source_clue = source_clue[:1].lower() + source_clue[1:] if source_clue else "the alternate finding"
        target_clue = question.get("visual_clues", [question.get("tested_concept", "a different finding")])[0]
        target_clue = target_clue[:1].lower() + target_clue[1:] if target_clue else "a different finding"
        rationale = f"{option} is associated with {source_clue}. The displayed target instead shows {target_clue}."
        basis = {
            "legacy_question_id": source["question_id"],
            "tested_concept": source.get("tested_concept"),
            "citation": first_pdf_citation(source),
        }
        return option, rationale, basis
    target_clue = question.get("visual_clues", [question.get("tested_concept", "a single directional result")])[0]
    target_clue = target_clue[:1].lower() + target_clue[1:] if target_clue else "a single directional result"
    fallbacks = {
        "direction": (
            "A biphasic response",
            f"The displayed target shows {target_clue}. It does not reverse direction after an initial change.",
        ),
        "numeric": (
            "0",
            "A value of 0 does not follow from the displayed measurements or the calculation requested in the stem.",
        ),
        "composite": (
            "No regional or physiologic transition across the displayed field",
            "The displayed field contains a definite regional or physiologic transition, so an unchanged composite does not fit.",
        ),
        "intervention": (
            "No change in either arteriole",
            "The source diagram shows an active arteriolar intervention rather than the unchanged baseline state.",
        ),
        "entity": (
            "A different structure outside the indicated region",
            "The tested target lies within the indicated region, so an unmarked structure elsewhere in the field is less appropriate.",
        ),
    }
    if target_shape == "sequence":
        parts = [part.strip() for part in current[0].split("→")]
        existing_sequences = {normalize(option) for option in current}
        for order in itertools.permutations(parts):
            option = " → ".join(order)
            if normalize(option) not in existing_sequences:
                rationale = "This ordering conflicts with the direction and layer sequence traced by the displayed arrow."
                return option, rationale, {"legacy_question_id": None, "tested_concept": "sequence permutation", "citation": None}
        raise ValueError(f"{question['question_id']}: could not construct a distinct sequence distractor")
    option, rationale = fallbacks[target_shape]
    if too_similar(option, current):
        option += " in this experiment"
    return option, rationale, {"legacy_question_id": None, "tested_concept": "format fallback", "citation": None}


def classify_reasoning(question: dict[str, Any], context_table: dict[str, Any] | None) -> str:
    qtype = question.get("question_type", "").casefold()
    lead_in = question.get("lead_in", question.get("stem", "")).casefold()
    if "calculation" in qtype or "calculate" in lead_in or "anion gap" in lead_in and "what is" in lead_in:
        return "calculation"
    if context_table or any(
        phrase in qtype
        for phrase in (
            "clinical association",
            "clinical microscopy association",
            "clinicopathologic",
            "hereditary oncology association",
            "oncologic staging imaging",
            "clinical radiology",
        )
    ):
        return "clinical_integration"
    if any(word in qtype for word in ("mechanism", "pathway", "transporter", "route", "ion identification", "ion stoichiometry")):
        return "mechanism"
    if any(word in qtype for word in ("direction", "interpretation", "prediction", "comparison", "orientation", "table", "graph")):
        return "interpretation"
    return "recognition"


def classify_difficulty(question: dict[str, Any], context_table: dict[str, Any] | None, reasoning_type: str) -> str:
    qtype = question.get("question_type", "").casefold()
    if reasoning_type == "calculation" or "integrated mechanism" in qtype or context_table and context_table["placement"] == "primary":
        return "advanced"
    if reasoning_type == "recognition":
        return "foundational"
    return "intermediate"


GENERIC_CONTEXTS = {
    "A patient undergoes renal or urinary tract imaging as part of a focused diagnostic evaluation.",
    "A renal specimen is reviewed to correlate the displayed morphology with the clinical differential.",
    "A urine-sediment specimen is examined during the evaluation of a renal or urinary disorder.",
    "A patient with a renal or systemic disorder has the accompanying clinical finding.",
    "A renal physiology study records the relationship displayed in the graph.",
    "A clinician uses the accompanying course table to compare renal findings or treatment effects.",
    "A renal micrograph or schematic is being used to orient the nephron and glomerular filtration apparatus.",
    "A renal physiology problem is analyzed using the accompanying course diagram.",
}


def restore_source_question(
    question: dict[str, Any],
    report_map: dict[str, dict[str, Any]],
    calibration_ids: set[str],
    baseline_citations: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    if question.get("format_version") != FORMAT_VERSION:
        return question
    restored = copy.deepcopy(question)
    legacy_id = restored["legacy_question_id"]
    legacy_citations = report_map.get(legacy_id, {}).get("legacy_citations") or baseline_citations.get(legacy_id)
    if legacy_citations is None:
        raise ValueError(f"{legacy_id}: original citations are unavailable for a clean rerun")
    restored["citations"] = copy.deepcopy(legacy_citations)
    if legacy_id not in calibration_ids:
        fifth = report_map[legacy_id]["fifth_distractor"]
        correct_option = restored["options"][restored["correct_index"]]
        index = restored["options"].index(fifth)
        restored["options"].pop(index)
        restored["choice_rationales"].pop(index)
        restored["correct_index"] = restored["options"].index(correct_option)
    restored["question_id"] = legacy_id
    restored["stem"] = restored["legacy_stem"]
    if restored.get("case_context") in GENERIC_CONTEXTS:
        restored["case_context"] = ""
    for field in (
        "legacy_question_id",
        "legacy_stem",
        "format_version",
        "scenario",
        "lead_in",
        "context_table",
        "fifth_distractor_basis",
        "difficulty",
        "reasoning_type",
    ):
        restored.pop(field, None)
    return restored


def append_unique_citation(citations: list[dict[str, Any]], item: dict[str, Any] | None) -> None:
    if not item:
        return
    key = (item.get("document"), item.get("page"))
    if all((c.get("document"), c.get("page")) != key for c in citations):
        citations.append(copy.deepcopy(item))


def git_head_citations(relative_path: str) -> dict[str, list[dict[str, Any]]]:
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=APP,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    return {question["question_id"]: copy.deepcopy(question.get("citations", [])) for question in payload["questions"]}


def rotate_to_index(options: list[str], rationales: list[str], correct_index: int, target: int) -> tuple[list[str], list[str], int]:
    pairs = list(zip(options, rationales))
    correct_pair = pairs.pop(correct_index)
    pairs.insert(target, correct_pair)
    return [p[0] for p in pairs], [p[1] for p in pairs], target


def question_id(legacy_id: str, scenario: str, lead_in: str, options: list[str]) -> str:
    payload = json.dumps([legacy_id, scenario, lead_in, options, FORMAT_VERSION], ensure_ascii=False, sort_keys=True)
    return "q-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def validate_table(table: dict[str, Any]) -> None:
    assert table["placement"] in {"primary", "additional"}
    assert table["columns"] and table["rows"]
    width = len(table["columns"])
    assert all(len(row) == width for row in table["rows"])
    assert table["source"]["document"].endswith(".pdf")
    assert isinstance(table["source"]["page"], int) and table["source"]["page"] > 0


def main() -> None:
    calibration_payload = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    calibration = {item["legacy_question_id"]: item for item in calibration_payload["questions"]}
    prior_report_map: dict[str, dict[str, Any]] = {}
    if REPORT_JSON.exists():
        prior_report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        prior_report_map = {row["legacy_question_id"]: row for row in prior_report.get("questions", [])}
    payloads: list[tuple[Path, dict[str, Any]]] = []
    all_questions: list[dict[str, Any]] = []
    for bank_path in BANK_PATHS:
        payload = json.loads(bank_path.read_text(encoding="utf-8"))
        bank_id = "pathology" if "pathology" in bank_path.parts else "physiology"
        if payload.get("format_version") == FORMAT_VERSION:
            relative_path = bank_path.relative_to(APP).as_posix()
            needs_baseline = any(
                not prior_report_map.get(question.get("legacy_question_id"), {}).get("legacy_citations")
                for question in payload["questions"]
            )
            baseline_citations = git_head_citations(relative_path) if needs_baseline else {}
            payload["questions"] = [
                restore_source_question(question, prior_report_map, set(calibration), baseline_citations)
                for question in payload["questions"]
            ]
        for question in payload["questions"]:
            question["bank_id"] = bank_id
            all_questions.append(question)
        payloads.append((bank_path, payload))

    migrated: list[dict[str, Any]] = []
    report_rows: list[dict[str, Any]] = []
    answer_targets = Counter()
    sequence = 0
    for bank_path, payload in payloads:
        legacy_bank_version = payload.get("bank_version")
        new_questions: list[dict[str, Any]] = []
        for original in payload["questions"]:
            legacy_id = original["question_id"]
            question = copy.deepcopy(original)
            question.pop("bank_id", None)
            legacy_stem = question["stem"]
            calibrated = calibration.get(legacy_id)
            fifth_basis: dict[str, Any] | None = None
            if calibrated:
                for field in (
                    "question_type",
                    "tested_concept",
                    "options",
                    "correct_index",
                    "choice_rationales",
                    "explanation",
                    "visual_clues",
                    "citations",
                    "image",
                    "zoom_image",
                    "original_image",
                    "visual_target",
                ):
                    question[field] = copy.deepcopy(calibrated[field])
                scenario, lead_in = CALIBRATION_PROMPTS[legacy_id]
                fifth_basis = {"calibration_id": calibrated["calibration_id"]}
            else:
                scenario = context_for(original)
                lead_in = lead_in_for(original, scenario)
                manual = MANUAL_FIFTH.get(legacy_id)
                if manual:
                    fifth, fifth_rationale, manual_citation = manual
                    fifth_basis = {
                        "legacy_question_id": None,
                        "tested_concept": "manually reviewed fifth distractor",
                        "citation": manual_citation,
                    }
                else:
                    fifth, fifth_rationale, fifth_basis = choose_fifth(original, all_questions)
                question["options"] = list(question["options"]) + [fifth]
                question["choice_rationales"] = list(question["choice_rationales"]) + [fifth_rationale]
                source_citation = fifth_basis.get("citation") if fifth_basis else None
                append_unique_citation(question["citations"], source_citation)

            if len(question["options"]) != 5 or len(question["choice_rationales"]) != 5:
                raise ValueError(f"{legacy_id}: migration did not produce five aligned choices")

            target_index = sequence % 5
            question["options"], question["choice_rationales"], question["correct_index"] = rotate_to_index(
                question["options"], question["choice_rationales"], question["correct_index"], target_index
            )
            answer_targets["ABCDE"[target_index]] += 1
            sequence += 1

            context_table = copy.deepcopy(TABLES.get(legacy_id))
            if context_table:
                validate_table(context_table)
                append_unique_citation(question["citations"], context_table["source"])

            question["legacy_question_id"] = legacy_id
            question["legacy_stem"] = legacy_stem
            question["format_version"] = FORMAT_VERSION
            question["scenario"] = scenario
            question["lead_in"] = lead_in
            question["stem"] = f"{scenario} {lead_in}".strip()
            question["case_context"] = scenario
            question["context_table"] = context_table
            question["fifth_distractor_basis"] = fifth_basis
            question["reasoning_type"] = classify_reasoning(question, context_table)
            question["difficulty"] = classify_difficulty(question, context_table, question["reasoning_type"])
            question["question_id"] = question_id(legacy_id, scenario, lead_in, question["options"])
            new_questions.append(question)
            migrated.append(question)
            report_rows.append(
                {
                    "bank": "pathology" if "pathology" in bank_path.parts else "physiology",
                    "legacy_question_id": legacy_id,
                    "question_id": question["question_id"],
                    "collection": question["collection"],
                    "tested_concept": question["tested_concept"],
                    "calibration_override": bool(calibrated),
                    "context_table": context_table["title"] if context_table else None,
                    "difficulty": question["difficulty"],
                    "reasoning_type": question["reasoning_type"],
                    "fifth_distractor": "Approved calibration option set" if calibrated else fifth,
                    "scenario": scenario,
                    "lead_in": lead_in,
                    "legacy_citations": copy.deepcopy(original.get("citations", [])),
                }
            )

        payload["schema_version"] = 4
        payload["bank_version"] = BANK_VERSION + ("-pathology" if "pathology" in bank_path.parts else "-physiology")
        payload["format_version"] = FORMAT_VERSION
        payload["title"] = (
            "Renal Pathology and Related Topics Visual Questions"
            if "pathology" in bank_path.parts
            else "Renal Visual Questions"
        )
        payload["migration"] = {
            "date": "2026-10-23",
            "legacy_bank_version": legacy_bank_version,
            "style_reference": "/Users/chriselwell/Desktop/Renal Quiz Question Format Analysis.pdf",
            "medical_source_root": "/Users/chriselwell/Desktop/Renal/Lectures",
            "calibration_artifact": "reports/clinical-format-calibration-2026-10-23.json",
            "visual_dependency_guardrail": "Do not restate the decisive visible finding in the stem.",
            "options_per_question": 5,
            "progress_namespace_reset": True,
        }
        payload["questions"] = new_questions

    ids = [question["question_id"] for question in migrated]
    if len(ids) != len(set(ids)):
        raise ValueError("new question IDs are not unique")
    if any(len(question["options"]) != 5 for question in migrated):
        raise ValueError("not every question has five options")
    if any(len(question["choice_rationales"]) != 5 for question in migrated):
        raise ValueError("not every question has five rationales")
    if len(TABLES) != sum(question["context_table"] is not None for question in migrated):
        raise ValueError("one or more authored context tables did not attach")
    if any(question["difficulty"] not in DIFFICULTIES for question in migrated):
        raise ValueError("one or more questions has an invalid difficulty")
    if any(question["reasoning_type"] not in REASONING_TYPES for question in migrated):
        raise ValueError("one or more questions has an invalid reasoning type")

    for bank_path, payload in payloads:
        bank_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "schema_version": 1,
        "status": "MIGRATED",
        "date": "2026-10-23",
        "format_version": FORMAT_VERSION,
        "total_questions": len(migrated),
        "physiology_questions": sum(row["bank"] == "physiology" for row in report_rows),
        "pathology_questions": sum(row["bank"] == "pathology" for row in report_rows),
        "calibration_overrides": sum(row["calibration_override"] for row in report_rows),
        "context_tables": sum(row["context_table"] is not None for row in report_rows),
        "answer_distribution": answer_targets,
        "difficulty_distribution": Counter(row["difficulty"] for row in report_rows),
        "reasoning_type_distribution": Counter(row["reasoning_type"] for row in report_rows),
        "questions": report_rows,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Renal clinical-format migration",
                "",
                "Date 2026-10-23",
                "",
                f"Migrated {len(migrated)} source-grounded visual questions to the approved five-choice clinical format.",
                "",
                f"- Physiology questions {report['physiology_questions']}",
                f"- Pathology and related questions {report['pathology_questions']}",
                f"- Calibration overrides {report['calibration_overrides']}",
                f"- Original responsive context tables {report['context_tables']}",
                f"- Correct-answer distribution {dict(answer_targets)}",
                f"- Difficulty distribution {dict(report['difficulty_distribution'])}",
                f"- Reasoning-type distribution {dict(report['reasoning_type_distribution'])}",
                "- New question IDs and browser progress namespace prevent legacy four-choice sessions from loading into the rebuilt bank.",
                "- Existing source lineage, images, teaching originals, explanations, and citations were preserved unless replaced by an approved calibration item.",
                "- Direct-identification prompts use a separate scenario and lead-in. The lead-in does not transcribe the decisive visual finding.",
                "",
                "The complete one-to-one legacy and rebuilt question map is in `reports/clinical-format-migration-2026-10-23.json`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "questions"}, indent=2, default=dict))


if __name__ == "__main__":
    main()
