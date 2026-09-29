# Status Effect Lifecycle Taxonomy 0.7.0

기준 문서: OldBoom/Limbus-Company-Auto-Guides `docs/status-effects.md` (원문은 limbuscompany.wiki.gg Status Effects를 ground truth로 지정).

## 상위 분류
- CONSUME: 게임 이벤트/자원 사용으로 값이 소모되는 상태. `consume_on` 또는 명시적 resource consumption이 필요.
- TURN: 시간/턴 경과가 수명 기준인 상태. 일반적인 1턴 Modifier와 Turn End 감소형을 포함하되, 값의 Count가 반드시 소비 횟수라는 뜻은 아님.
- RULE: 특정 조건/트리거/변환/상호작용으로 상태가 제거·변환·변경되는 상태.
- UNSPECIFIED: 자료만으로 상위 lifecycle을 안전하게 단정하지 않고 명시 선언을 요구.

## 핵심 결론
1. `Count`는 의미가 하나가 아니다. Potency의 강도, duration, stack, resource, 실제 consumption count 등으로 쓰일 수 있다.
2. 따라서 runtime의 `count` 필드는 lifecycle과 분리해야 한다.
3. 표준 1턴 modifier는 TURN, Bleed/Rupture/Sinking/Poise/Charge 등은 CONSUME 계열, 복합 상호작용은 RULE 계열로 보는 것이 일관적이다.
4. Burn/Tremor는 `Turn End`에서 효과가 발동하고 Count가 감소하므로 CONSUME이면서 소비 이벤트가 `turn_end`인 특수한 소비형이다.
5. 특수 상태는 하나의 lifecycle만으로 모든 동작을 설명할 수 없는 복합형이 많다. 이 경우 `lifecycle=RULE` + 별도 trigger/effect를 우선하고, 내부 효과에 CONSUME/TURN 동작을 포함시킨다.

## 표준/핵심 상태 분류
| 상태 | Lifecycle | Count 의미 | 소비/종료 이벤트 |
|---|---|---|---|
| Burn | CONSUME | 발동 Count | turn_end |
| Bleed | CONSUME | 발동 Count | attack_coin |
| Tremor | CONSUME | duration/발동 관리 Count | turn_end |
| Rupture | CONSUME | 발동 Count | on_hit |
| Sinking | CONSUME | 발동 Count | on_hit |
| Poise | CONSUME | crit/turn-end 소비 Count | on_critical + turn_end |
| Charge | CONSUME | resource Count | skill/resource use + turn_end |
| Power Up | TURN | effect strength | turn_end |
| Attack Power Up | TURN | effect strength | turn_end |
| Defense Power Up | TURN | effect strength | turn_end |
| Clash Power Up | TURN | effect strength | turn_end |
| Base Power Up | TURN/explicit duration | effect strength | duration rule |
| Offense Level Up | TURN | potency | turn_end |
| Defense Level Up | TURN | potency | turn_end |
| Haste | TURN | effect strength | turn_end |
| Damage Up | TURN | effect strength | turn_end |
| Protection | TURN | effect strength | turn_end |
| Crit DMG Up | TURN | stack/effect strength | turn_end |
| Plus Coin Boost | TURN | effect strength | turn_end |
| Minus Coin Drop | TURN | effect strength | turn_end |
| HP Healing Boost | TURN | effect strength | turn/duration rule |
| Weak-resist DMG Boost | TURN | effect strength | turn_end |
| E.G.O Resource Amp | TURN | effect strength | turn_end |
| Power Down | TURN | potency | turn_end |
| Attack Power Down | TURN | potency | turn_end |
| Defense Power Down | TURN | potency | turn_end |
| Clash Power Down | TURN | potency | turn_end |
| Offense Level Down | TURN | potency | turn_end |
| Defense Level Down | TURN | potency | turn_end |
| Bind | TURN | potency | turn_end |
| Damage Down | TURN | effect strength | turn_end |
| Fragile | TURN | effect strength | turn_end |
| Paralyze | TURN | number of affected coins | turn_end |
| Plus Coin Drop | TURN | effect strength | turn_end |
| Minus Coin Boost | TURN | effect strength | turn_end |
| HP Healing Down | TURN | effect strength | duration rule |
| Poison | CONSUME | damage Count | turn_end |
| Immobilized | TURN | fixed state | this turn |

## Typed Modifier Families
Slash/Pierce/Blunt 및 Wrath/Lust/Sloth/Gluttony/Gloom/Pride/Envy의 DMG Up, Power Up, Protection, DMG Down, Power Down, Fragility, Resist Down은 모두 **TURN** family로 분류한다. 이들은 별도 runtime이 아니라 `DamageModifier`의 selector(attack type/sin affinity)로 일반화할 수 있다.

