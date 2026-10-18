# Supplement PDF pages 1?36: visual review

Reviewed in two passes on 2026-10-17 by a separate integration reviewer. The second pass inspected the final pagination-corrected renders. This is a rendered-page inspection, not a mathematical proof certificate. The document page labels S-1?S-36 correspond to PDF pages 1?36.

## Actual visual coverage

Reopened and inspected all six final contact sheets with the image-viewing tool, including every page thumbnail, after the final pagination corrections:

| Rendered contact sheet | PDF pages viewed | Result |
| --- | --- | --- |
| `supplement-sheet-01.png` | 1?6 | Title, notation, contents, S1 and S2 fit the page; no missing symbols or clipping visible |
| `supplement-sheet-02.png` | 7?12 | S3?S4 formulas and text fit; the initial lemma split is repaired |
| `supplement-sheet-03.png` | 13?18 | S4 completion and S5?S6 layout fit; Checkpoint algorithm is legible on its float page |
| `supplement-sheet-04.png` | 19?24 | Retained lower-bound and shared-evidence proofs fit; long displays remain within margins |
| `supplement-sheet-05.png` | 25?30 | Endpoint, probability, occupation, and schedule-information text fit; no clipping or overlap |
| `supplement-sheet-06.png` | 31?36 | S12 feasibility, arbitrary recovery, fresh-block evidence, and ABM algorithm fit; the initial theorem split is repaired |

Additionally opened individual full-page renders for PDF pages **7, 8, 16, 30, 31, 32, 35, and 36**. The arbitrary-action decomposition on page 8, schedule constants on page 31, fresh-block description on page 35, and both algorithm blocks were checked at this larger size. In the final pass, individual pages **7, 8, 32, and 33** were opened again at full-page size to verify the two corrections directly.

## Findings

No blocking layout problem found. All 36 reviewed pages contain expected content, page numbers are present and readable, text and displayed formulas stay inside the body, and no overlap, cropped formula, unresolved reference marker, or empty page was visible. The contents span the first three pages and include the later appendix headings.

Pages 16 and 36 are algorithm float pages with deliberate surrounding whitespace. Their complete pseudocode, captions, rules, line numbers, and mathematical arguments remain readable and uncut. They are not accidental blank pages. No numerical result tables occur within these first 36 pages, so this review makes no claim about the later S15?S17 table font sizes or figures.

## Final correction checks and first-pass history

The first pass found two minor statement splits, both now repaired:

1. Originally PDF page 7 ended after the first two lines of Lemma S3.2, and page 8 began with ?experiment. Then?. After the added space reservation, page 7 ends with the preceding proof and Lemma S3.2 begins at the top of page 8 with its complete statement and displays. The final page pair was inspected directly; no clipping or stranded continuation remains.
2. Originally PDF page 32 ended with subsection S13.1 and two lines of Theorem S13.1. After the added space reservation, page 32 ends after the S13 introduction, and page 33 begins with subsection S13.1 and the complete theorem statement. The final page pair was inspected directly; its assumptions, KL condition, recovery conclusion, and opening proof fit normally.

The longer Theorem S12.1 still spans pages 30?31 naturally: page 30 includes its name, assumptions, and displayed mean vector; page 31 continues the definitions and conclusions. Both surrounding contact-sheet pages were rechecked in the final pass.

Final visual status for PDF pages 1?36: **PASS; both reported pagination observations corrected; no unresolved layout finding in this reviewed range.** The final supplement remains 64 pages; this reviewer inspected its first 36 pages, and other page ranges require their own coverage record. This report does not claim visual review of the main article.

## Final inspected snapshot

First-pass supplement PDF SHA-256 (retained only as history): `bede0915bf0f9974b959cb68d7622e07a75e2220c698d12c04396e1e9484fa76`.

- `supplement.pdf` SHA-256: `2b3799ed583df75d025609bbea9692140441a025ed8f07ccfe2eb1a825b34046`.
- `supplement-sheet-01.png` SHA-256: `a3486921777d18cbb98e7daafe2f7eaef6b307b5b37a25ce8f1164c8cacdb1a3`.
- `supplement-sheet-02.png` SHA-256: `e1e413cee498d1d6695acfb8d2a7aeed446eb19a7bfddfae9b55f37fc15b41b7`.
- `supplement-sheet-03.png` SHA-256: `4a8c7a17bbb611daa869a83ad3fbb2e285d4ab46d9af9d1109e31e98eb2c5171`.
- `supplement-sheet-04.png` SHA-256: `3395a2573ab8d262770e2ef583fde85df83e2814e3a3e91f623d552e56e9e008`.
- `supplement-sheet-05.png` SHA-256: `84a4dfcc96da200d468ec6116a52eaba41c1e25c17a88c988e1be8be58871ad2`.
- `supplement-sheet-06.png` SHA-256: `634303b8b6bc011f0e0adce8146e2ce20f0b3b9660e089a63fdabe01421033ea`.
