# F-CCP integration contract audit

Status: DONE for the four inline text blocks and their existing-proof interfaces. This record is a source and mathematical-contract check, not independent peer review or formal verification. No new theorem or simulation was created.

The four fields of `fccp_method.json` are intended for direct insertion into the two existing manuscript entry files. No new `.tex` source was created, and the research inputs were not edited.

## Sources and proof dependencies

The full arbitrary-action bridge was checked against the stage-2 companion source, not inferred from the regret of MC-MOSS itself. Its retained-history potential-prefix lemmas allow arbitrary selected, nonrepeating arm--count pairs. Clipping leaves the lower comparison for the true best arm valid even when that arm is unobserved. The decomposition adds the observable index gap, the segment cost is at most $15\sqrt{dh}$, and capacity-doubling charging gives $(1+60/(1-2^{-1/2}))\mathcal S_T<210\mathcal S_T<300\mathcal S_T$. The deterministic deletion/delay comparison also gives $\overline{\mathcal S}_T\le2\mathcal S_T$.

The mixture proof covers all bounded rewards by the chord bound for the exponential factor, followed by Beta mixing and Ville crossing. Mixture and fixed-checkpoint errors each cost $\delta/2$. Rectangular extrema explicitly exclude the arm itself. Pair-plan optimization is identified only as a continuous proxy, with its interior, boundary, zero-radius, and no-extra-work cases.

## Final-branch checks

- The final rule is `flexible_v2.py::choose_dual`, together with the interactive `FlexibleCCP`; the older `choose_flexible` is not used as the final dual-ledger specification.
- A refused service consumes exactly one attempt/phase increment and reveals no proposed reward. The reward kernel generates its score vector once and maximizes it in the reward-feasible set.
- Ledgers are separate and persistent. Preference changes preserve counts, evidence, virtual clock state, phase, and ledgers. Turning preference to one does not disable the certification guard.
- Pair endpoint score ties favor the current candidate $i$; pair-cost/reference/fallback ties follow the first fixed scan. A blanket claim that every tie uses earliest arrival would be inaccurate.
- The planning floor $\max(1,n_i)$ does not change actual counts; legal endpoint increments are compared with actual $n_i$. Numerical tolerances are disclosed separately.
- F-R and compatibility have inactive service budgets. Frozen `null` and API zero do not alter their service-free behavior and were not rewritten.

## Scope retained

- Finite-budget reward constant: $300+2\beta_R+2\beta_C$; F-R $332$, Balanced $334$. Classification retains the extra $Q_T^{\mathrm{cap}}$ term.
- Area bounds retain $D_T^{\mathrm{srv}}$ for finite certification budgets and require a common positive busy-round rate. Unlimited certification plus priority one yields the matching worst-area order only in the inherited lower-bound parameter range.
- The finite-arm completion result requires $\beta_C>0$, eventual finite arrivals, and the coverage event; it does not assert unconditional almost-sure exact-set consistency.
- Compatibility requires no service from the beginning, disabled reward guard, same complete kernel state, and the same backend random source. F-R is a distinct cold guarded configuration.
- The $1/8$ one-round obstruction concerns only the explicit zero-remainder universal comparison with two fixed initializations.

## Blockers

No BLOCKED_PROOF_INTERFACE was found for these four blocks. The companion mathematical source is present; its bibliographic identity must remain an unpublished companion manuscript unless independently established publication information is available. Source attribution uses the parent integration key `temporalgeometry2026`.

## Input hashes

| Read-only input | SHA-256 |
| --- | --- |
| `CCP_research_2026-10-16/theory.md` | `e0c8c947b7f399e2b1d21dba10fdc8a505a50b47a2db6425ad49a4ea144680df` |
| `F-CCP_2026-10-17/theory.md` | `16d75dce4bab7e77403660fd8c54c94d4b6a2b353dc9b7d1f72fa5633ec4b630` |
| `F-CCP_2026-10-17/src/flexible_v2.py` | `4b3f895b0e6352fd660283bc75b1e2e5bb90eb5268ef627c23386862b416dac7` |
| `F-CCP_2026-10-17/src/flexible_ccp.py` | `7286f226f49a8fc3e0ca0d53c8f42dacc92f360e04d74dad337c771a5478ab7a` |
| `F-CCP_2026-10-17/src/flexible_engine.py` | `453c22588b64e53de6cc32d103af98468fa31e61ba46acadc655aa27e03b88c4` |
| `F-CCP_2026-10-17/src/ccp_primitives.py` | `e3fbf8194b1b7559db6c60a1cff0d12c79c229034fe77aaf1dc3e89b58c4769f` |
| `F-CCP_2026-10-17/src/matched_all.py` | `46a7b8b308a89467f8c5dac3d464e1a9ec5eacbf6ca56e60dd06091af815251c` |
| `F-CCP_2026-10-17/protocols/holdout-freeze.json` | `7d4b8536869250ce3b19ad5f15ddf388c16ed17ca058a94171b694ad29229668` |
| `reconstruction_jasa_stage2_2026-10-13/sections/03_policy.tex` | `79f54d9efcdb1f211cf23051e133848d2bf52d8460fa9de32946ac09b46ee481` |
| `reconstruction_jasa_stage2_2026-10-13/sections/S1_spectral_proofs.tex` | `918237fb2ba83968c55f1f1933425ab090c1aaf10d1170e3025be53145603a66` |
