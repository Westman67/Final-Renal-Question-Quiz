# Renal clinical-format migration

Date 2026-10-23

Migrated 239 source-grounded visual questions to the approved five-choice clinical format.

- Physiology questions 99
- Pathology and related questions 140
- Calibration overrides 10
- Original responsive context tables 16
- Correct-answer distribution {'A': 48, 'B': 48, 'C': 48, 'D': 48, 'E': 47}
- Difficulty distribution {'foundational': 125, 'intermediate': 108, 'advanced': 6}
- Reasoning-type distribution {'recognition': 125, 'interpretation': 62, 'mechanism': 28, 'clinical_integration': 23, 'calculation': 1}
- New question IDs and browser progress namespace prevent legacy four-choice sessions from loading into the rebuilt bank.
- Existing source lineage, images, teaching originals, explanations, and citations were preserved unless replaced by an approved calibration item.
- Direct-identification prompts use a separate scenario and lead-in. The lead-in does not transcribe the decisive visual finding.

The complete one-to-one legacy and rebuilt question map is in `reports/clinical-format-migration-2026-10-23.json`.