## 특수 상태 분류 — source descriptions 기반
### RULE 우선
- Dark Flame — turn-end effect + expiry, value가 Burn Potency와 상호작용
- Spore — turn-end Burn Count 생성 + Bind next turn
- Resident Reg. Microchip — clash-lost trigger + turn-end stack loss
- Searing Birdcage — Burn 조건 + turn-end bind/stack 변환
- Nails — turn-start Bleed generation + turn-end halving
- Red Plum Blossom — critical trigger
- Needle — damage/turn-end triggers + stack consumption
- Corpus Theater (Hong Lu) — gaining Bleed from enemy skill trigger
- Rose Wedge — Bleed damage interaction + amplification/reflection
- Maggots — turn-end damage + Bleed Count generation
- Tremor - Decay — Tremor potency-derived Defense Level change
- Tremor - Reverb — Tremor Burst trigger
- Tremor - Everlasting — probabilistic extra Burst trigger
- Tremor - Chain — potency-derived Clash Power change
- Tremor - Scorch — Tremor Burst consumes Burn Count
- Tremor - Hemorrhage — Tremor Burst consumes Bleed Count
- Tremor - Superposition — conversion/combination state
- Time Moratorium — stores damage and releases on expiry
- Butterfly — turn-end conversion/reset
- Sheut Fracture — threshold trigger at max Stack
- Sinking Deluge — consumes/removes Sinking on activation
- Faint Aroma — threshold trigger → Tremor Burst/damage
- The Uninvited — death trigger
- Photoelectricity — hit trigger → Charge; expiry turn end
- Spark Discharge — hit trigger → Charge/Rupture changes
- Charged Sting — conditional damage modifier by Charge-consuming skills
- Lasso — turn-end Rupture/Bind generation + stack loss
- Concussion — turn-end stack loss + modifier
- Open Wound — turn-end Bind + stack threshold conversion
- Talisman — on-hit Rupture consumption/application
- Twisted Curse Talisman — threshold trigger + expiry consequence
- Echoes of the Manor / Impending Ruin / Shattermark / Blue Sand / Dazzle / Solitude — Panic/condition-triggered behavior
- Bloodflame / Fanatic / Blooming Thorn / Festive Fever / Shimmering / Dark Cloud Blade / Battle Ready / Strider / Rupture Protection / Burgeoning of Horns / Wild Hunt — identity-specific conditional/interaction states
- Contempt of the Gaze / Erudition / Hardblood Armor / Focused Performance / Tarnished Blood / Fell Bullet / Linebreaker / Iron Maiden / Overcharge / Gebura's Blade — identity-specific states with trigger/resource/turn interactions
- Mark of Decay / Sewing Target — identity-specific debuff modifiers with condition-dependent effects
- Deathrite variants — explicitly triggered by Rupture plus additional conditions

### TURN-leaning but still explicit
- Shattered World — expires Turn End; can be represented as TURN with an explicit modifier bundle.
- Sewing Target — has a turn-like countdown in source description; model duration explicitly rather than treating its numeric value as consumption count.

### RESOURCE / NEUTRAL (not ordinary Buff/Debuff)
- Aggro — targeting state
- Unbreakable Coin — combat rule/state, not ordinary modifier
- Corpus Ingredient — resource-like Count
- Bloodfeast — resource consumed/gained through Bleed interactions
- Torn Memory — skill resource
- K Corp Ampule — turn-start threshold behavior
- Discard — resource mechanic
- Insight — resource/interaction state
- Procuration — threshold resource/state unlocking skill
- Tianjiu Star's Blade — stack + turn-end effect
- Arrow — skill resource
- Magic Bullet — skill scaling resource/state
- Responsibility — modifier state with unique interaction
- Surgery — threshold/death state

## Implementation implication
`BuffDebuffRuntime` should remain the common storage/modifier layer. It should not become the implementation home for every special status. Use:
- BuffDebuffRuntime: standard TURN modifiers + simple declarative CONSUME/RULE expiry hooks.
- KeywordRuntime: Bleed/Burn/Tremor/Rupture/Sinking/Poise/Charge semantics.
- SpecialRuleRuntime: identity-specific conversions, threshold triggers, stored damage, panic/death interactions, and cross-status interactions.

## Coverage status
This document is a taxonomy/design audit, not a claim that every row has been fully verified in the calculator. Any effect not explicitly encoded in the runtime must remain UNSPECIFIED until its source rule is added.
