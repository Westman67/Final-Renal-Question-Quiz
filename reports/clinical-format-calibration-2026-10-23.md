# Renal picture quiz clinical-format calibration

Date 2026-10-23

Status awaiting approval

This is the ten-question calibration checkpoint required by the approved rebuild prompt. No production question bank, application code, progress namespace, or deployed artifact has been changed.

## Calibration standard

- The format target is the attached `Renal Quiz Question Format Analysis.pdf`.
- Medical content is restricted to `/Users/chriselwell/Desktop/Renal/Lectures`.
- Every item requires its learner-facing visual.
- Every item has exactly five options and five aligned rationales.
- Each item tests application, interpretation, calculation, or clinicopathologic integration rather than simple image naming.
- Correct-answer positions are distributed across A through E.
- The ten items span physiology, graph interpretation, urine microscopy, pharmacology, electron microscopy, immunofluorescence, laboratory interpretation, radiology, hereditary oncology, and staging imaging.

## Source and visual audit

The lecture inventory contains 230 readable PDFs totaling 5,278 pages. One exact duplicate pair was found, `R15 Urinalysis RLS copy.pdf` and `R15 Urinalysis RLS.pdf`. The audit is recorded in `reports/lecture-source-inventory-2026-10-23.json`.

All ten learner-facing images were inspected at full available resolution. Eight passed without limitation. The acyclovir microscopy crop and posterior urethral valve study are low resolution, but the tested features remain visible and no answer is exposed.

## Question 1

Collection R4

Type physiologic prediction

Visual `assets/89c10abe437cab368a7cdecf.webp`

An experimental maneuver causes isolated moderate constriction of the efferent arteriole. The figure summarizes the resulting renal hemodynamic changes, with one cell masked. Which complete pattern is most likely?

A. RPF decreases, Pgc increases, GFR increases, and filtration fraction increases

B. RPF decreases, Pgc decreases, GFR decreases, and filtration fraction is unchanged

C. RPF increases, Pgc increases, GFR increases, and filtration fraction is unchanged

D. RPF increases, Pgc decreases, GFR decreases, and filtration fraction decreases

E. RPF, Pgc, GFR, and filtration fraction are all unchanged

Correct answer A

Rationales

- A is correct. This is the pattern shown for moderate efferent constriction. Outflow resistance lowers RPF while raising Pgc enough to increase GFR, so filtration fraction also rises.
- B is the afferent-constriction pattern in the figure.
- C is the afferent-dilation pattern in the figure.
- D is the efferent-dilation pattern, the opposite intervention.
- E is the normal baseline row and does not follow an isolated resistance change.

Source `R4 Renal Plasma Flow (Physiology) RLS.pdf`, page 16.

## Question 2

Collection R12

Type graph interpretation

Visual `assets/4c9c25a0e1b18213a24cdff6.webp`

A patient receives an acute H+ or HCO3− load at time zero. At approximately two hours, which defense process in the graph is most nearly complete?

A. Respiratory compensation

B. Cellular buffering

C. Extracellular fluid distribution and buffering

D. Renal base excretion

E. Renal acid excretion

Correct answer C

Rationales

- A is still early in its rise at two hours.
- B has begun to rise but remains well below its plateau.
- C is correct. The leftmost extracellular-fluid distribution and buffering curve is already close to 100% completion.
- D develops over a longer interval and is not near completion at two hours.
- E is the latest response shown and remains near baseline at two hours.

Source `R12 Acid-Base Case Studies Beginners (Physiology) RLS.pdf`, page 6.

## Question 3

Collection R15

Type clinical microscopy association

Visual `assets/6aa62fb7fd96a0b45e2f18ed.webp`

A hospitalized patient receiving antiviral therapy has the long, birefringent, needle-shaped crystals pictured on urine microscopy. Which substance most likely formed these crystals?

A. Indinavir

B. Acyclovir

C. Sulfadiazine

D. Cystine

E. Calcium oxalate dihydrate

Correct answer B

Rationales

- A forms sunburst clusters or flat plate-like needles pointed at both ends, not the sparse crossing needles shown.
- B is correct. Acyclovir forms birefringent needle-shaped crystals matching the pictured morphology and antiviral exposure.
- C forms shocks-of-wheat or shell-shaped aggregates.
- D forms hexagonal crystals in acidic urine.
- E forms envelope-shaped crystals.

