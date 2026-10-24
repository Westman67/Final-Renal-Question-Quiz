# Renal Visual Questions

The completed manual review inventories 955 eligible renal lecture captures across two isolated banks. The physiology bank has 109 questions, and the pathology-and-related bank has 211 questions. The combined quiz has 320 questions. Reference-only images remain available to reviewers but do not enter scored sessions. Coverage and limitations are documented in the audit reports.

As of 2026-10-24, all 320 scored items use the clinical Visual Question format. Each question has a separate scenario and image-dependent or table-dependent lead-in, exactly five options with aligned rationales, difficulty and reasoning metadata, and preserved lecture provenance. The banks include 81 table-only questions, 239 image questions, and 100 responsive, self-authored context tables grounded in cited lecture pages. The current set covers 100 distinct lecture cases and examples. Eighty questions are advanced, which is 25.00 percent of the bank. Four explicit R30 questions distinguish classic distal type 1, voltage-mediated distal type 1, proximal type 2, and type 4 renal tubular acidosis. The case inventory and one-to-one mappings are documented in `reports/case-coverage-ledger-2026-10-24.md` and `reports/case-coverage-ledger-2026-10-24.json`.

Table-only questions are first-class visual questions. They render a source-grounded data table as the primary stimulus and intentionally omit image, zoom, full-image, and image-flag controls. Image questions retain all image tools, including the in-app flag form. Left Arrow and Right Arrow navigate both formats.

The R13 micturition self-assessment and RX.1 review-question set remain excluded because they are text-only question banks rather than visual cases. This avoids duplicating the separate text quiz pathway.

## Open locally

Double-click `Start Quiz.command`. Keep its terminal window open while studying. Close it with Control-C when finished.

The launcher uses Python 3 and opens `http://127.0.0.1:8783`. No package installation or internet connection is required when Python is available. If that port is busy, run `python3 scripts/serve.py --port 8766 --open` from this app folder. Do not open `index.html` directly with a file URL.

## Study

Select Learn for immediate feedback or Exam for feedback only after finishing. Back and Next preserve drafts and locked answers. You may skip questions. Unanswered items are reported separately. Use 1–5 to choose, Enter to submit or advance, Left Arrow and Right Arrow to move between questions, and Z or the image controls to zoom. Drag a zoomed image to pan. Every new question starts fitted to its frame.

Mode and session length use selectable boxes. Lecture boxes allow one lecture or a mixed selection as the bank grows. Image category, difficulty, reasoning type, and review-state filters can be combined. The Start button shows the actual available session size, even when the requested length is larger. Endless practice labels the pool size rather than promising a finite session.

Menu preferences are remembered in this browser separately from progress. On mobile, practice controls come first and the question appears above its image. Full image is available before answering, but displays only the safe quiz version until feedback is available. The teaching original remains hidden during an unfinished Exam.

The home screen's Lecture coverage summary distinguishes tested topics from known missing coverage. Expand each lecture to see its gaps. This is not a mastery score or a claim that every listed topic is covered exhaustively.

The Keanne Button changes an incorrect locked attempt to correct without changing your selection or adding an attempt. The correction gets its own visual treatment. Previously incorrect uses the latest result, not a lifetime miss count.

Session results summarize performance by image category, difficulty, reasoning type, and tested concept. Lifetime progress also reports difficulty and reasoning type. Missed and marked questions retain review access to every question and rationale.

Unseen uses shared source history. Questions from the same visual are related, not independent unseen images. Sessions rotate source groups before showing another question from the same image when alternatives remain. Endless practice repeats the selected pool with source-aware ordering. Small filtered pools may necessarily repeat a source consecutively.

Use Your progress to export, import, or reset browser-local data. Export before changing browsers, clearing storage, or moving from a local address to a hosted address. Nothing is sent to a server. Imports replace local progress only after confirmation.

Source review shows the ground-truth basis, confidence, source group, transform, proposed answer, and accepted synonyms when available. Reviewers can record a corrected proposed answer, approve a transformation, retain or crop a source, return it to review, or exclude it. These browser-local decisions never alter the scored bank until a rebuilt bank passes validation.

## Repository and local build

The source is stored in the private `Westman67/renal-picture-quiz` GitHub repository. Run `npm run build` to create the self-contained hosted site in `dist`. The hosted build keeps every scored learner, zoom, and teaching image unchanged. It converts only reference-only review images to full-dimension quality 90 WebP derivatives and records each derivative's source path and source hash in the generated manifest. This keeps the hosted site below GitHub Pages' 1 GB limit without deleting or changing the source originals.

