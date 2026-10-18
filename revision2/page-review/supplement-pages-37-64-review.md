# Supplement pages 37–64: visual review

Final status: **PASS**. The final 64-page PDF has SHA-256 `2b3799ed583df75d025609bbea9692140441a025ed8f07ccfe2eb1a825b34046`. The first-pass observations below are retained for provenance; all three were resolved and checked again on the final rendering.

Reviewed the actual rendered images using `view_image`, not text extraction or bounding boxes alone. All 28 pages were inspected in `supplement-sheet-07.png` through `supplement-sheet-11.png`. Pages 40, 42, 43, 46, 50, 51, 53, 54, 55, 58, 59, 60, 61, 62, 63 and 64 were also opened individually at original image resolution.

## Findings

- Pages 37–39: mathematical statements, proofs, section transitions and formula layouts are visible and contained within the page.
- Pages 40–42: the complete scenario table, arrival/mean specifications and 25-method map are readable. The frozen method identifiers and distinct inactive/infinite service budgets remain distinguishable.
- Pages 43–49: the six-method reward table and full 300-row method–scenario table have readable digits, standard errors, area units and tail columns. Continuation headers and footers are present. No merged cells, cropped columns or collisions were seen.
- Pages 49–52: the 60-comparison reward table and paired joint-cost table have aligned headers, correctly displayed signed differences and separate individual/family interval columns. The longer scenario identifiers fit their cells.
- Pages 53–55: service diagnostics, all 25 failure-count rows, data-generation inventory and ablation table are readable. The default method's nonzero failure counts remain visible. The proposed rate is clearly distinguished from actual service pulls.
- Pages 56–58: the earlier checkpoint study retains its own protocol and numbers. The full 24-row old table fits without clipping.
- Pages 59, 60 and 62: all three old numerical figures were opened at full resolution. Plot titles, axes, legends, units, curves, scatter points and captions remain clear. Their legends identify checkpoint configurations, not F-CCP.
- Pages 61–64: the allocation table, accounting formula, historical resources, reporter formula and references are intact and legible.

## Editorial issues notified to the main integration task

1. Page 59 has consecutive headings “S17.3 Computational details of the earlier experiment” and “S17.4 Configuration, records, and implementation names”, with no prose between them. The empty wrapper heading should be removed or merged, retaining its semantic reference target.
2. Page 60 has a standalone “Figure 2.” between the figure caption and reproducibility prose. This appears to be a migrated sentence fragment and should be removed.
3. Optional placement improvement: the new S15 scenario table floats to the top of page 40 before the closing S14 proof. The table itself is readable and correct; preventing the preceding-section placement would clarify its ownership.

No clipping, page-boundary overflow, unreadable legend, table overlap or missing resource was found. The first two editorial remnants were reported immediately for correction. This review does not assert independent mathematical verification or a new probability certificate. No manuscript source was modified by this reviewer.

## Final rendering follow-up

After the main integration task rebuilt the document, I reopened all five final contact sheets 07–11 and reviewed every page from 37 through 64 again. I additionally opened final pages 40, 41, 59 and 60 individually at original resolution using `view_image`.

- The final S15 scenario table appears on page 41, after S15 begins on page 40. It no longer precedes the closing S14 proof.
- Page 59 now has no empty computational-details wrapper heading. The actual configuration subsection appears once on page 60, numbered S17.3, with its explanatory prose directly below.
- The standalone “Figure 2.” line is absent. The actual Figure 2 caption and the following configuration prose are complete and separate.
- The reordered table continuation rows, method map, service/failure tables and archived figures remain contained and readable throughout final pages 37–64. No new visual issue appeared after reflow.

The final rendering matches the supplement hash recorded in `revision2/final-verification.json`; the actual root PDF hash was checked separately. There are no remaining layout findings from this page range.
