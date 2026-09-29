# E-16 resource_transform 1차 전체 클러스터링

- source: `gimmick_gap_report_0.6.2.json`
- resource_transform entries: **215**
- unique source_text: **214**
- exact duplicate source_text: **1**

## 주의
현재 ZIP의 전체 gap JSON에서 `resource_transform`은 99건이 아니라 215건이다. 99건은 다른 필터/분석 집합의 분모일 가능성이 있으므로 여기서는 실제 JSON의 215건을 기준으로 분석했다.

## 1차 Primary cluster (휴리스틱)

- **resource_gain_on_trigger**: 145건 (67.4%)
- **unclassified_resource_transform**: 48건 (22.3%)
- **affiliation_count_scaled_gain**: 15건 (7.0%)
- **special_state_candidate**: 2건 (0.9%)
- **cumulative_resource_gain**: 2건 (0.9%)
- **skill_reclassify**: 2건 (0.9%)
- **resource_scaled_damage_bonus**: 1건 (0.5%)

## 해석
- 위 숫자는 최종 Primitive 확정치가 아니라 원문 전체를 빠르게 구조화하기 위한 1차 primary clustering이다.
- 하나의 원문이 여러 primitive 신호를 동시에 포함할 수 있으므로 overlap도 별도 기록했다.
- `special_state_candidate`는 억지 일반화를 피하기 위해 독립 Runtime 후보로 분리했다.
- `unclassified_resource_transform`은 원문을 버리지 않고 다음 수동 클러스터링 대상으로 남겼다.

## 대표 패턴

### resource_gain_on_trigger (145)
- 중지 작은 형님 / 앙갚음 장부: 자신 또는 중지 소속의 아군 인격이 적에게 피격 시, 대상에게 복수 대상을 1 부여하고 앙갚음 장부 [히스클리프] 1 얻음 (스킬당 1회) / 아군 인격 사망시, 앙갚음 장부 [히스클리프] 3 얻음 /  / 턴 시작시 자신의 원한 문신이 15 이상이면 아래 효과 적용 / - 기본 스킬 하나를 ‘전원, 처형이다!!’로 변경 (가장 왼쪽 슬롯의 아래 스킬 우선 적용) / · 변경된 스킬이 다른 스킬로 변경되어 사용할 수 없게 되면, 위 효과를 다시 발동함 / - 이번 턴이 종료될 때까지 전투 BGM을 변경 (일부 전투 제외) /  / 대기 해제 또는 복귀로 등장한 턴의 전투 시작시, ‘내 헤어쿠포오오오온!!!!'을 무작위 

### unclassified_resource_transform (48)
- 거미집 엄지 제자 / 필사의 분전: 거미집 엄지 아비 로쟈가 전장에 있을 경우, 다음 효과 발동 / (자신이 패닉 또는 흐트러진 턴 제외) / - 거미집 엄지 아비 로쟈가 예지안이 있을 때 적에게 기본 스킬 적중 시, 해당 공격 종료 시점에 대상에게 '팔레르모 스파다'로 일방 공격 (턴당 1회) / - 전투 시작 시 거미집 엄지 아비 로쟈가 예지안 과열이 있는 상태에서 적으로부터 일방 공격으로 지정된 스킬이 있으면, 거미집 엄지 제자 히스클리프가 원호 방어 1 얻음 / (이 원호 방어는 거미집 엄지 아비 로쟈를 대상으로만 발동)

### affiliation_count_scaled_gain (15)
- LCCB 대리 / 돛대: 탄환을 가장 적게 보유한 아군 1명이 코인에서 마지막 탄환을 소모하면, 코인의 공격 종료 시, 각 대상에게 해당 코인의 공격으로 입힌 피해량의 50%만큼 추가 피해를 줌. (소수점 반올림)

