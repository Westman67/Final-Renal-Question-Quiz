#!/usr/bin/env python3
"""Audit every scored question against its local lecture citations and source capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANKS = (
    ("physiology", ROOT / "data/question-bank.json", ROOT / "data/source-manifest.json"),
    ("pathology", ROOT / "data/pathology/question-bank.json", ROOT / "data/pathology/source-manifest.json"),
)


def sha256(path: Path, cache: dict[Path, str]) -> str:
    if path not in cache:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        cache[path] = digest.hexdigest()
    return cache[path]


def pdf_pages(path: Path, cache: dict[Path, int]) -> int:
    if path not in cache:
        result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
        match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
        if not match:
            raise RuntimeError(f"Could not read page count for {path}")
        cache[path] = int(match.group(1))
    return cache[path]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lecture-root", action="append", type=Path, required=True)
    parser.add_argument("--manual-root", type=Path, required=True)
    parser.add_argument("--vault-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    file_index: dict[str, list[Path]] = defaultdict(list)
    for root in args.lecture_root:
        for path in root.rglob("*"):
            if path.is_file():
                file_index[path.name].append(path)

    hash_cache: dict[Path, str] = {}
    page_cache: dict[Path, int] = {}
    errors: list[str] = []
    records: list[dict] = []

    def resolve(document: str, expected_hash: str) -> Path | None:
        if document.startswith("Renal/"):
            candidates = [args.vault_root / document]
        elif "/" in document and not document.endswith(".pdf"):
            candidates = [args.manual_root / document]
        else:
            candidates = file_index.get(Path(document).name, [])
        candidates = [path for path in candidates if path.is_file()]
        if expected_hash:
            matches = [path for path in candidates if sha256(path, hash_cache) == expected_hash]
            if matches:
                return matches[0]
        return candidates[0] if len(candidates) == 1 else None

    for bank_name, bank_path, manifest_path in BANKS:
        questions = json.loads(bank_path.read_text(encoding="utf-8"))["questions"]
        sources = json.loads(manifest_path.read_text(encoding="utf-8"))["sources"]
        source_by_id = {source["source_id"]: source for source in sources}
        for question in questions:
            qid = question["question_id"]
            q_errors: list[str] = []
            citations = []
            pdf_citations = []
            manual_citations = []
            for citation in question.get("citations", []):
                document = citation.get("document", "")
                expected_hash = citation.get("sha256", "")
                path = resolve(document, expected_hash)
                entry = {"document": document, "page": citation.get("page"), "resolved": bool(path), "sha256_match": False}
                if not path:
                    q_errors.append(f"unresolved citation {document!r}")
                else:
                    entry["sha256_match"] = sha256(path, hash_cache) == expected_hash
                    if not entry["sha256_match"]:
                        q_errors.append(f"hash mismatch for {document!r}")
                    if document.endswith(".pdf") and citation.get("page") is not None:
                        page = citation["page"]
                        page_count = pdf_pages(path, page_cache)
                        entry["page_count"] = page_count
                        if not isinstance(page, int) or page < 1 or page > page_count:
                            q_errors.append(f"out-of-bounds page {page!r} for {document!r}")
                citations.append(entry)
                if document.endswith(".pdf"):
                    pdf_citations.append(entry)
                elif document.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    manual_citations.append(entry)

            source = source_by_id.get(question.get("source_id"))
            if question.get("visual_kind") == "table":
                table = question.get("context_table")
                if not isinstance(table, dict) or table.get("placement") != "primary":
                    q_errors.append("table-only question has no primary context table")
                if question.get("source_origin") != "lecture-table":
                    q_errors.append("table-only question has an invalid source_origin")
            elif not source:
                q_errors.append("source_id is missing from the source manifest")
            else:
                if source.get("status") != "USABLE":
                    q_errors.append(f"source status is {source.get('status')!r}, not 'USABLE'")
                if source.get("lecture_id") != question.get("collection"):
                    q_errors.append("source and question lecture identifiers differ")
                original = args.manual_root / source.get("relative_path", "")
                if not original.is_file():
                    q_errors.append("original source capture is missing")
                elif sha256(original, hash_cache) != source.get("sha256"):
                    q_errors.append("original source capture hash differs from the manifest")

            correct_index = question.get("correct_index")
            options = question.get("options", [])
            rationales = question.get("choice_rationales", [])
            if not isinstance(correct_index, int) or not 0 <= correct_index < len(options):
                q_errors.append("correct_index is invalid")
                correct_answer = None
            else:
                correct_answer = options[correct_index]
                if correct_index >= len(rationales) or not str(rationales[correct_index]).strip():
                    q_errors.append("the keyed choice rationale is missing")
                if not str(question.get("explanation", "")).strip():
                    q_errors.append("the overall explanation is missing")
            if not pdf_citations:
                q_errors.append("no lecture PDF citation")

            collection = question.get("collection", "")
            notes = sorted((args.vault_root / "Renal/Lecture").glob(f"{collection} - */{collection} - Detailed Notes.md"))
            null_pages = sum(1 for citation in pdf_citations if citation["page"] is None)
            if null_pages and not notes:
                q_errors.append("unresolved PDF page has no local detailed-note support")

            records.append(
                {
                    "bank": bank_name,
                    "question_id": qid,
                    "lecture": collection,
                    "tested_concept": question.get("tested_concept"),
                    "correct_answer": correct_answer,
                    "confidence": question.get("ground_truth_confidence"),
                    "ground_truth_basis": question.get("ground_truth_basis"),
                    "lecture_citations": pdf_citations,
                    "manual_capture_citations": manual_citations,
                    "detailed_note": str(notes[0].relative_to(args.vault_root)) if notes else None,
                    "status": "PASS" if not q_errors else "FAIL",
                    "errors": q_errors,
                }
            )
            errors.extend(f"{qid}: {message}" for message in q_errors)

    by_lecture = Counter(record["lecture"] for record in records)
    confidence = Counter(record["confidence"] for record in records)
    unresolved_page_questions = [record["question_id"] for record in records if any(c["page"] is None for c in record["lecture_citations"])]
    distinct_documents = {citation["document"] for record in records for citation in record["lecture_citations"] + record["manual_capture_citations"]}
    report = {
        "audit_date": date.today().isoformat(),
        "scope": "Local user-supplied renal lecture material only; no internet or outside sources.",
        "summary": {
            "questions": len(records),
            "passed": sum(record["status"] == "PASS" for record in records),
            "failed": sum(record["status"] == "FAIL" for record in records),
            "distinct_lecture_and_capture_documents": len(distinct_documents),
            "questions_with_unresolved_pdf_page": len(unresolved_page_questions),
            "confidence": dict(sorted(confidence.items())),
            "questions_by_lecture": dict(sorted(by_lecture.items(), key=lambda item: int(item[0][1:]))),
        },
        "unresolved_pdf_page_question_ids": unresolved_page_questions,
        "errors": errors,
        "questions": records,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
