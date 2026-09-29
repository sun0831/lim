# 0.5.70 — conditional cross-identity assist triggers

## Changes
- Cross-identity assist rules now require the assisted identity to be present in the configured combat roster before the trigger can fire.
- Fixed natural-language trigger extraction so quoted skill names are stripped of surrounding whitespace before `skill_name_any` matching.
- Added generic `highest_resonance_gte` trigger condition.
- Captain Ishmael's stated probability remains normalized to 100% in the project's high-roll convention, while zero highest resonance does not satisfy the underlying resonance condition.
- Passed current resonance counts from the one-turn solver into `after_skill` trigger context.
- Existing source-skill / owner-specific assist behavior remains otherwise unchanged; ambiguous prose is not auto-compiled.

## Verification
- 140 pytest tests passed.
- 184-identity catalog scan completed.