The optimized build requires the `cwebp` command from the WebP tools package. Run `npm run build:full` only when an exact local copy of every source PNG is required. That command creates `dist-full`, which is too large for GitHub Pages. Both generated folders are excluded from Git.

Upload the contents of `dist` with `index.html` at the site root. Relative asset paths support a repository subdirectory. No API keys, backend, or build service are required for the finished site.

Do not make the repository or a hosted site public until permission to redistribute the course images is confirmed. Redistribution permission has not been verified. This app contains original teaching copies as well as masked or cropped quiz images.

Client-side answer hiding is a study-interface feature, not security. Someone inspecting the static data can see the answer keys.

## Validate or rebuild

Node.js is needed only for development tests and building the static upload folder.

```sh
npm test
npm run build
npm run test:browser
```

Install development dependencies with `npm install` before running the browser suite. The local learner app itself has no runtime JavaScript dependencies. The optimized hosted build checks every runtime asset reference and fails if the completed site reaches 1 GB. `scripts/validate_bank.py` validates the source/question contract, metadata, context tables, and rationale quality. `scripts/verify_images.py` additionally validates hashes, formats, and exact unchanged pixels outside approved masks or crops. Run it with `--source` pointing to the `Renal/Manual` root. Use `--bank-root data/pathology` for the pathology-and-related bank.

`scripts/build_bank.py` and `scripts/write_questions.py` reproduce the original R1 pilot only; they are retained for provenance and must not be run over this mixed bank. The earlier mixed-bank recipe is `scripts/rebuild_existing.py`; do not rerun it over this later bank. The append-only recipes are `scripts/add_r6.py`, `scripts/add_r7.py`, `scripts/add_r8.py`, `scripts/add_r5_r8_new_captures.py`, and `scripts/add_r9_course_grounded.py`, with explicit full-size reviews in `scripts/review_r6.py` and `scripts/review_r7.py`. These scripts verify source hashes and create app-local derivatives. No script extracts new PDF images or edits source captures.

## Add future lectures

Keep new screenshots in a separate manual lecture folder. Request the quiz-maker workflow for that lecture and approve its prompt. Append validated sources/questions with stable IDs. Preserve existing IDs and browser-storage version so prior progress remains compatible. Do not replace the existing bank with a lecture-only bank.

Lecture-selection boxes appear automatically from question collection values. Add a source-backed entry to `data/coverage.json` for each audited lecture. Lectures without an entry are explicitly shown as not yet audited rather than assumed complete.

## Review and provenance

Source review includes all current manifest sources and local reviewer decisions. Learner flags can be resolved and deliberately reopened. Export decisions to guide a future correction build. Decisions do not auto-activate unvalidated images.

`reports/preflight-audit.md` describes selection and limitations. `data/source-manifest.json` preserves hashes, source-slide citations, grouping, and reproducible edit coordinates. `data/question-bank.json` contains option-aligned rationales and citations. No web sources were used. Clinical scenarios and data tables were authored only from the supplied renal lectures and existing source-grounded bank. The R4 resistance table has 16 distinct masked-arrow questions from one shared source group, not 16 independent photos. The two R6 SEM views share one source group, and the mitochondria EM supports separate yellow-arrow and red-arrow questions.

Educational use only. Not clinical guidance.

The R7 import uses six distinct questions from three scored EM captures. Both arrow colors in the collecting-duct TEM, both cell populations in the starred surface EM, and two separately visible distal-tubule EM features are tested. Two labeled or soft H&E captures remain Source review references.

The R8 import uses one complete manual flowchart and eleven separate safe masks for renal autoregulation, RAAS, baroreflex, ADH, thirst, and ANP targets. All eleven questions share one source group. The original capture is preserved, and no unprovided R8 picture or clinical measurement was invented.

## R5–R8 added-photo import, 2026-10-05

Twenty-four new filenames were reviewed. One renamed R6 H&E image was byte-identical to a pre-existing reference, leaving 23 new physical sources. Eighteen new captures are scored with 22 additional visual questions, and five remain references. Original manual captures were not edited. R5 and R6 transporter/feedback diagrams, R7 cell mechanisms, and R8 hormone diagrams now supplement the earlier EM and flowchart bank. Multiple independently identifiable targets were tested separately where supported. The R6 clipped-axis TF/P graph and four R7 text-only cards were not forced into scored picture questions. Existing question IDs and browser progress remain compatible. Full lecture coverage is not claimed.

## R9 course-grounded addendum, 2026-10-05

