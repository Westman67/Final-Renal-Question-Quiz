#!/usr/bin/env python3
"""Replace the six R2 boundary-direction items with tonicity interpretation items."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data" / "question-bank.json"

CLASS_OPTIONS = [
    "Hypertonic volume expansion",
    "Hypotonic volume expansion",
    "Isotonic volume expansion",
    "Hypertonic volume contraction",
]

EFFECT_OPTIONS = [
    "Higher ECF tonicity pulls water out of cells, so cells shrink and final osmolality rises",
    "Lower ECF tonicity drives water into cells, so cells swell and final osmolality falls",
    "Unchanged ECF tonicity causes no net transcellular water shift, so cell volume and osmolality stay unchanged",
    "Higher ECF tonicity drives water into cells, so cells swell while final osmolality rises",
]

REVISIONS = {
    "q-151080dedf0eb5fbc074": {
        "question_type": "Physiologic Interpretation",
        "tested_concept": "Hypertonic volume expansion from compartment diagram",
        "stem": "The dashed outline is the post-infusion state. Which tonicity and volume disturbance best explains the complete pattern?",
        "options": CLASS_OPTIONS,
        "correct_index": 0,
        "choice_rationales": [
            "The dashed top rises above baseline while ICF narrows and ECF expands, the lecture pattern for hypertonic volume expansion.",
            "Hypotonic expansion would lower the dashed top and expand ICF as water enters cells, opposite to this pattern.",
            "Isotonic expansion would keep the top height and ICF width unchanged while only ECF expands.",
            "Hypertonic contraction would reduce ECF volume rather than extend the final right boundary outward.",
        ],
        "explanation": "This is hypertonic volume expansion. The added effective solute raises ECF tonicity, so water leaves cells until both compartments reach the same higher final osmolality.",
        "visual_clues": [
            "Final dashed height is above baseline",
            "Pink ICF narrows while yellow ECF expands",
        ],
    },
    "q-6c3d10d46fa070483718": {
        "question_type": "Mechanism",
        "tested_concept": "Hypertonic solution effect on cell volume",
        "stem": "Which cause-and-effect chain best explains the cellular response represented by the dashed final outline?",
        "options": EFFECT_OPTIONS,
        "correct_index": 0,
        "choice_rationales": [
            "Higher extracellular effective osmolality draws water from ICF to ECF. The narrower pink compartment and higher dashed top indicate cell shrinkage and higher final osmolality.",
            "Lower ECF tonicity would move water into cells, widen the pink compartment, and lower the final top border rather than raise it.",
            "Unchanged tonicity would leave ICF width and graph height unchanged; both change in this diagram.",
            "Water moves toward the higher effective osmolality, so hypertonicity cannot drive water into cells; the observed ICF instead narrows.",
        ],
        "explanation": "A hypertonic infusion raises ECF tonicity. Water shifts from the cell interior to the exterior, causing cells to shrink and increasing final osmolality in both compartments.",
        "visual_clues": [
            "Higher final dashed height indicates greater osmolality",
            "Narrower ICF indicates water loss from cells",
        ],
    },
    "q-1fa7083ab6bff16fda88": {
        "question_type": "Physiologic Interpretation",
        "tested_concept": "Hypotonic volume expansion from compartment diagram",
        "stem": "The dashed outline is the post-infusion state. Which tonicity and volume disturbance best explains the complete pattern?",
        "options": CLASS_OPTIONS,
        "correct_index": 1,
        "choice_rationales": [
            "Hypertonic expansion would raise the dashed top and shrink ICF as water leaves cells, opposite to this pattern.",
            "The dashed top falls below baseline while both ICF and ECF expand, the lecture pattern for hypotonic volume expansion.",
            "Isotonic expansion would keep the top height and ICF width unchanged while only ECF expands.",
            "Hypertonic contraction would raise osmolality and reduce extracellular volume rather than lower the top while both compartments expand.",
        ],
        "explanation": "This is hypotonic volume expansion. The added fluid lowers ECF tonicity, so water enters cells until both compartments reach the same lower final osmolality.",
        "visual_clues": [
            "Final dashed height is below baseline",
            "Both ICF and ECF widths expand",
        ],
    },
    "q-26a9daafe5a46a510f0e": {
        "question_type": "Mechanism",
        "tested_concept": "Hypotonic solution effect on cell volume",
        "stem": "Which cause-and-effect chain best explains the cellular response represented by the dashed final outline?",
        "options": EFFECT_OPTIONS,
        "correct_index": 1,
        "choice_rationales": [
            "Higher ECF tonicity would pull water out of cells, narrow ICF, and raise the final top border rather than lower it.",
            "Lower extracellular effective osmolality drives water from ECF into ICF. The wider pink compartment and lower dashed top indicate cell swelling and lower final osmolality.",
            "Unchanged tonicity would leave ICF width and graph height unchanged; both change in this diagram.",
            "The dashed top falls rather than rises, and the ICF expansion reflects water entering cells because ECF is hypotonic, not hypertonic.",
        ],
        "explanation": "A hypotonic infusion lowers ECF tonicity. Water shifts from the cell exterior to the interior, causing cells to swell and decreasing final osmolality in both compartments.",
        "visual_clues": [
            "Lower final dashed height indicates reduced osmolality",
            "Wider ICF indicates water entry into cells",
        ],
    },
    "q-532612d732c68bb725bb": {
        "question_type": "Physiologic Interpretation",
        "tested_concept": "Isotonic volume expansion from compartment diagram",
        "stem": "The dashed outline is the post-infusion state. Which tonicity and volume disturbance best explains the complete pattern?",
        "options": CLASS_OPTIONS,
        "correct_index": 2,
        "choice_rationales": [
            "Hypertonic expansion would raise the dashed top and narrow ICF as water leaves cells; neither occurs here.",
            "Hypotonic expansion would lower the dashed top and widen ICF as water enters cells; neither occurs here.",
            "The dashed top and ICF width stay at baseline while only ECF expands, the lecture pattern for isotonic volume expansion.",
            "Hypertonic contraction would raise osmolality and reduce ECF volume rather than preserve height while ECF expands.",
        ],
        "explanation": "This is isotonic volume expansion. The infused fluid has approximately the same effective solute concentration as plasma, so it expands ECF without changing osmolality or cell volume.",
        "visual_clues": [
            "Final dashed height remains at baseline",
            "ICF width is unchanged while ECF expands",
        ],
    },
    "q-ae5a34041f587bc4fe12": {
        "question_type": "Mechanism",
        "tested_concept": "Isotonic solution effect on cell volume",
        "stem": "Which cause-and-effect chain best explains the cellular response represented by the dashed final outline?",
        "options": EFFECT_OPTIONS,
        "correct_index": 2,
        "choice_rationales": [
            "Higher ECF tonicity would raise the final top border and narrow ICF; the diagram shows neither change.",
            "Lower ECF tonicity would lower the final top border and widen ICF; the diagram shows neither change.",
            "Because effective osmolality is unchanged, there is no sustained transcellular water shift. The overlapping ICF boundaries therefore indicate unchanged cell volume.",
            "ECF is not hypertonic because the dashed top does not rise, and water entry would widen ICF rather than leave it unchanged.",
        ],
        "explanation": "An isotonic infusion does not create a sustained osmotic gradient across cell membranes. ECF expands, but there is no net transcellular water shift, so cell volume and final osmolality remain unchanged.",
        "visual_clues": [
            "Solid and dashed top borders overlap",
            "Solid and dashed ICF boundaries overlap",
        ],
    },
}


def main() -> None:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    by_id = {question["question_id"]: question for question in bank["questions"]}
    missing = set(REVISIONS) - set(by_id)
    if missing:
        raise SystemExit(f"Missing expected question IDs: {sorted(missing)}")

    for question_id, revision in REVISIONS.items():
        question = by_id[question_id]
        if question.get("collection") != "R2" or question.get("category") != "Diagram":
            raise SystemExit(f"Unexpected source scope for {question_id}")
        question.update(revision)
        question["visual_target"] = question["stem"]
        question["ground_truth_basis"] = (
            "Visible compartment pattern and authoritative R2 lecture definitions and body-fluid-shift explanation"
        )

    bank["bank_version"] = "renal-2026-10-07-r3-tonicity"
    BANK_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Revised {len(REVISIONS)} R2 questions in {BANK_PATH}")


if __name__ == "__main__":
    main()
