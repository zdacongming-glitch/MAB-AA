# English prose review

Date: 2026-10-15. Scope: `sections/01_introduction.tex`, `sections/07_discussion.tex`, and the experimental and source-reference passages of `response_to_reviewers.md`. The mathematical sections, preamble, and main source were not edited in this pass. No assessment or scoring files were read.

The review applied stat-journal-writing to the order of the argument and the match between claims and evidence, followed by humanizer to sentence structure and repetitive qualifiers. Existing technical terms, citations, assumptions, and mathematical expressions were preserved. The introduction and discussion received section labels for stable source references. The experimental response was updated from recorded artifacts, not from stylistic inference.

## Draft, audit, and final example

This example uses the first introduction paragraph. The draft below is the wording that existed before this pass.

### Draft

> A sequential experiment may need to retain several promising alternatives while new alternatives continue to enter. Examples include a testing platform that receives externally generated designs and an experimental pipeline that introduces candidates during an ongoing study. The investigator must decide which alternative to sample and what can currently be said about the whole candidate set. A small cumulative reward loss answers the allocation question. It does not imply that the investigator can distinguish all alternatives within a specified tolerance of the current best from those outside that tolerance.

### Audit

- The application examples establish the problem concretely and should stay.
- The last two sentences repeat the allocation-versus-reporting distinction through a short assertion followed by a separate negation. Combining them makes their logical relation easier to follow.
- "What can currently be said" hides the source of the report. Referring to accumulated evidence clarifies what the statistical task uses.
- "Answers the allocation question" can overstate what a small regret value provides. Calling regret a measure of allocation quality retains the intended distinction without implying that every allocation question has been settled.

### Final

> A sequential experiment may need to retain several promising alternatives while new alternatives continue to enter. Examples include a testing platform that receives externally generated designs and an experimental pipeline that introduces candidates during an ongoing study. The investigator must decide which alternative to sample and what the accumulated evidence says about the whole candidate set. Cumulative reward loss measures the quality of allocation, but a small loss does not guarantee that all alternatives within a specified tolerance of the current best can be distinguished from those outside it.

## Other changes and retained boundaries

The introduction now credits the established separation between reward collection and reporting directly, instead of explaining the credit by ruling out an overstated novelty claim. The paragraph on prior ALL-$\varepsilon$ work continues to identify $(\mathrm{ST})^2$ and FAREAST as essential comparisons. The two main results retain the same scope: a common-environment broadcast bound and worst-schedule area result, followed by a restricted multiple-update tradeoff. The initial-batch nature of the worst-case area lower bound, the two-budget restriction, and the lack of general checkpoint dominance remain explicit.

The discussion states the role of unresolved-time normalization in one connected passage. It still distinguishes vanishing unresolved counts from vanishing proportions, exempts boundary-band time without exempting issued labels from correctness, and reserves almost-sure eventual recovery for the revisable multiresolution construction. The fixed-checkpoint limitations, open instancewise scheduling problem, critical logarithmic question, and unknown service precision remain. The practical paragraph points to confidence-driven policies as a concrete next problem without turning that recommendation into a claim of a new proof.

The response now cites the actual main-text sections and records the completed study: 4 environments × 9 methods × 160 replications = 5,760 runs, with $T=20{,}000$. It reports the conservative fine-quota failure, strong identification adaptation's joint improvements in the stable and burst environments, the reward-versus-area tradeoff under successive improvements, and Growing MOSS's lowest regret in all four environments. It includes Batch100-UCB's three-component regret accounting, implementation parity, and the limited interpretation of zero observed report errors. It states that the new ALL-$\varepsilon$ comparator is an adaptation, not an implementation of FAREAST or $(\mathrm{ST})^2$.

The final source-document boundary is unchanged in substance: the original decision letter and verbatim earlier novelty report were not provided, so neither an invitation to resubmit nor exact reviewer wording is asserted.

The final discussion paragraph describes the supplementary proofs, numerical package, and simulated nature of the data. Its sentence about the research folder, revision map, and response draft was removed: those submission-process details belong in the research documentation rather than the scientific article.

## Text and provenance limits

This pass edits prose for a plain, precise academic voice. It does not detect or certify the removal of a statistical text watermark. No unknown detector, watermark key, or generation-level mechanism was available for such a test. Provenance and source attribution were retained.

All new or modified Markdown files were checked for the required dollar-sign math delimiters and standalone display delimiters. No em or en dash was introduced into the reviewed English prose.
