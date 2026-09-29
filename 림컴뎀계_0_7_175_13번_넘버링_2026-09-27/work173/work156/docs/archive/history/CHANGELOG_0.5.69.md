# 림컴뎀계 0.5.69

## Support/Assist generic bridge
- Formation-relative support-command parsing generalized beyond a hard-coded identity.
- Explicit `자신의 우측에 위치한 아군에게 ... 원호 공격을 명령함` is represented as a generic right-ally support rule.
- Explicit left-ally counterpart is supported as `ally_left`.
- Captain Ishmael retains the legacy `captain_right_assist` label for compatibility, but execution uses the same generic `ally_right` resolver.
- Support actions continue to use the selected ally's next requested skill rather than inventing or optimizing a skill.
- Stated probability is normalized to 100% under the project's high-roll convention.

## Verification
- 184 identities scanned.
- 19 gimmick rules registered.
- 138 pytest tests passed.
