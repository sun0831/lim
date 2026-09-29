# Gimmick Gap Report v3 — 0.5.51

## Audit target
- Identity catalog: 184 identities
- Base skills: 621
- Passive records: 588
- Existing passive compiler report: 349 passives compiled, 239 passives with at least one unsupported clause.

## 0.5.51 implemented first-priority skill mechanics
1. Explicit status potency/count based damage scaling.
2. Explicit status threshold damage bonuses.
3. Hit-based percentage extra damage (`damage dealt × percentage`).

These are evaluated at the relevant coin timing so preceding coin effects can change the condition for later coins.

## Why these were prioritized
They directly alter damage on ordinary skills and occur repeatedly across the current catalog. They are also generic enough to implement without identity-specific hardcoding.

## Remaining high-impact gaps
### A. Additional/reused attacks
Examples include `추가 공격`, skill reuse, forced named skill execution, and generated attacks tied to specific resources. The runtime can execute declarative `queue_action`, but many catalog texts still need reliable compilation into such rules.

### B. Resource transformation / conversion
Examples: resource A consumed and resource B gained, threshold-based resource conversion, reload behavior, and split-ammo systems. These require explicit resource semantics rather than treating every named resource as a generic integer.

### C. Target selection
Patterns such as fastest/slowest ally, highest/lowest HP, highest/lowest resource, formation-order selection, random target, and focused-combat part targeting are not fully generic in the passive compiler.

### D. Skill transformation / slot replacement
Patterns such as replacing a basic skill with a named variant at turn/combat start, or changing a defense skill into a special attack, need stronger slot-level runtime support.

### E. Probability-driven effects
Some effects have explicit probabilities. These should be represented as branch probabilities in probabilistic mode rather than silently rounded to deterministic effects.

### F. Multi-target / area damage
Attack weight and multiple targets need a dedicated target-set model so damage, status application, and stagger are attributed correctly.

### G. Clash-start / clash-win / clash-loss condition coverage
The trigger runtime supports these events, but the compiler still cannot reliably convert every prose clause into the corresponding event/condition/effect combination.

### Conservative rule
Do not auto-execute ambiguous prose. Keep unsupported source text visible and only promote patterns whose timing, target, and numerical meaning can be established unambiguously.
