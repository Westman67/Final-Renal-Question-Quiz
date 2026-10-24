# Full manual Renal picture-quiz audit

Reviewed 2026-10-18. Scope was the course-only manual library. No external material was added. All sources remained unmodified. The source library's `_Not for quiz` subfolders were excluded.

| Folder | Eligible captures | New scored questions | Reference-only |
|---|---:|---:|---:|
| R18 | 64 | 0 | 64 |
| R22.2 | 33 | 0 | 33 |
| R23 | 34 | 1 | 33 |
| R24 | 33 | 2 | 31 |
| R25 | 113 | 7 | 106 |
| R26 | 24 | 1 | 23 |
| R27 | 5 | 0 | 5 |
| R28 | 71 | 3 | 68 |
| R29 | 109 | 4 | 105 |
| R30 | 33 | 1 | 32 |
| R31 | 41 | 3 | 38 |
| Total newly adjudicated | 560 | 22 | 538 |

All 22 new learner WebP variants were individually inspected at native size against their source PNGs. Zoom PNGs are byte-identical copies of the originals. No crop or mask was used for this batch. A candidate R30 ammonium-transporter item was demoted to reference-only because the tested ion was printed on the source. R26 wording was corrected after image review so it no longer claims a cuff is visible. R25 wording was corrected to avoid implying that a comparison image is shown.

Source records include immutable SHA-256, course lecture attribution, source and variant lineage, and either the course RLS record or the detailed note when an RLS manifest is unavailable. Exact PDF pages are left null when not independently established. New scores are kept separate across physiology and pathology routes. All previously scored questions and their IDs remain unchanged.

Remaining limits: The manual library has no eligible folders for R3, R10–R13, R32, or R33. R18, R22.2, and R27 have no new scored questions. Many other files are labeled, alternate slide captures, repetitive, or lack a distinct leak-free target. This audit does not assert complete concept coverage of every Renal lecture. Some historical R35 external original-PDF paths recorded in the Vault remain unavailable; the in-Vault course note and picture captures were available for the earlier R35 quiz integration.

Validation passed both bank validators, all 17 Node tests, the production build, source and image integrity checks, and desktop/mobile browser review of both quiz routes. The pathology route had one optional remediation-file 404 during initial QA; this was corrected. Source review now labels unverified PDF pages instead of displaying “p. null”.