Sources `R15 Urinalysis RLS.pdf`, pages 30, 32, and 33.

## Question 4

Collection R17

Type applied pharmacology table

Visual `assets/8505e62e48029b25baec3fb2.webp`

An adult begins one of the diuretic classes listed in the table. Follow-up urine studies show increased sodium excretion but decreased calcium excretion. Which class was most likely prescribed?

A. Loop diuretics

B. Osmotic diuretics

C. Carbonic anhydrase inhibitors

D. Thiazides

E. ENaC blockers

Correct answer D

Rationales

- A increases urinary calcium rather than decreasing it.
- B does not produce the urinary calcium decrease shown for thiazides.
- C increases urinary sodium but does not have the downward urinary-calcium pattern.
- D is correct. The thiazide row combines increased urinary sodium with decreased urinary calcium.
- E increases urinary sodium but does not produce the thiazide calcium pattern.

Source `R17 Diuretics II (Pharmacology) RLS.pdf`, page 24.

## Question 5

Collection R18

Type clinicopathologic electron microscopy

Visual `assets/1dd7880c6751c317315af920.webp`

A young man has persistent hematuria, progressive kidney disease, sensorineural hearing loss, and a family history of renal failure. Which ultrastructural finding is illustrated by the electron micrograph?

A. Continuous intramembranous electron-dense deposits

B. Discrete subepithelial hump-like deposits

C. A uniformly thin but structurally intact glomerular basement membrane

D. Diffuse podocyte foot-process effacement

E. Splitting and fraying of the lamina densa with a basket-weave appearance

Correct answer E

Rationales

- A characterizes dense deposit disease, not hereditary nephritis with hearing loss.
- B is seen in infection-associated glomerulonephritis, not the lamellated membrane shown.
- C describes thin basement membrane disease, which lacks the ocular and auditory findings of Alport syndrome.
- D is the defining electron-microscopy pattern of minimal change disease.
- E is correct. Alport syndrome produces splitting and fraying of the lamina densa, creating the pictured basket-weave membrane.

Sources `R18 Renal Pathology - Glomerular Diseases (Part 1) (Nephritic Diseases) (Pathology) RLS.pdf`, pages 48, 61, 73, 75, 76, 77, and 97.

## Question 6

Collection R34

Type clinicopathologic immunofluorescence

Visual `assets/8c90cfc1d680b0b8b9ea3377.webp`

A 7-year-old boy develops acute kidney injury and hematuria two weeks after Streptococcus pyogenes pharyngitis. His C3 is low, C4 is normal, and ANA, ANCA, and anti-GBM testing are negative. Which immunofluorescence pattern is shown in the IgG image?

A. Smooth linear IgG along the glomerular basement membranes

B. Dominant mesangial IgA staining

C. Granular capillary-wall and mesangial IgG staining

D. A pauci-immune pattern with little or no glomerular immunoglobulin

E. A full-house granular pattern with IgG, IgA, IgM, C3, and C1q

Correct answer C

Rationales

- A is the anti-GBM pattern. The serology is negative and the pictured signal is irregular rather than linear.
- B supports IgA nephropathy, whereas this poststreptococcal case has strong granular IgG and C3.
- C is correct. Infection-associated glomerulonephritis produces granular IgG and C3 along capillary walls and in the mesangium.
- D has little or no immune staining, which conflicts with the strong glomerular IgG signal.
- E supports lupus nephritis. This case is ANA-negative and the lecture panel emphasizes IgG and C3.

Sources `R34 Renal Pathology - Renal Diseases - Slide Review RLS.pdf`, pages 16, 29, 36, 42, 44, and 47. The full-house distractor is supported by `R18 Renal Pathology - Glomerular Diseases (Part 1) (Nephritic Diseases) (Pathology) RLS.pdf`, page 129.

## Question 7

Collection R35

Type laboratory calculation

Visual `assets/1590c04287f2104b99926146.webp`

A 30-year-old man presents after three days of lethargy, fever, and diarrhea. He is thirsty and orthostatic, and urinalysis shows glucosuria and ketonuria. Using the admission values shown, what is his serum anion gap in mEq/L?