### special_state_candidate (2)
- 거미집 검지 아비 / 신탁 단말기 [카두세우스]: 기본 공격 스킬의 코인마다 무기가 무작위로 정해져 특수한 효과가 적용됨 / - 손도끼로 갈비뼈를 찍어 내릴 때는… / - 스틸레토로 허파를 꿰뚫을 때는… / - 바스타드 소드로 어깨와 머리를 짓이길 때는… / - 레이피어로 몸에 10개 이상의 구멍을 내야할 때는… / - 망치로 뒤통수를 으깨야 할 때는… / - 커다란 검으로 몸통을 갈라야 할 때는… / - 랜스로 20인치의 구멍을 내야 할 때는… / - 채찍으로 살점을 만 갈래 떼어내야 할 때는… / - 낫으로… 누군가처럼 공간을 따라 베어내야 할 때는… /  / 지령 표식 스킬 사용 시, 대행 [헤르메스] 1 얻음 /  / 이번 전투에서 ‘Furioso-Replica
- 거미집 검지 아비 / 신탁 단말기 [카두세우스]: 기본 공격 스킬의 코인마다 무기가 무작위로 정해져 특수한 효과가 적용됨 / - 손도끼로 갈비뼈를 찍어 내릴 때는… / - 스틸레토로 허파를 꿰뚫을 때는… / - 바스타드 소드로 어깨와 머리를 짓이길 때는… / - 레이피어로 몸에 10개 이상의 구멍을 내야할 때는… / - 망치로 뒤통수를 으깨야 할 때는… / - 커다란 검으로 몸통을 갈라야 할 때는… / - 랜스로 20인치의 구멍을 내야 할 때는… / - 채찍으로 살점을 만 갈래 떼어내야 할 때는… / - 낫으로… 누군가처럼 공간을 따라 베어내야 할 때는… /  / 지령 표식 스킬 사용 시, 대행 [헤르메스] 1 얻음

### cumulative_resource_gain (2)
- 라만차랜드 공주 / 경혈의 가시: 자신을 제외한 아군이 출혈 피해를 받거나 혈찬을 소모할 때마다, 자신이 피어나는 가시 1 얻음 (턴 당 최대 5회) / 자신이 기본 스킬로 가한 피해량의 20%만큼 자신의 체력 회복 (스킬당 최대 10) / - 자신이 최대 체력이면, 초과하는 회복량만큼 현재 체력 비율이 가장 낮은 아군 1명의 체력 회복
- 라만차랜드 공주 / 경혈의 가시: 자신을 제외한 아군이 출혈 피해를 받거나 혈찬을 소모할 때마다, 자신이 피어나는 가시 1 얻음 (턴 당 최대 3회) / 자신이 기본 스킬로 가한 피해량의 20%만큼 자신의 체력 회복 (스킬당 최대 10)

### skill_reclassify (2)
- 동부 시 협회 3과 / 저격 - 활: 자신이 저격 자세 상태면, 가장 왼쪽에 장착한 기본 공격 스킬을 ‘섬궁’으로 변경하여 전투 시작 시 사용함. / - 이 효과 발동시 자신의 목표 조준이 최대 수치이고, 조작 패널과 예비 스킬 슬롯에 스킬 3이 없으면,  / 가장 왼쪽 슬롯에 장착한 수비 스킬을 스킬 3으로 취급하여 ‘섬궁’으로 변경함 /  / 사용하는 기본 공격 스킬에 따라 아래 효과 적용 (죄악 속성은 사용한 스킬 속성을 따름) / - 스킬 1: 기본 위력 +1, 피해량 +11% / - 스킬 2: 기본 위력 +1, 코인 위력 +1, 피해량 +22% / - 스킬 3: 기본 위력 +4, 코인 위력 +4, 피해량 +44% /  / ※ E.G.O 스킬 장착하
- 마침표 사무소 대표 / 제압 사격: 탄환을 가장 많이 보유한 아군 인격이 탄환을 소모하는 스킬로 가하는 피해량 +10% / (탄환이 없으면 적용되지 않음)

### resource_scaled_damage_bonus (1)
- LCA 우제트 선봉 3팀 팀장 / 선봉대: 자신의 보호 1당, 피해량 5% 증가 (최대 15%) /  / 전투 시작 시 우제트의 눈 [선봉] 2 얻음