Four manual R9 PNGs were visually matched to the user-supplied R9 RLS. Three scored captures support four dedicated questions on the unmeasured-anion band, fixed-acid widening of the gap, and two proximal glutamine/ammonium/bicarbonate pathways. The two anion-gap pictures share a source group. The fourth, a thin text-only chart, remains a teaching reference. Existing IDs and local progress remain compatible. Two pre-existing R8 Part 5 transcript citations were corrected from nonexistent page 3 to page 2. No source capture was edited, and no internet source was used.

## R2 tonicity revision, 2026-10-07

The six questions attached to the hypertonic, hypotonic, and isotonic compartment diagrams now test tonicity classification and its effects on transcellular water movement, cell volume, and final osmolality. Direct boundary-direction prompts were removed. Question IDs, source lineage, image files, and the total bank size remain unchanged so existing browser progress remains compatible. The revision is grounded in pages 23 and 26 of the R2 RLS and is documented in `reports/r2-tonicity-revision-2026-10-07.md`.


## Separate pathology bank

The default launch route opens the 99-question physiology bank. The pathology-and-related route has 140 questions under `data/pathology/` and a separate browser-progress namespace. Both banks use the same `app.js` and `engine.js` interface and hash-named assets. The clinical-format rebuild intentionally uses v2 progress keys because legacy sessions contain four-choice item orderings and incompatible question IDs.

Run `Start Pathology Quiz.command` or `python3 scripts/serve.py --open --bank pathology` for pathology. The physiology launcher remains `Start Quiz.command`. Alternatively open `http://127.0.0.1:8783/?bank=pathology` after starting the local server. Export progress separately for each bank. Do not merge the two progress exports.

The pathology source manifest, question bank, review queue, and coverage records are in `data/pathology/`. Use `python3 scripts/validate_bank.py data/pathology/source-manifest.json data/pathology/question-bank.json` for bank validation. `npm test` and `npm run build` validate and package both routes. Combined mode is enabled as of 2026-10-20 and is described below.

## R16–R17 diuretics import, 2026-10-14

The separate pathology-and-related-topics route includes six visually dependent questions from thirteen manual R16/R17 captures. Two R16 and four R17 sources are scored. Seven labeled, repetitive, or alternate captures remain available in Source review; the full and cropped R17 comparison tables share one visual group. Originals are unchanged. The source manifest records RLS page and capture hashes. The 95-question physiology route and its progress key remain untouched. No combined mode is enabled.

## R19–R22 pathology expansion

The pathology bank now includes R19–R22 manual captures alongside R14–R17. Of 124 newly reviewed captures, 19 support scored visual questions; 105 remain reference-only. The original manual folders and the physiology bank are unchanged. See `reports/preflight-audit-r19-r22.md` for source/variant exclusions.

## R34 manual-capture import, 2026-10-18

The pathology route now includes R34's 89 eligible manual PNG captures. Twelve complete images support distinct visual questions; 77 are retained in Source review as labeled or alternate views, repeated targets, or captures without a separate defensible question in this batch. The 22 PNGs in `_Not for quiz` were excluded. The app's neutral WebP learner images and pixel-exact PNG zoom copies preserve every edge of each selected capture. The physiology bank and its progress namespace remain unchanged. See `reports/preflight-audit-r34.md`.

This is an R34 batch within the broader Renal Visual Questions project, not a claim that all supplied Renal lectures have been imported. Additional manual folders remain for source review and question construction.

## R35 case-lab import, 2026-10-18

Twelve eligible manual R35 captures were screened. Four complete laboratory panels support distinct image-dependent acid-base calculations or interpretations. Eight labeled framework diagrams or alternate case panels remain reference-only. Original PNGs are unchanged, zoom copies are pixel-identical, and full-size WebP learner images retain all edges. See `reports/preflight-audit-r35.md`. This does not complete the broader Renal manual-library run.


## Full manual Renal review, 2026-10-18

All 896 eligible top-level manual PNGs across the current Renal manual library have been inventoried in the two separate bank manifests. `_Not for quiz` folders remain excluded. The original 336 captures were retained and 560 additional captures from R18, R22.2, R23–R31 were adjudicated. Twenty-two new image-dependent questions passed native-size original/variant review. The physiology bank now has 103 questions from 232 captures; the pathology-and-related bank has 76 questions from 664 captures. The app does not merge the banks or their learner-progress namespaces. Reference-only images remain available to reviewers but never enter scored sessions.

R18, R22.2, and R27 did not yield a newly scored item in this pass. Their captures contain substantial answer-bearing labels, overlapping teaching targets, or diagrams better retained as references. This is a scored-question quality decision, not a claim that the lectures lack educational value. See `reports/preflight-audit-renal-full-2026-10-18.md` for the per-folder disposition.

