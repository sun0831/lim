# Identity Rule Classification 0.6.18-r1

## Four physical layers
1. **소속**: cross-identity/group combat rules.
2. **키워드**: Charge/Bleed/Poise/Tremor/Burn/Rupture/Sinking.
3. **공통**: reusable trigger shapes whose owner is supplied by identity data.
4. **인격 전용**: rules whose trigger/effect semantics are specific to one identity.

`생체 재료` remains a Charge-equivalent resource. Ring only owns its acquisition/consumption rules.

## Current parsed rule ownership
- Affiliation: Middle, Ring, Pequod, Spider House, Black Cloud, Dawn Office.
- Common: assist/follow-up, clash-loss follow-up, kill/resource/heal patterns, ammo/poise, extra damage, resource lifecycle.
- Identity-specific: enemy-HP follow-up, forced skill, conditional assist, reused-status damage.
- Keyword modules: the seven generic combat keywords; no keyword-specific rule math was moved into the affiliation layer.

The full 184-identity matrix is in `RULE_LAYER_CLASSIFICATION_0.6.18.json`.
