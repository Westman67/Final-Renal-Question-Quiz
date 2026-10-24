#!/usr/bin/env python3
"""Fill absent citation hashes from the current local source files.

Existing lecture PDF and image hashes are never replaced. This keeps the operation
narrow and makes a changed primary source remain visible to the grounding audit
instead of silently blessing the new bytes. The optional notes refresh is limited
to supplemental local Markdown citations whose paths already exist in the bank.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATHS = (ROOT / "data/question-bank.json", ROOT / "data/pathology/question-bank.json")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lecture-root", action="append", type=Path, required=True)
    parser.add_argument("--vault-root", type=Path, required=True)
    parser.add_argument(
        "--refresh-supplemental-note-hashes",
        action="store_true",
        help="Refresh existing Renal/*.md hashes without changing PDF or image hashes.",
    )
    args = parser.parse_args()

    by_name: dict[str, list[Path]] = defaultdict(list)
    for source_root in args.lecture_root:
        for path in source_root.rglob("*"):
            if path.is_file():
                by_name[path.name].append(path)

    filled = 0
    refreshed_notes = 0
    touched_questions: set[str] = set()
    hash_cache: dict[Path, str] = {}

    for bank_path in BANK_PATHS:
        bank = json.loads(bank_path.read_text(encoding="utf-8"))
        for question in bank["questions"]:
            for citation in question.get("citations", []):
                document = citation.get("document", "")
                refresh_note = (
                    args.refresh_supplemental_note_hashes
                    and document.startswith("Renal/")
                    and document.endswith(".md")
                )
                if citation.get("sha256") and not refresh_note:
                    continue
                if document.startswith("Renal/"):
                    candidates = [args.vault_root / document]
                else:
                    candidates = by_name.get(Path(document).name, [])
                candidates = [candidate for candidate in candidates if candidate.is_file()]
                if len(candidates) != 1:
                    raise RuntimeError(
                        f"Expected one local source for {document!r}, found {len(candidates)}"
                    )
                source = candidates[0]
                if source not in hash_cache:
                    hash_cache[source] = digest(source)
                current_hash = hash_cache[source]
                if citation.get("sha256") == current_hash:
                    continue
                if refresh_note and citation.get("sha256"):
                    refreshed_notes += 1
                else:
                    filled += 1
                citation["sha256"] = current_hash
                touched_questions.add(question["question_id"])
        bank_path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "filled_citations": filled,
                "refreshed_supplemental_note_citations": refreshed_notes,
                "touched_questions": len(touched_questions),
                "lecture_pdf_or_image_hashes_replaced": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