## Bank reassignment, 2026-10-19

R23, R24, R26, R30, and R31 moved from the physiology bank to the pathology-and-related bank at the owner's request. Eight questions and 165 captures moved with their source records, review queue items, and coverage entries. The physiology bank now has 95 questions from 67 captures, and the pathology-and-related bank has 126 questions from 834 captures. Question IDs and image assets are unchanged. Browser progress saved for those eight questions under the physiology key does not carry over to the pathology key.

R27 (5 reference-only captures, no scored questions) also moved to the pathology-and-related bank on 2026-10-19, so every lecture from R14 upward is now in that bank. The physiology bank has 95 questions from 62 captures, and the pathology-and-related bank has 84 questions from 834 captures.

## Pathology candidate review, 2026-10-19

All reference-only pathology captures were visually screened. Forty-two additional image-dependent questions were added to the pathology-and-related bank from R15, R18, R20, R21, R25, R28, R29, and R34 captures, bringing it to 126 questions. Title banners, captions, and answer labels were cropped or filled where they revealed the answer, and each edit is recorded as an exact coordinate in the source manifest. Originals are unchanged and zoom copies are pixel-identical to the learner image. Questions marked medium confidence in the bank rest on slide titles and the lecture RLS rather than an explicit text statement. Eight screened captures were left reference-only because their target was unclear or not verifiable. Build recipe is `scripts/add_pathology_candidates_20261019.py`. The physiology bank and its progress key are unchanged. Backups of the data folder before this change are beside the app folder.

## R12, R13, R36, and R37 manual-capture import, 2026-10-20

The 59 newly staged top-level PNG captures were visually reviewed against the corresponding course RLS slides. Four questions were added to the physiology bank from R12 and R13, and five to the pathology-and-related bank from R36 and R37. The other 50 captures remain reference-only rather than being forced into scored questions. The R13 pitting-edema learner image omits an answer-bearing caption below the complete photograph; its teaching original is unchanged. Source file hashes, RLS pages, variant recipes, and the per-image dispositions are recorded in `reports/preflight-audit-2026-10-20-r12-r13-r36-r37.md`. No progress namespace changed and the banks remain separate.


## Bank selector and combined mode, 2026-10-20

The home screen has a Question bank selector with Physiology, Pathology, and Both. The same choice appears in the header and is remembered in this browser. The address `?bank=physiology`, `?bank=pathology`, or `?bank=both` overrides the remembered choice, and `python3 scripts/serve.py --open --bank both` opens that address. Each bank keeps its own progress key and export. In Both mode the app merges the two banks in memory, writes each question's progress back to the bank that owns it, and keeps the unfinished combined session and combined exam history under `renal-combined-picture-quiz-session-v2`. Lecture boxes, image categories, filters, Mark for review, flags, and source review work across both banks. Export in Both mode downloads one file per bank. Import and Reset are available only after choosing a single bank. Question IDs are unique across banks, so `tests/combine.test.mjs` checks routing. R11 to R13 belong to Physiology.

## R17 diuretic table flag fix, 2026-10-20

The learner flag on the Thiazide urinary calcium question (`q-b162e3a354041916d035`) was fixed by blocking the urinary Na⁺ and Ca²⁺ body cells with opaque question-mark blocks and rewording the stem to say those columns are hidden. The original capture and zoom copy are unchanged, the question ID is unchanged, and the open flag is resolved by `data/pathology/flag-remediation.json` the next time the app loads. Recipe: `scripts/fix_r17_diuretic_table_20261020.py`, with shared mask helpers in `scripts/mask_tools.py`. A backup of the code and data from before these changes is in `backups/2026-10-20-before-bank-selector/`.

## Blocked-cell and label fixes, 2026-10-20

- R17 diuretic table: four more blocked-cell questions (aldosterone antagonist K+, loop diuresis circles, loop maximum Na+ 25%, loop Ca2+ double arrow).
- R31 CKD risk map: the G4 and A3 question now keeps the cell color and hides only the text. Four more blocked-cell questions (G2/A1, G3a/A1, G3b/A3, G5/A1).
- R30 alpha-intercalated cell: arrows beside the H+ pumps and the HCO3- exchanger are hidden.
- R6 glucose graph and R12 buffering graph: the callout and curve labels that named the answer are hidden.
- Existing question ids are unchanged, so progress carries over. New questions have new ids.
- scripts/mask_tools.py now preserves transparency in source images.
- The optimized dist/ bundle was rebuilt and validated on 2026-10-20.