## 다음 단계
1. 215건의 미분류/복합 항목을 수동 검토한다.
2. A~H를 최종 Primitive 이름으로 확정하기 전에 Condition/Target/Effect로 다시 분해한다.
3. `resource_transform` 내부에서 기존 `common.py`가 이미 처리하는 규칙과 신규 Primitive를 분리한다.
4. 이후 Primitive schema를 코드로 구현한다.
## 5. 원시자 관점의 1차 결론

전체 `resource_transform` 215건을 원문 전체 단위로 하나의 Primitive에 배정하면 오히려 오분류가 발생한다. 실제로 한 항목 안에 여러 독립 규칙이 함께 들어 있다. 따라서 **항목 단위가 아니라 규칙 절(clause) 단위로 Condition / Target / Effect를 분해한 뒤 Primitive를 조합**해야 한다.

확인된 대표 Primitive는 다음과 같다.

| Primitive | 확인된 실제 패턴 | 기존 구조 | 판단 |
|---|---|---|---|
| Trigger → ResourceGain | 피격/사망/처치/적중/턴 종료 등 → 자원 획득 | `common.py` 일부 | **일반화 우선** |
| AffiliationCount → Gain/Modifier | 소속 인원 수/사망자 수/조건 인원 수에 따른 자원·효과 | 부족 | **신규** |
| CumulativeSpend → Reward | 자원 N 누적 소모마다 다른 자원/효과 획득 | `cumulative_resource_gain` 부분 구현 | **확장** |
| ResourceScaledModifier | 자원 1당 피해/위력/방어 등 변화 | 부분/분산 | **신규 공용 Modifier** |
| ResourceZero → Effect | 자원 0/없음 → 상태/스킬 변환 | 부분 | **Condition + Effect 조합** |
| LowestResourceSelector | 소속/아군 중 특정 자원이 가장 낮은 대상 | `lowest_ammo_poise` 등 | **Selector 일반화** |
| RandomTarget × CountScaling | 무작위 대상 + 사망/소속 수에 따른 추가량 | 분산 | **Primitive 조합** |
| SkillMetadata/SkillReclassify | 특정 스킬을 특정 자원 획득/사용 스킬로 취급 | 부족 | **Skill metadata** |
| SpecialState | 예지안/코인별 무기 등 자체 상태 머신 | 없음/전용 필요 | **독립 Runtime 인정** |

### 중요한 구조적 결론

`resource_transform`은 하나의 Runtime을 만드는 카테고리가 아니다. 이 태그는 **Resource를 조건·대상·효과로 변환하는 규칙군을 묶은 분석 태그**다. 따라서 구현도 다음처럼 해야 한다.

```text
RuleIR
 ├─ Condition
 │   ├─ Trigger
 │   ├─ ResourceCompare / ResourceZero
 │   ├─ AffiliationCount
 │   └─ Threshold
 ├─ Target
 │   ├─ Self
 │   ├─ Affiliation
 │   ├─ LowestResource
 │   └─ Random
 └─ Effect
     ├─ ResourceGain
     ├─ ResourceConsume
     ├─ ResourceTransform
     ├─ ResourceScaledModifier
     ├─ StatusApply
     └─ SkillTransform / SkillMetadata
```

이 구조를 먼저 확정하면 특정 인격 이름을 박은 `middle_revenge_hit`, `bio_material_kill_bonus`, `lowest_ammo_poise`류를 점진적으로 공용 Primitive 조합으로 치환할 수 있다.

## 6. 현재 단계에서 코드 구현을 보류한 이유

이번 E-16은 **Primitive Pattern Audit**이다. 215건을 전부 수동 검증하기 전에 자동 분류 결과만으로 코드를 확정하면, 하나의 인격 설명에 포함된 여러 규칙을 하나의 Runtime으로 잘못 묶을 위험이 있다.

따라서 이번 단계의 산출물은:

1. 전체 대상 수 확정
2. 원문 중복 확인
3. clause 단위 분해
4. 반복 Primitive 후보 확인
5. 기존 구현과 신규 구현의 경계 확인
6. 특수 Runtime으로 남겨야 할 사례 식별

까지로 제한한다.