A. 5

B. 12

C. 18

D. 23

E. 35

Correct answer D

Rationales

- A is the pictured potassium concentration.
- B is the pictured bicarbonate concentration.
- C does not result from applying the lecture formula to the pictured values.
- D is correct. AG = Na − (Cl + HCO3) = 150 − (115 + 12) = 23 mEq/L.
- E equals sodium minus chloride alone and omits bicarbonate.

Sources `R35 Acid-Base Case Studies Advanced (Clinical) RLS.pdf`, pages 2, 3, and 4.

## Question 8

Collection R25

Type clinical radiology

Visual `assets/6635757cf3cdd3e794a9f425.webp`

A male newborn has bilateral hydronephrosis and a weak urinary stream. The voiding cystourethrogram shows a dilated posterior urethra with abrupt distal narrowing. Which diagnosis is most likely?

A. Primary vesicoureteral reflux

B. Duplex collecting system

C. Ureteropelvic junction obstruction

D. Multicystic dysplastic kidney

E. Posterior urethral valves

Correct answer E

Rationales

- A is retrograde flow from the bladder into the ureters and kidneys, not a dilated posterior urethra with distal narrowing.
- B produces two ureters from one kidney and does not create the pictured posterior-urethral obstruction.
- C usually produces upper-tract, often unilateral, hydronephrosis without posterior-urethral dilation.
- D is a nonfunctioning kidney with an abnormal renal contour, not a lower-tract obstructive VCUG pattern.
- E is correct. Posterior urethral valves produce congenital outlet obstruction in boys with a dilated posterior urethra and bilateral hydronephrosis.

Sources `R25 Renal Imaging - Part 1 (Radiology) RLS.pdf`, pages 35 through 39 and page 41.

## Question 9

Collection R28

Type hereditary oncology association

Visual `assets/52b24222ace98cba2e279ded.webp`

A patient with multifocal renal tumors has the retinal vascular lesion pictured. Which molecular abnormality best unifies these findings?

A. Loss of VHL at chromosome 3p25

B. MET activation with trisomy 7 and 17

C. Fumarate hydratase mutation

D. Folliculin loss on chromosome 17p

E. PTEN and p53 alterations

Correct answer A

Rationales

- A is correct. The lecture links 3p25 loss and Von Hippel-Lindau disease to clear cell renal carcinoma, retinal angiomas, and multifocal renal tumors.
- B is associated with papillary type I renal carcinoma.
- C causes hereditary leiomyomatosis and renal cell cancer, an aggressive papillary type II association.
- D causes Birt-Hogg-Dubé syndrome, which the lecture links to fibrofolliculomas, pneumothorax, and oncocytic renal tumors.
- E is listed with chromophobe carcinoma and does not unify renal tumors with retinal angiomas.

Sources `R28 Renal & Urinary Tract Malignancies (Urology - Part 1) RLS.pdf`, pages 13 through 15, 20 through 22, 24, and 32.

## Question 10

Collection R29

Type oncologic staging imaging

Visual `assets/dc04a1dc551b640a6dd8c4ad.webp`

A patient with a renal malignancy undergoes staging. The chest CT shows numerous well-circumscribed nodules of varying sizes in both lungs. Which metastatic pattern from the lecture is present?

A. Direct extension through the peripheral renal fascia

B. Hematogenous pulmonary metastases

C. Regional lymph-node metastases

D. Distant hepatic metastases

E. Lytic osseous metastases

Correct answer B

Rationales

- A is contiguous invasion around the primary renal mass and would not create scattered bilateral lung nodules.
- B is correct. The lecture labels this pattern as hematogenous lung metastases.
- C appears as nodal disease rather than numerous rounded nodules throughout both lungs.
- D produces distant lesions in the liver, not the pulmonary pattern shown.
- E involves bone and does not produce intrapulmonary nodules.

Source `R29 Renal Imaging - Part 2 (Radiology) RLS.pdf`, page 22.

## Approval boundary

Approval of this calibration set will authorize the full-bank rewrite and app migration described in the approved prompt. Until then, the production quiz remains unchanged.
