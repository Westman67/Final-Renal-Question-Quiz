#!/usr/bin/env python3
"""Validate a medical visual-question manifest and question bank."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ACTIVE_STATUS = "USABLE"
BLOCKED_STATUSES = {"NEEDS_REVIEW", "REFERENCE_ONLY", "DUPLICATE", "AGGREGATE_DUPLICATE", "BROKEN", "EXCLUDED"}
DIFFICULTIES = {"foundational", "intermediate", "advanced"}
REASONING_TYPES = {"recognition", "interpretation", "mechanism", "calculation", "clinical_integration"}
GENERIC_RATIONALE_PHRASES = {
    "supported in the source bank",
    "not the relationship or target tested",
    "not the target tested",
    "single directional or steady-state result",
}


def option_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r"\w+", value.casefold(), flags=re.UNICODE):
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
            token = token[:-1]
        tokens.add(token)
    return tokens


def near_duplicate_pair(options: list[str]) -> tuple[str, str] | None:
    contrast_tokens = {
        "afferent",
        "blood",
        "bright",
        "dark",
        "decrease",
        "efferent",
        "fall",
        "increase",
        "left",
        "lower",
        "lumen",
        "right",
        "rise",
        "upper",
        "α",
        "β",
    }
    for index, left in enumerate(options):
        left_tokens = option_tokens(left)
        for right in options[index + 1 :]:
            right_tokens = option_tokens(right)
            if "→" in left or "→" in right or "toward" in left_tokens.intersection(right_tokens):
                continue
            smaller, larger = sorted((left_tokens, right_tokens), key=len)
            added_tokens = larger - smaller
            if (
                len(smaller) >= 2
                and smaller < larger
                and len(added_tokens) <= 2
                and not added_tokens.intersection(contrast_tokens)
            ):
                return left, right
    return None


def records(payload: Any, common_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in common_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError(f"expected a list or one of keys {common_keys}")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(manifest_path: Path, bank_path: Path) -> list[str]:
    errors: list[str] = []
    sources = records(load(manifest_path), ("sources", "records", "items"))
    bank_payload = load(bank_path)
    questions = records(bank_payload, ("questions", "items"))
    schema_version = 1
    if isinstance(bank_payload, dict):
        raw_version = bank_payload.get("schema_version", 1)
        try:
            schema_version = int(raw_version)
        except (TypeError, ValueError):
            errors.append(f"invalid schema_version: {raw_version!r}")

    source_by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        source_id = source.get("source_id")
        if not source_id:
            errors.append(f"manifest[{index}] has no source_id")
            continue
        if source_id in source_by_id:
            errors.append(f"duplicate source_id: {source_id}")
        source_by_id[source_id] = source

    seen_questions: set[str] = set()
    for index, question in enumerate(questions):
        label = question.get("question_id") or f"question[{index}]"
        if label in seen_questions:
            errors.append(f"duplicate question_id: {label}")
        seen_questions.add(label)

        visual_kind = question.get("visual_kind", "image")
        if visual_kind not in {"image", "table"}:
            errors.append(f"{label}: visual_kind must be image or table")
        source_id = question.get("source_id")
        source = source_by_id.get(source_id)
        if visual_kind == "image":
            if source is None:
                errors.append(f"{label}: unknown source_id {source_id!r}")
            else:
                status = source.get("status")
                if status in BLOCKED_STATUSES or status != ACTIVE_STATUS:
                    errors.append(f"{label}: source {source_id} is not USABLE (status={status!r})")
        elif source is not None:
            errors.append(f"{label}: table-only source_id must not shadow an image-manifest source")

        options = question.get("options")
        if not isinstance(options, list) or len(options) != 5:
            errors.append(f"{label}: options must contain exactly five entries")
        elif len({str(option).strip().casefold() for option in options}) != 5:
            errors.append(f"{label}: options must be unique")
        else:
            near_duplicate = near_duplicate_pair([str(option) for option in options])
            if near_duplicate:
                errors.append(
                    f"{label}: near-duplicate options {near_duplicate[0]!r} and {near_duplicate[1]!r}"
                )

        correct_index = question.get("correct_index")
        if not isinstance(correct_index, int) or not 0 <= correct_index < 5:
            errors.append(f"{label}: correct_index must be an integer from 0 through 4")

        if schema_version >= 2:
            rationales = question.get("choice_rationales")
            if not isinstance(rationales, list) or len(rationales) != 5:
                errors.append(f"{label}: choice_rationales must contain exactly five entries")
            elif any(not isinstance(rationale, str) or not rationale.strip() for rationale in rationales):
                errors.append(f"{label}: every choice_rationale must be a non-empty string")
            else:
                for rationale in rationales:
                    generic = next((phrase for phrase in GENERIC_RATIONALE_PHRASES if phrase in rationale.casefold()), None)
                    if generic:
                        errors.append(f"{label}: generic rationale phrase is not allowed: {generic!r}")
                        break

        if schema_version >= 3:
            if question.get("format_version") != "clinical-visual-v1":
                errors.append(f"{label}: format_version must be clinical-visual-v1")
            for field in ("scenario", "lead_in"):
                if not question.get(field):
                    errors.append(f"{label}: missing {field}")
            if visual_kind == "image":
                for field in ("legacy_question_id", "legacy_stem", "fifth_distractor_basis"):
                    if not question.get(field):
                        errors.append(f"{label}: missing {field}")

            table = question.get("context_table")
            if table is not None:
                if not isinstance(table, dict):
                    errors.append(f"{label}: context_table must be an object or null")
                else:
                    columns = table.get("columns")
                    rows = table.get("rows")
                    if table.get("placement") not in {"primary", "additional"}:
                        errors.append(f"{label}: context_table placement must be primary or additional")
                    if not isinstance(table.get("title"), str) or not table["title"].strip():
                        errors.append(f"{label}: context_table requires a title")
                    if not isinstance(columns, list) or not columns or any(not str(cell).strip() for cell in columns):
                        errors.append(f"{label}: context_table requires non-empty columns")
                    if not isinstance(rows, list) or not rows:
                        errors.append(f"{label}: context_table requires at least one row")
                    elif isinstance(columns, list) and any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
                        errors.append(f"{label}: context_table rows must match the column count")
                    table_source = table.get("source")
                    if not isinstance(table_source, dict) or not str(table_source.get("document", "")).endswith(".pdf") or not isinstance(table_source.get("page"), int) or table_source["page"] < 1:
                        errors.append(f"{label}: context_table requires a PDF document and positive page")
            if visual_kind == "table":
                if not isinstance(table, dict) or table.get("placement") != "primary":
                    errors.append(f"{label}: table-only questions require a primary context_table")
                if question.get("source_origin") != "lecture-table":
                    errors.append(f"{label}: table-only questions require source_origin lecture-table")
                if not question.get("case_id") or not question.get("generation_batch"):
                    errors.append(f"{label}: table-only questions require case_id and generation_batch")
                if any(question.get(field) for field in ("image", "zoom_image", "original_image")):
                    errors.append(f"{label}: table-only questions must not carry image asset paths")

        if schema_version >= 4:
            if question.get("difficulty") not in DIFFICULTIES:
                errors.append(f"{label}: difficulty must be one of {sorted(DIFFICULTIES)}")
            if question.get("reasoning_type") not in REASONING_TYPES:
                errors.append(f"{label}: reasoning_type must be one of {sorted(REASONING_TYPES)}")

        for field in ("variant_id", "question_type", "tested_concept", "stem", "explanation", "visual_clues"):
            if not question.get(field):
                errors.append(f"{label}: missing {field}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("question_bank", type=Path)
    args = parser.parse_args()

    bank_payload = load(args.question_bank)
    if not isinstance(bank_payload, dict) or bank_payload.get("schema_version") != 4:
        print("ERROR: bank schema_version must be 4")
        raise SystemExit(1)
    if bank_payload.get("format_version") != "clinical-visual-v1":
        print("ERROR: bank format_version must be clinical-visual-v1")
        raise SystemExit(1)

    errors = validate(args.manifest, args.question_bank)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("OK: manifest and question bank passed validation")


if __name__ == "__main__":
    main()
