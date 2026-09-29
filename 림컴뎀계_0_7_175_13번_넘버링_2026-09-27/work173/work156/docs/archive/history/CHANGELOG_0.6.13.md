# 0.6.13

## Identity keyword / affiliation manifest + gimmick module ownership

- Added `identity_module_manifest_v1.json` for all 184 identities.
- Seven generic combat keywords and affiliation/gimmick modules are maintained as independent multi-label axes.
- Generic keyword labels: Charge, Bleed, Poise, Tremor, Burn, Rupture, Sinking.
- Ring Finger's `생체 재료` is classified under Charge while Ring remains an independent affiliation/gimmick module.
- Added normalized gimmick-module classification for Dawn Office, Middle Finger, Pequod Crew, Ring Finger, Spider House, and Black Cloud.
- ModuleResolver now prefers the generated per-identity manifest and retains runtime fallback for legacy/custom identity objects.
- Added explicit rule ownership metadata for affiliation-specific gimmick rules.
- Existing combat/runtime engines remain unchanged; this is a safe modularization layer before further parser extraction.
- Tests: 262 passed.

### 0.6.16
- Expanded affiliation taxonomy with evidence-based combat-affiliation confirmation.
- Added explicit keyword-equivalent resource classification; Bio Material maps to Charge.
