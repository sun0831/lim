# Identity Keyword / Affiliation / Personal Mechanic Classification 0.6.18

## Classification order
1. Generic keyword: one of the seven global combat axes.
2. Combat affiliation: affiliation that changes cross-identity combat behavior.
3. Affiliation-bound mechanic: named resource/state whose lifecycle is primarily owned by one combat affiliation.
4. Shared resource: independent resource used across unrelated affiliations.
5. Identity-specific mechanic: explicit named mechanic belonging to one identity.
6. Raw affiliation remains descriptive metadata and is never promoted automatically.

## Seven generic keywords
- charge / 충전
- bleed / 출혈
- poise / 호흡
- tremor / 진동
- burn / 화상
- rupture / 파열
- sinking / 침잠

`생체 재료` is a keyword-equivalent resource: it uses the Charge axis; Ring owns its acquisition/consumption rules.

## Confirmed combat affiliation modules
- blade_lineage / 검계
- thumb / 엄지
- middle / 중지
- ring / 약지
- index / 검지
- pequod / 피쿼드호
- black_cloud / 흑운회
- spider_house / 거미집
- dawn_office / 새벽 사무소
- seven / 세븐
- zwei / 츠바이
- liu / 리우
- n_corp / N사
- w_corp / W사
- full_stop / 마침표
- la_mancha_land / 라만차랜드

Membership is multi-label. A confirmed module can be loaded even if its current rule provider is empty; this preserves the classification axis for future rules.

## Affiliation-bound mechanics
- dawn_office: 새벽불, 불꽃나비의 관, 새벽녘
- index: 검지의 지령 / 지령
- middle: 중지 - 원한, 중지식 강화 문신, 원한 문신, 앙갚음 장부, 원한 스탬핑
- ring: 생체 재료 (Charge-equivalent), ring-specific lifecycle
- spider_house: 예지, 예지안
- thumb: dedicated ammunition-support interactions remain affiliation rules, while 탄환 itself is not promoted to a global keyword
- pequod: Captain support/Pequod-specific assist interactions
- black_cloud: received-attack support interactions

## Identity personal mechanics
The per-identity matrix does not infer mechanics from names. `named_mechanics` are only explicit named resources/states found in the source skill/passive text or the project resource catalogs. `effect_tags` are source catalog effect tags excluding attack type labels and generic seven-keyword labels.

Examples include:
- 탄환
- 얽힘
- 작품명
- 섬궁
- 흑풍마각월참
- 폐장 - 설치미술 제 1호
- 내 헤어쿠포오오오온!!!!
- 열기
- 가속탄
- 처분
- 즉결처형
- 새벽녘
- 원한 스탬핑

These are not automatically new global keywords.

## File split
### Generic keyword modules
- `gimmick_modules/charge.py`
- `gimmick_modules/bleed.py`
- `gimmick_modules/poise.py`
- `gimmick_modules/tremor.py`
- `gimmick_modules/burn.py`
- `gimmick_modules/rupture.py`
- `gimmick_modules/sinking.py`

### Affiliation modules
- `gimmick_modules/blade_lineage.py`
- `gimmick_modules/thumb.py`
- `gimmick_modules/middle.py`
- `gimmick_modules/ring.py`
- `gimmick_modules/index.py`
- `gimmick_modules/pequod.py`
- `gimmick_modules/black_cloud.py`
- `gimmick_modules/spider_house.py`
- `gimmick_modules/dawn_office.py`
- `gimmick_modules/seven.py`
- `gimmick_modules/zwei.py`
- `gimmick_modules/liu.py`
- `gimmick_modules/n_corp.py`
- `gimmick_modules/w_corp.py`
- `gimmick_modules/full_stop.py`
- `gimmick_modules/la_mancha_land.py`

### Execution ownership migrated out of the monolith
The concrete trigger builders for Ring, Middle, Spider House, Black Cloud, Pequod, and Dawn Office are now defined in their respective module files. `ModuleResolver` asks the selected module provider for rule ownership. `special_gimmick_v2.py` remains the compatibility/parser orchestration layer and delegates module-owned trigger construction.

## Verification
- Identity catalog: 184 identities
- Seven-keyword counts: charge 25, bleed 53, poise 41, tremor 37, burn 28, rupture 50, sinking 32
- Full regression suite: 273 passed
- Python syntax check: PASS
