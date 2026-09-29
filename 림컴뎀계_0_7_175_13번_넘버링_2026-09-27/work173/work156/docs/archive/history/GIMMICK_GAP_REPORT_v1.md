# 림컴뎀계 특수기믹 구현 공백 분석 v1

- 인격: 184개
- 패시브 레코드: 588개
- 완전 컴파일: 193개
- 부분 컴파일/미지원 요소 포함: 156개
- 완전 미지원: 239개

## 미지원 사유

- `effect`: 408
- `trigger`: 543

## 우선 구현 후보

아래 목록은 단순히 미지원 개수 순서가 아니라, 1턴 데미지 계산에 영향을 크게 주는 동적 트리거/자원/스킬 변환/연계 기믹을 우선 표시한다.

### 1. 중지 작은 형님 — 앙갚음 장부
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger, effect, trigger, trigger, trigger, effect
- 분류: action_trigger, target_selection, resource_transform, skill_transform, probability_random, multi_target, stack_threshold, cross_identity
- 원문: 자신 또는 중지 소속의 아군 인격이 적에게 피격 시, 대상에게 복수 대상을 1 부여하고 앙갚음 장부 [히스클리프] 1 얻음 (스킬당 1회)
아군 인격 사망시, 앙갚음 장부 [히스클리프] 3 얻음

턴 시작시 자신의 원한 문신이 15 이상이면 아래 효과 적용
- 기본 스킬 하나를 ‘전원, 처형이다!!’로 변경 (가장 왼쪽 슬롯의 아래 스킬 우선 적용)
· 변경된 스킬이 다른 스킬로 변경되어 사용할 수 없게 되면, 위 효과를 다시 발동함
- 이번 턴이 종료될 때까지 전투 BGM을 변경 (일부 전투 제외)

대기 해제 또는 복귀로 등장한 턴의 전투 시작시, ‘내 헤어쿠포오오오온!!!!'을 무작위 대상에게 사용함
- 해당 공격 종료 시 모든 아군 중지 인격에게 공격 레벨 증가 1, 방어 레벨 증가 1 부여

### 2. 거미집 검지 아비 — 단말기로 전해진 지령
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, skill_transform, probability_random, special_state
- 원문: 턴 시작 시,
- 자신의 해금 단계에 따라 지령[단말기] I/지령[단말기] II/지령[단말기] III/지령[단말기] IV 얻음
- 무작위 적 1명에게 지령 대상 부여 (집중 전투면, 부위에 부여)
- 조작 슬롯의 자신의 기본 공격 스킬에 지령 표식 부여 (슬롯당 1개, 최대 2개 부여)
· 해금 - II 이상이면, 스킬 3에 우선 부여 (강화된 스킬 우선)
- 흐트러짐, 행동 불가, 패닉, E.G.O 침식 상태면, 위의 모든 효과와 지령 수행 여부가 적용되지 않음

### 3. 거미집 약지 제자 — 소중한 작품 파시아
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, trigger, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state, stack_threshold, cross_identity
- 원문: 스테이지 첫 등장 시 자신의 생체 재료 횟수가 (전장에 있는 약지 소속 아군 수 x 2)만큼 증가 (최대 10)

스킬 종료 시 해당 스킬로 체력 또는 보호막 피해를 입혔으면, 자신의 생체 재료 횟수 5 증가
- 대상이 사망했으면, 추가로 횟수 3 증가

전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음
- 위 효과로 생체 재료 위력이 2 이상이 되면, 작품명: 파시아 얻음

기본 공격 스킬과 합 가능 반격 스킬이 충전 횟수를 얻는 스킬로 취급됨

### 4. 거미집 약지 아비 — 일생의 작품 티비아
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, trigger, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state, stack_threshold, cross_identity
- 원문: 스테이지 첫 등장 시 자신의 생체 재료 횟수가 (전장에 있는 약지 소속 아군 수 x 2)만큼 증가 (최대 10)

스킬 종료 시 해당 스킬로 체력 또는 보호막 피해를 입혔으면, 자신의 생체 재료 횟수 5 증가
- 대상이 사망했으면, 추가로 횟수 3 증가

전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음
- 위 효과로 생체 재료 위력이 2 이상이 되면, 작품명: 티비아 얻음

기본 공격 스킬과 합 가능 반격 스킬이 충전 횟수를 얻는 스킬로 취급됨

### 5. 거미집의 검 — 재회 [再會]
- 상태: **partial** / 컴파일 규칙 4개
- 미지원: trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, effect, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, skill_transform, multi_target, special_state, cross_identity
- 원문: 전투에 첫 등장 시, 얽힘 0, 절연 [絕緣] 0 얻음
전투에 첫 등장 시, 편성된 거미집 소속 아군 인격(자신 포함) 3명당 얽힘 버프의 최솟값, 최댓값 1 증가 (최대 3)
거미집 소속 인격이 출전 중이면, 자신이 체력 피해를 받을 때 현재 체력 비율이 가장 낮은 거미집 소속 아군 인격에게 받은 피해를 전가함
체력이 0이 되는 피해를 받을 때 해당 턴 동안 체력이 1 미만으로 감소하지 않음 (전투당 1회)
거미집 소속 아군 인격이 사망한 상태면, 아래 효과 적용
- 얽힘 1 얻음
- 사망한 인격에 따라 이번 전투 동안 아래 추가 효과를 얻음
· 검지 아비 이상 : 기본 공격 스킬 사용시 마지막 코인이 파괴 불가 코인으로 변경됨. 기본 공격 스킬의 파괴 불가 코인의 피해량 +10%
· 검지 대행자 - 개화 E.G.O::대행 돈키호테 : 기본 공격 스킬 사용시 호흡 2 얻음. 기본 공격 스킬 크리티컬 적중시 침잠 1 부여
· 중지 제자 이스마엘 : 방어 레벨 2 증가, 기본 스킬로 부여하는 화상 위력 +1
· 약지 아비 홍루 : 신체가 울리는 선율 얻음
· 약지 제자 파우스트 : 매 턴 시작시 최대 체력의 10%만큼 보호막 얻음
· 소지 제자 싱클레어 : 매 턴 시작시 호흡 횟수 1, 크리티컬 피해량 증가 1 얻음
대기 해제 또는 복귀할 인격이 없으면, 사망 상태인 아군 거미집 소속 인격 3명당 거미집의 검 료슈의 슬롯 수 +1 (최대 3회 증가)
이 인격은 화상, 출혈, 호흡을 부여하는 인격으로만 취급됨
특정 조건 달성 시 이번 전투 동안 전투 BGM을 변경 (일부 전투 제외)

### 6. 거미집의 검 — 시공간 잔상 분열
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger, trigger, effect, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, skill_transform, probability_random, multi_target, cross_identity
- 원문: 무작위 대상 1명에게 잔영 부여 (집중 전투인 경우, 본체로 판정)
- 사망한 아군 거미집 소속 인격 3명당, 추가로 무작위 적 1명에게 잔영 부여 (최대 3개 생성)
- 전투 시작 시 잔영이 부여된 적을 기본 공격 스킬 메인 타겟으로 지정했으면, 해당 스킬 사용 전 '필연쇄 [必然殺]'로 일방 공격함 (턴당 1회)
- 잔영을 보유한 대상에게 기본 공격 스킬 사용시,
· 해당 스킬 코인이 모두 파괴 불가 코인으로 변경되고, 최종 위력 +1
· 얽힘 1 얻음 (턴당 1회)

### 7. 거미집 약지 아비 — 신체극복
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect, trigger, effect
- 분류: action_trigger, resource_transform, skill_transform, special_state, cross_identity
- 원문: 스테이지에 첫 등장 시 조망 21 얻음

약지 소속 아군 인격이 스킬 사용 시 조망 1 감소 (인격별 턴당 1회)

턴 종료 시 자신에게 조망이 없으면, 다음 턴 시작 시 기본 스킬 하나를 ‘폐장 - 설치미술 제 1호 ‘여러분이 흩뿌린 살과 뼈가 객석이 되어’’로 변경 (전투당 1회, 가장 왼쪽 슬롯의 아래 스킬 우선 적용)
- 변경된 스킬이 다른 스킬로 변경되어 사용할 수 없게 되면, 위 효과를 다시 발동함

턴 종료 시 이번 전투에서 처음으로 흐트러졌으면, 흐트러짐 해제 (강제 흐트러짐 제외)

### 8. 거미집 검지 아비 — 신탁 단말기 [카두세우스]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, effect, effect, trigger
- 분류: action_trigger, target_selection, resource_transform, skill_transform, probability_random
- 원문: 기본 공격 스킬의 코인마다 무기가 무작위로 정해져 특수한 효과가 적용됨
- 손도끼로 갈비뼈를 찍어 내릴 때는…
- 스틸레토로 허파를 꿰뚫을 때는…
- 바스타드 소드로 어깨와 머리를 짓이길 때는…
- 레이피어로 몸에 10개 이상의 구멍을 내야할 때는…
- 망치로 뒤통수를 으깨야 할 때는…
- 커다란 검으로 몸통을 갈라야 할 때는…
- 랜스로 20인치의 구멍을 내야 할 때는…
- 채찍으로 살점을 만 갈래 떼어내야 할 때는…
- 낫으로… 누군가처럼 공간을 따라 베어내야 할 때는…

지령 표식 스킬 사용 시, 대행 [헤르메스] 1 얻음

이번 전투에서 ‘Furioso-Replica’를 처음 사용하였다면,
해당 턴 종료 시 상처를 가린 가면이 이글거리는 상처로 변경됨

턴 시작 시 이글거리는 상처를 보유 중일 때,
조작 슬롯에 ‘Furioso-Replica’가 있으면 지령 탐닉 얻음

### 9. 새벽 사무소 대표 — 새벽 사무소
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, effect, effect
- 분류: action_trigger, resource_transform, skill_transform, multi_target, cross_identity
- 원문: 스테이지 첫 등장 시 자신을 포함한 전장에 있는 새벽 사무소 소속 인격이 2명 이상이면, 모든 새벽 사무소 소속 인격에게 해당 인원 수 만큼 새벽 사무소 부여

새벽 사무소 해결사 싱클레어가 전장에 있으면, 다음 효과 발동
- 새벽 사무소 해결사 싱클레어가 새벽에서 노을로 얻음
- 새벽 사무소 대표 그레고르가 사망했으면, 턴 시작 시 새벽 사무소 해결사 싱클레어가 보유한 새벽에서 노을로가 타오르는 노을로 변경됨
- 턴 시작 시 새벽 사무소 해결사 싱클레어의 체력이 50% 미만이면, 도주 장치 부여

### 10. 홍원 군주 — 더러운 피마저 받아들이고, 누군가의 피를 묻혀가며 뜻을 이룬다.
- 상태: **partial** / 컴파일 규칙 2개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, probability_random, multi_target, special_state, cross_identity
- 원문: 전투 시작시 자신이 수비스킬을 장착하지 않고 일방공격 당할 예정이면, 원호 방어 수치가 가장 낮은 무작위 흑수 아군 (최대 공명 수 / 3)명에게 호위 1 부여. (최대 2명, 인격 당 1회. 원호 방어를 획득하는 스킬 보유 인격 제외)

이번 전투에서 체력이 0이 되는 피해를 받았을 때, 해당 피해를 받지 않고 해당 턴 동안 체력이 1로 유지되며, 오혈 1 얻음 (전투 당 1회)

자신의 오혈 1 당 스킬 피해량 +3%

E.G.O 스킬 ‘오혈읍루 - 종’ 발동 시, 공격 종료시 사망 효과가 발동하지 않고 최대 체력의 60% 회복. 다음 턴부터 매 턴 시작시마다 피해량 증가 1 얻음 (전투 당 1회)

### 11. 거미집 엄지 아비 — 예지안
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, resource_transform, skill_transform, special_state, stack_threshold
- 원문: 스테이지에 첫 등장 시 예지안 30 얻음 / 자신의 예지안 수치가 0이 되면, 예지안이 예지안 과열로 변경됨 / 예지안이 있을 때, 다음 효과 발동 - 합 진행 시 매 합마다 가속하는 미래 1 얻음 (스킬당 5회) - 일방 공격 또는 파괴 불가 코인 공격을 당하거나 공격 스킬에 합 패배 시 '예지' 스킬 발동 (턴당 1회) / 예지안은 다음 조건에 따라 수치가 감소 - 매 합마다 예지안 1 감소 - 일방 공격 또는 파괴 불가 코인 공격을 당하여, 패시브 효과로 '예지' 스킬 발동 시 예지안 3 감소 - 합 패배 시 패시브 효과로 '예지' 스킬 발동 시 예지안 5 감소 / 자신의 예지안이 예지안 과열로 변경된 턴 종료 시, 다음 효과 발동 - 재장전 (전투당 1회) - 다음 턴 시작 시 조작 슬롯에 '처분'이 없으면, 기본 스킬 하나를 '처분'으로 변경 (가장 왼쪽 슬롯의 위 스킬 우선) / 전투 중 자신의 예지안이 0이 되거나, 흐트러짐 상태가 되거나 거미집 엄지 제자 히스클리프가 사망하였으면, 다음 턴에 신(心) - 불명예 얻음 (대기 해제 시 거미집 엄지 제자 히스클리프가 사망한 상태면, 턴 시작 시 신(心) - 불명예 얻음) / 턴 종료 시 이번 턴에 처음으로 흐트러졌으면, 흐트러짐 해제 (강제 흐트러짐 제외)

### 12. LCE E.G.O:: 초롱 — E.G.O가 붕괴될 때 거름과 같이 분해되오
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 현재 체력이 가장 낮은 아군 1명이 사망 시 가장 부족한 속성의 E.G.O 자원 2종을 2개씩 얻음.

### 13. 홍원 방랑무사 — 군.가.곁.좋
(군주라… 그런 가능성에서 곁을 지켰다면 더할 나위 없이 좋았겠군.)
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, cross_identity
- 원문: 자신을 제외한 아군의 스킬이 적에게 적중하면, 해당 공격 종료시 ‘어이, 물러서라’로 일방 공격 (턴 당 1회)

대기해제 또는 복귀로 등장한 턴에 호위태세 2 얻음
홍원 군주 홍루의 ‘흑수군주’ 패시브 효과로 일방공격 명령 받을 때 흑수 또는 가씨 가문 소속으로 간주함

### 14. W사 4등급 정리 요원 - CCA — ‘언젠가 결항 열차용 정리 장비도 노려볼수있겠지’
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: - 전투 시작시 편성 순서가 가장 빠른 아군이 자신의 스킬로 충전 횟수 최대치를 초과하여 충전 횟수를 얻으면, 초과한 충전 횟수 1 당 다음 턴에 충전 역장 1 얻음 (최대 3. E.G.O 스킬 포함)

### 15. 중지 작은 형님 — 작은 형님
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect
- 분류: action_trigger, resource_transform, skill_transform, cross_identity
- 원문: 전투 시작시, 질투 공명당 원한 문신 1 얻음 (최대 7)

적이 자신을 포함한 중지 소속 아군 인격을 공격했으면, 해당 스킬 공격 종료 시 공격자를 ‘발길질’로 일방 공격함 (턴당 1회)

### 16. 남부 디에치 협회 4과 — 지식 전도
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 최대 체력이 가장 높은 아군 1명이 이번 턴 동안 받은 피해량에 비례하여 다음 턴에 타격 피해량 증가를 얻음.
(보호막으로 받은 피해도 받은 피해량에 포함됨. 턴 시작 시 체력의 15%만큼 피해를 받았을 때 최대로 획득. 최대 획득 값: 3)

### 17. 중지 작은 아우 — 중지는 잊지 않아
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, trigger
- 분류: action_trigger, resource_transform, skill_transform, cross_identity
- 원문: 자신이 적에게 피격당할 때마다, 공격자(또는 부위)에게 복수 대상 3 부여 (턴당 1회)

자신을 제외한 아군이 적에게 피격당할 때마다, 공격자(또는 부위)에게 복수 대상 2 부여 (인격 별로 턴당 1회)

기본 공격 스킬 또는 반격 스킬 공격 종료 시, 대상의 복수 대상을 전부 소모
- 적의 복수 대상을 소모할 때마다, 그 수치만큼 앙갚음 장부 [싱클레어] 얻음

### 18. 중지 작은 아우 — 중지는 잊지 않아
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger, effect, trigger
- 분류: action_trigger, resource_transform, skill_transform, cross_identity
- 원문: 자신이 적에게 피격당할 때마다, 공격자(또는 부위)에게 복수 대상 5 부여 (턴당 1회)

자신을 제외한 아군이 적에게 피격당할 때마다, 공격자(또는 부위)에게 복수 대상 2 부여 (인격 별로 턴당 1회)
- 아군이 중지 소속이면, 복수 대상 3 추가로 부여

기본 공격 스킬 또는 반격 스킬 공격 종료 시, 대상의 복수 대상을 전부 소모
- 적의 복수 대상을 소모할 때마다, 그 수치만큼 앙갚음 장부 [싱클레어] 얻음

### 19. 거미집 검지 아비 — 검지 아비
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state
- 원문: 스테이지에 첫 등장 시, 상처를 가린 가면 얻음
- 이 효과를 보유 중일 때 이번 전투에서 처음으로 흐트러지면,
턴 종료 시 흐트러짐을 해제(강제 흐트러짐 제외)하고
상처를 가린 가면이 이글거리는 상처로 변경됨

검지 대행자 - 개화 E.G.O::대행 돈키호테가 자신과 함께 전장에 있으면, 돈키호테에게 인정 욕구 충족 부여

### 20. 검지 수행자: 【쪽지】 — 쪽지로 전해진 지령
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, probability_random, special_state
- 원문: 턴 시작 시
- 자신의 지령의 가호 수치에 따라 지령[쪽지] I / 지령[쪽지] II / 지령[쪽지] III /지령[쪽지] IV 얻음
- 무작위 적 1명에게 지령 대상 부여 (집중 전투면, 부위에 부여)
- 조작 슬롯의 자신의 기본 공격 스킬에 지령 표식 부여 (슬롯당 1개, 최대 2개 부여)
· 지령의 가호가 6 이상이면, 스킬 3에 우선 부여
- 흐트러짐, 행동 불가, 패닉, E.G.O 침식 상태면, 위의 모든 효과와 지령 수행 여부가 적용되지 않음

### 21. 동부 섕크 협회 3과 — 경신법
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 화상 또는 특수 화상을 보유한 적에게 합 승리 시, 다음 턴에 신속 1을 얻음 (턴당 1회)
- 대상의 화상 위력이 20 이상이면, 신속 1을 추가로 얻음

### 22. 검지 대행자 - 개화 E.G.O:: 대행 — 단말기로 전해진 지령
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger, effect
- 분류: action_trigger, target_selection, resource_transform, probability_random, special_state
- 원문: 턴 시작 시
- 자신의 해금 단계에 따라 지령[단말기] I / 지령[단말기] II / 지령[단말기] III / 지령[단말기] IV 얻음
- 무작위 적 1명에게 지령 대상 부여 (집중 전투면, 부위에 부여)
- 조작 슬롯의 자신의 기본 공격 스킬에 지령 표식 부여 (슬롯당 1개, 최대 2개 부여)
· 해금 - II 이상이면, 스킬 3에 우선 부여
- 흐트러짐, 행동 불가, 패닉, E.G.O 침식 상태면, 위의 모든 효과와 지령 수행 여부가 적용되지 않음

턴 시작 시 해금 - III이면, 신(心) - 대행 얻음

### 23. LCCB 대리 — 돛대
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, multi_target, cross_identity
- 원문: 탄환을 가장 적게 보유한 아군 1명이 코인에서 마지막 탄환을 소모하면, 코인의 공격 종료 시, 각 대상에게 해당 코인의 공격으로 입힌 피해량의 50%만큼 추가 피해를 줌. (소수점 반올림)

### 24. LCCB 대리 — 돛대
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect
- 분류: action_trigger, target_selection, resource_transform, multi_target, cross_identity
- 원문: - 탄환을 가장 적게 보유한 아군 1명이 탄환을 소모하는 스킬을 사용할 때, 호흡 3 부여. (턴 당 1회. 탄환이 없는 대상에게는 적용되지 않음)
탄환을 가장 적게 보유한 아군 1명이 코인에서 마지막 탄환을 소모하면, 코인의 공격 종료 시, 각 대상에게 해당 코인의 공격으로 입힌 피해량의 50%만큼 추가 피해를 줌. (소수점 반올림)

### 25. W사 2등급 정리 요원 — 열차 정리 매뉴얼 전달
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 속도가 가장 느린 아군이 전투 시작 시 충전 횟수가 5 이상 있으면, 다음 턴에 신속 2를 얻음

### 26. 거미집 엄지 제자 — 필사의 분전
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, effect, effect, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state
- 원문: 거미집 엄지 아비 로쟈가 전장에 있을 경우, 다음 효과 발동
(자신이 패닉 또는 흐트러진 턴 제외)
- 거미집 엄지 아비 로쟈가 예지안이 있을 때 적에게 기본 스킬 적중 시, 해당 공격 종료 시점에 대상에게 '팔레르모 스파다'로 일방 공격 (턴당 1회)
- 전투 시작 시 거미집 엄지 아비 로쟈가 예지안 과열이 있는 상태에서 적으로부터 일방 공격으로 지정된 스킬이 있으면, 거미집 엄지 제자 히스클리프가 원호 방어 1 얻음
(이 원호 방어는 거미집 엄지 아비 로쟈를 대상으로만 발동)

### 27. 정사무소 대표 — 코이코이[こいこい]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, effect, trigger, trigger, trigger, trigger, effect, trigger, effect
- 분류: action_trigger, target_selection, resource_transform, probability_random, special_state
- 원문: 턴 시작시 광【光】이 없으면, 광【光】 위력 0, 횟수 3 얻음

턴 시작시 ‘짝패’가 없으면, 짝패 - 송학, 짝패 - 억새, 짝패 - 청벚꽃 중 자신의 가장 왼쪽 슬롯의 기본 공격 스킬에 대응되는 무작위 ‘짝패’ 얻음

전투 시작시 자신의 가장 왼쪽 슬롯에 장착한 기본 공격 스킬 또는 E.G.O 스킬이 사용될 때 아래 효과 적용 (턴당 1회)
- 다음 턴에 해당 스킬에 대응되는 ‘짝패’로 변경
- '사쿠라센' 또는 E.G.O 스킬이면, 광【光】 위력 1 얻음
- 해당 스킬 속성이 ‘짝패’와 일치하면, 아래 효과 적용
  · 광【光】 위력 1 얻음
  · 이전 턴과 연속으로 ‘짝패’가 일치했으면, 광【光】 위력 1 얻음
  · 해당 스킬 적중 시 진동 폭발. 대상의 진동 횟수 1 감소
  · 25% 확률로 해당 스킬 속성의 E.G.O 자원 1 얻음
- 해당 스킬 종료 시 광【光】 위력이 5거나, 횟수가 0이면, '코오쟌' 발동

### 28. 새벽 사무소 해결사 — 불안정한 자아의 껍질
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger, trigger, effect
- 분류: action_trigger, resource_transform, multi_target, special_state, cross_identity
- 원문: 턴 시작 시 정신력이 40 이상이면, 정신력을 20 소모하여 불안정 E.G.O::밀랍날개 상태가 됨. (이후 턴 시작 시 효과가 추가로 발동되지 않음)
또는 한 턴에 아군이 2명 이상 사망했을 때, 턴 종료 시 정신력이 -45가 아니면, 정신력을 20으로 변경한 후 불안정 E.G.O::밀랍날개 상태가 됨. (두 조건이 동시에 발생한 경우, 정신력 결과 값은 높은 쪽으로 결정됨.)

불안정 E.G.O 상태가 될 때, 피해나 흐트러짐 손상으로 흐트러짐 상태가 된 경우, 흐트러짐 상태를 해제함. 해제할 수 없는 흐트러짐 상태인 경우, 불안정 E.G.O 상태가 될 수 없음.

불안정 E.G.O 상태동안 불안정한 격정을 얻음.

턴 시작 시 정신력이 0 이하면, 불안정 E.G.O 상태가 해제됨.

### 29. 거미집 중지 아비 — 봉인된 검 [레바테인]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger, trigger, effect, effect, effect, trigger, trigger, effect, effect, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state
- 원문: 스테이지에 첫 등장 시, 봉인된 검 얻음
각 검의 단계 효과를 얻으면, 달아오르는 재미를 아래 수치에 맞게 얻음
- 봉인된 검: 1
- 1단계 봉인 해제: 2
- 2단계 봉인 해제: 2
아래 조건 만족 시 달아오르는 재미 1 감소 (턴당 1회)
- '원한 스탬핑' 사용 시 (반격으로 발동 포함)
- 질투 완전 공명 수의 합이 6 이상이면, 해당 턴 종료 시
달아오르는 재미가 0이면, 자신의 스킬 종료 시 '포장을 뜯어볼까'로 일방 공격함
- 턴 종료 시 달아오르는 재미가 0이고, 해당 턴에 '포장을 뜯어볼까'를 사용하지 못했으면, 다음 턴 전투 시작 시 해당 스킬 사용
- 자신의 검이 봉인된 검 상태일 때 자신의 체력이 80% 미만이면, 달아오르는 재미와 상관없이 해당 스킬 사용
자신의 체력이 50% 이하면, 초근성 3 얻음 (전투당 1회)
전투에서 처음으로 흐트러지면, 턴 종료 시 흐트러짐을 해제하고 중지 - 원한 15 얻음
턴 시작 시 자신의 중지 - 원한이 15면, 자신의 조작 슬롯의 기본 스킬 하나를 '원한 스탬핑' 또는 '즉결처형'으로 변경 (전투당 3회)
- 가장 왼쪽 슬롯의 아래 스킬만 적용
- 해당 슬롯에 이미 해당 스킬이 있는 경우 발동하지 않음

### 30. 흑운회 와카슈 — 흑운도
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, multi_target, cross_identity
- 원문: 자신을 포함해 전투에 참여한 아군 흑운회 소속 인격이 2명 이상이면 흑운도 1 얻음 (최대 1)

이번 턴에 수비 스킬을 사용한 적 또는 공격 시작 전에 최대 체력인 적에게 입히는 피해량 +10%

이번 턴에 적이 자신을 제외한 아군을 스킬로 공격하여 피해를 입혔으면, 공격자를 스킬 1로 일방 공격함 (턴 당 1회)

### 31. 흑운회 와카슈 — 흑운도
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger, trigger, effect
- 분류: action_trigger, resource_transform, skill_transform, multi_target, cross_identity
- 원문: 자신을 포함해 전투에 참여한 아군 흑운회 소속 인격이 2명 이상이면 흑운도 1 얻음 (최대 1)

이번 턴에 수비 스킬을 사용한 적 또는 공격 시작 전에 최대 체력인 적에게 입히는 피해량 +10%

적이 자신을 제외한 아군을 스킬로 공격하여 피해를 입혔으면, 공격자를 스킬 1로 일방 공격함 (턴 당 1회)

적이 자신을 제외한 아군을 처치했거나, 공격 종료후 공격당한 아군의 체력이 25% 미만이면, 공격자를  으로 일방 공격함 (아군 캐릭터 당 1회, 턴 당 2회. 해당 효과로 발동된 스킬은 공격 스킬로 간주함)

### 32. 약지 야수파 도슨트 — 지도 편달
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect
- 분류: action_trigger, target_selection, resource_transform, probability_random, multi_target
- 원문: 턴 시작시 (전장에 있는 스튜던트 인격 수)만큼 경의를 얻음 (전투당 1회)

턴 시작 시 무작위 약지 스튜던트 인격 2명에게 공격 레벨 증가나 방어 레벨 증가 효과를 (전장에 있는 스튜던트 인격 수)만큼 무작위로 부여 (전투당 1회, 최대 부여량 2개, 야수파 스튜던트 우선 적용)

### 33. W사 3등급 정리 요원 — 비워낸 생각
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: - 턴 종료 시 자신의 충전 횟수 5 당 다음 턴에 신속 1을 얻음. (최대 2)
- 자신이 스킬로 충전 횟수를 소모할 때, 현재 체력 비율이 가장 낮은 아군 1명에게 충전 역장 3 부여

### 34. W사 3등급 정리 요원 — 비워낸 생각
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: - 턴 종료 시 자신의 충전 횟수 5 당 다음 턴에 신속 1을 얻음. (최대 3)
- 자신이 스킬로 충전 횟수를 소모할 때, 현재 체력 비율이 가장 낮은 아군 1명에게 충전 역장 3 부여

### 35. LCE E.G.O:: 초롱 — 외형 또한 이전 L사의 E.G.O에 비해, 환상체와 가깝게 추출할 수 있소
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, resource_transform, special_state, cross_identity
- 원문: 사망 시 자신을 가장 마지막으로 공격한 대상에게 파열 4, 파열 횟수 2를 부여하고, 가장 부족한 속성의 E.G.O 자원 4종을 2개씩 얻음.
- 공격자가 없거나 아군에게 사망한 경우, 현재 파열 횟수가 가장 적은 적에게 파열 4, 파열 횟수 2 부여

### 36. LCE E.G.O:: 초롱 — 외형 또한 이전 L사의 E.G.O에 비해, 환상체와 가깝게 추출할 수 있소
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger
- 분류: action_trigger, resource_transform, special_state, cross_identity
- 원문: 사망 시 자신을 가장 마지막으로 공격한 대상에게 파열 5, 파열 횟수 3을 부여하고, 가장 부족한 속성의 E.G.O 자원 4종을 2개씩 얻음.
- 공격자가 없거나 아군에게 사망한 경우, 현재 파열 횟수가 가장 적은 적에게 파열 5, 파열 횟수 3 부여
- 자신이 미끼 요정 상태인 경우, 이 효과로 부여하는 파열 위력이 2배로 적용됨.

### 37. N사 E.G.O:: 흉탄 — 흉탄
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect
- 분류: action_trigger, resource_transform, special_state, cross_identity
- 원문: 전투 중 자신의 공격으로 아군을 사망시켰으면, 다음 턴동안 흉탄을 얻음 (자신의 E.G.O 침식 및 아군 공격 포함)
자신의 E.G.O 흉탄을 사용하여, 찢어진 추억이 소모되면, 턴 종료 시 소모한만큼 다음 턴에 찢어진 추억을 얻음

### 38. N사 E.G.O:: 흉탄 — 대상 지정
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 속도가 가장 느린 아군이 아군을 공격했다면 공격 종료 시, 다음 턴에 피해량 증가를 1 얻음 (턴 당 최대 2)
- 이 때, 아군이 사망했으면, 위 효과를 대신하여 이번 전투 동안 피해량 증가를 1 얻음 (스테이지 및 인격당 최대 2)
- 위 효과들로 얻는 피해량 증가는 최대 2까지만 얻어짐.

### 39. 흑수 - 오 필두 — 구마지심 [狗馬之心]
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger, effect, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, skill_transform, special_state, stack_threshold
- 원문: 홍원 군주 홍루와 존명 발동 시, 홍원 군주 홍루가 흑수환염[黑獣丸染]으로 아래 효과 얻음
- 기본 스킬의 마지막 코인 적중 시, 진동 폭발 1회 (턴 당 1회)

전투 인원에 가주 후보 이스마엘이 있다면, 아래 효과 적용
- 가주 후보 이스마엘이 스킬 효과로 파열 또는 파열 횟수 부여 시 호흡 위력 3 얻음 (턴 당 2회, E.G.O 스킬에는 적용되지 않음)
- 턴 시작 시 가주 후보 이스마엘에게 공격 위력 증가 1 부여. 이스마엘의 호흡 위력이 10 이상이면, 공격 위력 증가 1 추가 부여
- ‘흑풍마각월참’ 사용 후 가주 후보 이스마엘이 적춘 스킬로 원호 공격함 (턴 당 1회)

### 40. 멀티크랙 사무소 대표 — 전류 해체
- 상태: **partial** / 컴파일 규칙 3개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, multi_target, stack_threshold, cross_identity
- 원문: 전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다, 충전 1 얻음
충전이 2 이상이면, 피해량이 (충전 x 3)%만큼 증가 (최대 15%)
- 대상의 체력이 50% 미만이면 (충전 x 5)%만큼 추가로 증가 (최대 25%)

적을 처치하면 자신과 충전 횟수가 가장 적은 아군 2명이 (2 + 충전)만큼 충전 횟수 증가 (최대 5, 충전을 소모하거나 스스로 획득하는 스킬을 보유한 아군에게 우선으로 적용됨)

### 41. 동부 섕크 협회 3과 — 경신법
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 화상 또는 특수 화상을 보유한 적에게 합 승리 시, 다음 턴에 신속 1을 얻음 (턴당 1회)

### 42. 료. 고. 파. 주방장 — 즉흥 조리
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 적 처치 시 체력이 가장 낮은 아군 1명의 체력 15 회복 (턴 당 1회 발동).
갈증 이 있는 경우 전부 소모하고, 소모한 갈증 에 비례하여 체력 회복량 증가.

### 43. 서부 섕크 협회 3과 — 한 발 더 빠르게
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 합 승리시 다음 턴에 신속 1을 얻음(턴 당 최대 2회)

### 44. 남부 섕크 협회 4과 부장 — 느리시네요
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 회피 성공 시 다음 턴에 신속 1을 얻음 (최대 5회)

### 45. 중지 작은 아우 — 빽
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 전투 시작 시, 현재 체력 비율이 가장 낮은 아군 1명이 방어 레벨 증가 2 얻음

### 46. LCE E.G.O:: AEDD — 제세동
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 편성 순서가 제일 빠른 아군 둘이 턴 종료 시 이번 턴에 각자의 공격 스킬을 사용하여 소모한 충전 횟수와 소모한 특수 충전의 합만큼 각자의 체력을 회복 (최대 10)

### 47. LCE E.G.O:: AEDD — 제세동
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 편성 순서가 제일 빠른 아군 셋이 턴 종료 시 이번 턴에 각자의 공격 스킬을 사용하여 소모한 충전 횟수와 소모한 특수 충전의 합만큼 각자의 체력을 회복 (최대 10)

### 48. 로보토미 E.G.O:: 엄숙한 애도 — 죽어가는나비를본다.
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, probability_random
- 원문: 전투 시작 시 산나비·죽은나비를 각각 10씩 보유함.

 산나비·죽은나비를 소모할 때, 해당 효과의 산나비(위력)와 죽은나비(횟수)를 무작위로 소모.

나비를 부여할 때, 해당 코인에서 소모한 산나비·죽은나비에 따라 부여.
- 산나비를 소모했으면, 소모한 값만큼 산나비를 부여.
- 죽은나비를 소모했으면, 소모한 값만큼 죽은나비를 부여.

스킬 사용 중 산나비·죽은나비가 부족하면, 다음 코인을 모두 취소하고 재장전

재장전을 하거나 산나비·죽은나비를 얻을 때, 현재 정신력에 따라 얻는 나비가 정해짐.
- 정신력이 0 이상이면, 30% 확률로 산나비를, 70% 확률로 죽은나비를 얻음.
- 정신력이 0 미만이면, 70% 확률로 산나비를, 30% 확률로 죽은나비를 얻음.
- 확률은 각 탄환마다 개별적으로 적용됨.

### 49. 새벽 사무소 해결사 — 선배
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, effect
- 분류: action_trigger, resource_transform, skill_transform
- 원문: 새벽 사무소 해결사 싱클레어가 전장에 있으면, 다음 효과 발동
- 새벽 사무소 해결사 싱클레어가 정오 얻음
- 새벽 사무소 해결사 파우스트가 사망했으면, 턴 시작 시 새벽 사무소 해결사 싱클레어가 보유한 정오가 고독한 정오로 변경됨

### 50. 라만차랜드 실장 — 아류 산초 경혈식
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, stack_threshold, cross_identity
- 원문: 턴 시작 시, 경혈 15 이상이고 다음의 인격이 전투에 참가 중이거나 사망했으면, 자신의 가장 왼쪽 슬롯의 스킬이 강화됨.
- 라만차랜드 신부 그레고르: 스킬 1 강화
- 라만차랜드 이발사 오티스: 스킬 2 강화
- 자신: 스킬 3 강화
- 라만차랜드 공주 로쟈: 수비 스킬 강화

자신을 제외한 아군이 출혈 피해를 받거나 혈찬을 소모할 때, 경혈 2 얻음 (턴 당 3회)

### 51. 라만차랜드 실장 — 혈족을 책임지게 된 자
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, effect
- 분류: action_trigger, resource_transform, multi_target, cross_identity
- 원문: 전투 동안 자신을 제외한 아군 중  소속이 사망한 경우
- 자신의 기본 공격 스킬로 경혈을 얻을 때, 경혈을 1 추가로 얻음
- 자신을 제외한 아군 중  소속이 3명 이상 사망한 경우, 대신 경혈 3을 추가로 얻고 턴 시작 시, 책임감 1 얻음

### 52. 거미집의 검 — 지혜성 [地慧星]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, effect
- 분류: action_trigger, target_selection, resource_transform, probability_random
- 원문: 자신의 지혜성도가 50 이상이면, 해당 턴의 마지막 순서에 무작위 적에게 '공간참 - 연 [空間斬 - 緣]' 발동 (전투당 1회)
- 이 효과로 '공간참 - 연 [空間斬 - 緣]'을 사용한 후, 아래 효과 적용
· 이번 전투 동안 퇴각 불가
· 턴 종료시 자신의 지혜성도가 50 이상이면, 다음 턴 시작시 기본 스킬 하나를 '공간참 - 잔 [空間斬 - 殘]'으로 변경 (가장 왼쪽 슬롯의 아래 스킬 우선 적용)

### 53. 홍원 군주 — 흑수군주
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect, effect, effect, trigger
- 분류: action_trigger, target_selection, resource_transform, probability_random, cross_identity
- 원문: 자신을 제외한 아군 인격이 대기해제 또는 복귀했으면, 정신력을 10 회복하고, 전투 시작시 스킬 1로 무작위 대상에게 일방공격 명령
- 해당 아군이 흑수 또는 가씨 가문 소속이면 대신 정신력을 20 회복하고, 전투 시작시 기본 스킬 3으로 무작위 대상에게 일방공격 명령 (인격 당 전투 당 2회)

스테이지 시작 시, 대기 인원을 포함하여 편성된 흑수 인격 1명 당 모든 흑수의 주인 1 얻음

전투에서 흑수 인격이 사망 시, 정신력을 20 회복하고, 사중구활[死中求活] 버프 1 얻음
(자신이 퇴각 상태여도 적용)
흑수환염[黑獣丸染] 1 당 피해량 +5% (최대 55%)

### 54. 마침표 사무소 해결사 — 정밀 조준
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 턴 종료시 자신의 호흡 10 당, 다음 턴에 신속 1 얻음 (최대 2)

전투 시작시 자신이 (E.G.O 스킬 포함) 공격 스킬을 사용할 예정이 아니면, 호흡 위력이 가장 낮은 아군 1명에게 호흡 3 부여

턴 종료 시 이번 턴에 자신이 (E.G.O 스킬 포함, 타겟 포착 제외) 공격 스킬을 사용하지 않았으면, 다음 턴에 호흡 10, 관통 위력 증가 1 얻음

### 55. 흑운회 부조장 — 몰려드는 검은 구름
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect
- 분류: action_trigger, resource_transform, multi_target, cross_identity
- 원문: 전투 시작시 자신을 포함해 전투에 참여한 아군 흑운회 소속 인격이 2명 이상이면, 흑운도 1 얻음

전투 시작시 조작 패널에서 자신의 양 옆의 흑운회 소속 인격에게 검은 구름 1 부여

### 56. 흑운회 부조장 — 몰려드는 검은 구름
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger
- 분류: action_trigger, resource_transform, multi_target, cross_identity
- 원문: 전투 시작시 자신을 포함해 전투에 참여한 아군 흑운회 소속 인격이 2명 이상이면, 흑운도 1 얻음

전투 시작시 조작 패널에서 자신의 양 옆의 흑운회 소속 인격에게 검은 구름 1 부여
- 색욕 공명이 4 이상이면, 자신을 제외한 모든 흑운회 소속 아군에게 검은 구름 1 부여

### 57. 북부 제뱌찌 협회 3과 — 신속 배달
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 턴 시작 시 속도가 6 이상이거나 신속을 보유하였다면, 자신의 최대 체력의 (딜리버리 캐리어 - 로쟈/2)%만큼 보호막을 얻음 (최대 15%)

퇴각 시, 다음 턴에 아군 둘에게 합 위력 증가 1 부여 (대기 해제된 인격에게 우선으로 부여되며, 그 다음으로는 편성 순서가 빠른 순으로 적용)

### 58. 북부 제뱌찌 협회 3과 — 신속 배달
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 턴 시작 시 속도가 6 이상이거나 신속을 보유하였다면, 자신의 최대 체력의 (딜리버리 캐리어 - 로쟈)%만큼 보호막을 얻음 (최대 20%)

퇴각 시, 다음 턴에 아군 둘에게 합 위력 증가 1 부여 (대기 해제된 인격에게 우선으로 부여되며, 그 다음으로는 편성 순서가 빠른 순으로 적용)
- 자신이 보유한 딜리버리 캐리어 - 로쟈 15당 유지 턴 수 1 증가 (최대 2턴 증가)

### 59. 북부 제뱌찌 협회 3과 — 잠시만 부탁드려요...
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 턴 시작시 속도가 6 이상이거나 신속을 보유하였다면, 자신의 최대 체력의 (딜리버리 캐리어 - 싱클레어)%만큼 보호막을 얻음 (최대 20%)
퇴각 시, 다음 턴에 아군 둘에게 합 위력 증가 1 부여 (대기 해제된 인격에게 우선으로 부여되며, 그 다음으로는 편성 순서가 빠른 순으로 적용)
- 딜리버리 캐리어 - 싱클레어 15당 유지 턴 수 1 증가 (최대 2턴 증가)

### 60. 거미집 중지 아비 — 자식 교육
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, effect, trigger, effect, effect
- 분류: action_trigger, resource_transform, skill_transform
- 원문: 거미집 중지 제자 이스마엘이 자신과 함께 전장에 있으면, 아래 효과 발동
- 자신의 합 승리 시 잘 봐뒀라 딸! 1 얻음 (턴당 1회, 해당 턴에 자신이 처음 사용한 스킬이면, 추가로 1 얻음)
- 자신의 스킬 적중 시 잘 봐뒀라 딸! 1 얻음 (턴당 1회, 파괴된 코인이면, 얻지 않음)
[거미집 중지 제자 이스마엘 전용 효과]
- 이스마엘이 합 승리 시 칭찬 받았다! 1 얻음 (턴당 1회, 해당 턴에 이스마엘이 처음 사용한 스킬이면, 추가로 1 얻음)
- 이스마엘이 스킬 적중 시 칭찬 받았다! 1 얻음 (턴당 1회, 해당 스킬이 반격으로 사용한 스킬 3이면, 칭찬 받았다! 추가로 1 얻음.)

### 61. 불주먹 사무소 생존자 — 나만 살아남아버렸어...
- 상태: **partial** / 컴파일 규칙 3개
- 미지원: trigger
- 분류: action_trigger, target_selection, resource_transform, probability_random, multi_target, stack_threshold
- 원문: 자신이 이번 전투에서 소모한 12구산 연료, 과열 연료당 피해량 +0.2% (최대 40%)
- 메인 타겟이 , 거나, 대상의 화상과 화상 횟수의 합이 30 이상이면, 대신 피해량 +0.3% (최대 60%)

12구산 연료, 과열 연료가 1 이상일 때, 화상이 부여된 적을 흐트러짐 상태로 만들거나 처치하면 화상이 없거나 화상 횟수가 가장 낮은 무작위 적 2명의 화상 횟수 2 증가 (턴 당 1 회)
- 집중 전투인 경우 부위에 부여

### 62. 로보토미 E.G.O:: 램프 — 등불과 같은 눈
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 전투 시작 시 램프 1 얻음

전투 시작 시 현혹이 부여된 적이 있으면, 정신력 3 회복

턴 종료 시 아래 조건에 포함되지 않은 아군 중 편성 순서가 가장 빠른 아군에게 다음 턴에 숲의 파수꾼 부여
- 자기 자신
- 숲의 파수꾼을 보유한 아군
- 패닉/침식 등의 정신력 회복이 불가능한 아군

### 63. 로보토미 E.G.O:: 램프 — E.G.O 장비 숙련 매뉴얼
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 턴 시작 시 E.G.O 장비를 착용한 아군 1명당, 방어 레벨 증가 1 얻음 (최대 3)

아군 사망 시 다음 턴에 관통 피해량 증가 2 얻음 (턴당 1회)

### 64. 로보토미 E.G.O:: 램프 — 등불과 같은 눈
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, special_state, cross_identity
- 원문: 전투 시작 시 우울 공명 2당, 램프 1 얻음 (최대 3)

전투 시작 시 현혹이 부여된 적이 있으면, 정신력 5 회복

턴 종료 시 아래 조건에 포함되지 않은 아군 중 편성 순서가 가장 빠른 아군에게 다음 턴에 숲의 파수꾼 부여
- 자기 자신
- 숲의 파수꾼을 보유한 아군
- 패닉/침식 등의 정신력 회복이 불가능한 아군

### 65. 남부 디에치 협회 4과 — 반복 지식
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger
- 분류: target_selection, resource_transform, special_state, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 스킬을 버릴 때, 해당 캐릭터 최대 체력의 (3 x 버린 스킬의 등급) % 만큼 보호막을 얻음 (턴 당 최대 1회)

### 66. 남부 디에치 협회 4과 — 반복 지식
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger
- 분류: target_selection, resource_transform, special_state, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 스킬을 버릴 때, 해당 캐릭터 최대 체력의 (5 x 버린 스킬의 등급) % 만큼 보호막을 얻음 (턴 당 최대 2회)

### 67. LCB 수감자 — 관찰
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, probability_random, cross_identity
- 원문: 최대 체력이 가장 높은 아군 1명 공격 적중 시 25% 확률로 공격 레벨 감소 2 부여

### 68. 멀티크랙 사무소 대표 — 전류 해체
- 상태: **partial** / 컴파일 규칙 2개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다, 충전 1 얻음
충전이 2 이상이면, 피해량이 (충전 x 3)%만큼 증가 (최대 15%)

적을 처치하면 자신과 충전 횟수가 가장 적은 아군 1명이 충전만큼 충전 횟수 증가 (최대 3, 충전을 소모하거나 스스로 획득하는 스킬을 보유한 아군에게 우선으로 적용됨)

### 69. 검지 대행자 - 개화 E.G.O:: 대행 — 해금/개화 E.G.O::대행
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger, effect, trigger, trigger, trigger, trigger, trigger, effect
- 분류: action_trigger, resource_transform, special_state, stack_threshold
- 원문: 턴 종료 시 지령의 가호가 3/6/9이면, 해금 - I/해금 - II/해금 - III 얻음

해금 - I을 얻으면, 정신력을 15 소모하여 개화 E.G.O::대행 상태가 됨
- 정신력 소모 전 정신력이 25까지 증가하고 (증가한 정신력/5)만큼 카르마 얻음 (소수점 올림)
- 이후 턴 시작 시 해금이 있고, 정신력이 25 이상이면,
정신력을 15 소모하여 해당 상태가 됨

개화 E.G.O::대행 상태가 될 때,
- 해당 턴의 흐트러짐 해제
(해제할 수 없는 흐트러짐이면 해당 상태가 될 수 없음)
- 해당 상태일 때, 당연한 믿음 얻음

턴 시작 시 정신력이 0 이하면, 해당 상태 해제

### 70. 남부 디에치 협회 4과 부장 — 성실한 배움
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger
- 분류: target_selection, resource_transform, special_state, cross_identity
- 원문: 최대 체력이 가장 높은 아군 1명이 스킬을 버릴 때, 해당 인격 최대 체력의 (5 x 버린 스킬의 등급)% 만큼 보호막을 얻음 (턴 당 1회)
탐구한 지식이 있는 경우, 보호막 수치가 1.5배로 적용됨

### 71. 동부 엄지 솔다토II — 탄환 상납
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, trigger
- 분류: target_selection, resource_transform, probability_random, cross_identity
- 원문: 탄환을 쓰는 인격 중 편성 순서가 가장 빠른 아군 1명의 공격이 종료 되었을 때, 해당 인격의 현재 보유 탄환이 절반 미만이면 (소수점 올림), 해당 인격이 소모한 탄환 수 만큼 자신의 작열 추진탄을 소모하고, 작열 추진탄을 소모한 만큼 해당 인격이 사용하는 탄환을 보급함. (최대 소모 값: 3개) (전투당 1회)

- 탄환을 보급 받는 인격이 자신보다 계급이 높은 엄지 소속 인격이면, 해당 인격이 사용하는 탄환을 1개 더 보급함
- 위력, 횟수가 분리된 탄환은 위력, 횟수를 무작위로 보급함
- 만약 위력 또는 횟수가 최댓값인 경우, 최댓값이 아닌 쪽의 탄환으로 보급함

### 72. 동부 엄지 솔다토II — 탄환 상납
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, trigger
- 분류: target_selection, resource_transform, probability_random, cross_identity
- 원문: 탄환을 쓰는 인격 중 편성 순서가 가장 빠른 아군 1명의 공격이 종료 되었을 때, 해당 인격의 현재 보유 탄환이 절반 미만이면 (소수점 올림), 해당 인격이 소모한 탄환 수 만큼 자신의 작열 추진탄을 소모하고, 작열 추진탄을 소모한 만큼 해당 인격이 사용하는 탄환을 보급함. (최대 소모 값: 5개) (전투당 1회)

- 탄환을 보급 받는 인격이 자신보다 계급이 높은 엄지 소속 인격이면, 해당 인격이 사용하는 탄환을 1개 더 보급함
- 위력, 횟수가 분리된 탄환은 위력, 횟수를 무작위로 보급함
- 만약 위력 또는 횟수가 최댓값인 경우, 최댓값이 아닌 쪽의 탄환으로 보급함

### 73. 동부 엄지 솔다토II — 재장전
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, trigger, trigger
- 분류: target_selection, resource_transform, probability_random, cross_identity
- 원문: 탄환을 쓰는 인격 중 편성 순서가 가장 빠른 아군 1명의 공격이 종료 되었을 때, 해당 인격의 현재 보유 탄환이 절반 미만이면, 탄환을 최대치의 절반만큼 다시 얻음 (소수점 올림, 전투당 1회, 최대 탄환 획득 값 : 5)

- 위력, 횟수가 분리된 탄환은 위력, 횟수를 무작위로 얻음
- 만약 위력 또는 횟수가 최댓값인 경우, 최댓값이 아닌 쪽의 탄환으로 얻음
- 탄환을 사용하는 인격이 없으면, 이 효과는 발동하지 않음

### 74. W사 3등급 정리 요원 팀장 — 과충전 / 정리 지시
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger
- 분류: action_trigger, target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다 충전을 1 얻음
턴 종료 시, 자신을 포함한 W사 직원 (충전)명에게 편성 순서가 가장 뒤인 순으로 다음 턴에 합 위력 증가 1 부여 (최대 부여 대상 수: 5명)

### 75. LCE E.G.O:: AEDD — 앞으로 나서게. 지원하도록 하지.
- 상태: **partial** / 컴파일 규칙 4개
- 미지원: trigger, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, multi_target, cross_identity
- 원문: 전투 시작 시, 자신의 충전 횟수 10 증가 (전투당 1회)

전투 종료 시 자신의 충전 횟수가 12를 초과하면,
초과한 충전 횟수를 최대 8까지 소모하고 이 효과로 소모한 수치의 절반만큼 아군 1명의 충전 횟수 증가 (소수점 올림)
- 자신보다 편성 순서가 빠른 아군 중 충전 횟수가 낮은 아군에게 우선 적용
- 전장에 자신보다 편성 순서가 빠른 아군이 없거나 자신의 충전이 3 이상이면, 이 효과가 비활성화

우울 또는 질투 공명이 2 이상이면,
다음 턴에 자신보다 편성 순서가 빠른 아군의 충전 횟수 2 증가
- 편성 순으로 (우울, 질투 중 높은 공명 수-1)명에게 효과 적용 (최대 3명)
- 자신의 충전이 3 이상이면, 대신 아군의 충전 횟수 4 증가
- 전장에 자신보다 편성 순서가 빠른 아군이 없으면, 대신 자신의 충전 횟수 4 증가

### 76. LCE E.G.O:: AEDD — 앞으로 나서게. 지원하도록 하지.
- 상태: **partial** / 컴파일 규칙 4개
- 미지원: trigger, trigger, trigger, trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, multi_target, cross_identity
- 원문: 전투 시작 시, 자신의 충전 횟수 5 증가 (전투당 1회)

전투 종료 시 자신의 충전 횟수가 12를 초과하면,
초과한 충전 횟수를 최대 8까지 소모하고 이 효과로 소모한 수치의 절반만큼 아군 1명의 충전 횟수 증가 (아군 충전 횟수 최소 1 증가, 소수점 버림)
- 자신보다 편성 순서가 빠른 아군 중 충전 횟수가 낮은 아군에게 우선 적용
- 전장에 자신보다 편성 순서가 빠른 아군이 없거나 자신의 충전이 3 이상이면, 이 효과가 비활성화

우울 또는 질투 공명이 3 이상이면,
다음 턴에 자신보다 편성 순서가 빠른 아군의 충전 횟수 2 증가
- 편성 순으로 (우울, 질투 중 높은 공명 수-2)명에게 효과 적용 (최대 3명)
- 자신의 충전이 3 이상이면, 대신 아군의 충전 횟수 4 증가
- 전장에 자신보다 편성 순서가 빠른 아군이 없으면, 대신 자신의 충전 횟수 4 증가

### 77. 로보토미 E.G.O:: 엄숙한 애도 — 구원의 손
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 아군의 스킬 적중 시 대상의 침잠을 2 소모하여 나비 1 부여 (턴 당 3회)

### 78. LCE E.G.O::차원찢개 — 뚫린 골목
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 전투 중 누적으로 자신의 충전 횟수 10 소모할 때마다 충전 위력 1 얻음
자신을 제외한 아군의 스킬이 적에게 적중하면, 해당 공격 종료시 차원 표류를 1 소모하여 대상에게 '차원 베기'를 발동한 후, 사색 차원 1 얻음

### 79. 새벽 사무소 해결사 — 포이어팔터 [스티그마 공방]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect, effect, effect, trigger
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신에게 전투 감각이 있을 때 전투 시작 시 (수치x3)만큼 불꽃나비의 관 얻음

자신 이외의 새벽 사무소 소속 인격이 다음 조건 만족 시, 새벽 사무소 해결사 파우스트가 '연계' 사용 (인격별 턴당 1회)
- 기본 스킬 공격 종료 시 적중한 적이 흐트러졌을 때, 대상에게 사용 (해당 스킬 공격 시작 전 이미 흐트러짐 상태였으면, 발동하지 않음)
- 새벽 사무소 대표 그레고르의 '새벽을 가르는 검', '새벽녘' 또는 새벽 사무소 해결사 싱클레어의 '낙인', '타오르는 일격' 공격 종료 시, 적중한 적에게 사용 (흐트러진 대상 우선)

새벽 사무소 해결사 싱클레어가 전장에 있으면, 새벽 사무소 해결사 파우스트가 사용하는 기본 스킬의 재사용 코인 적중 시 대상 적의 화상 위력만큼 분노 피해를 추가로 입힘 (최대 10, 턴당 최대 20)
- 화상이 발동한 것으로 취급

### 80. 홍원 방랑무사 — 협객
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, skill_transform, cross_identity
- 원문: 적이 아군을 공격하여 해당 아군이 사망했거나 체력이 25% 미만이면, 해당 공격 종료시 홍원 방랑무사 료슈가 ‘가척아원’으로 해당 적 일방 공격 (전투 당 1회)
- 홍원 군주 홍루는 횟수 제한을 초과하여 이 효과 1회 추가 발동 가능

‘군.가.곁.좋’ 패시브 효과로 ‘어이, 물러서라’ 발동 시, 해당 스킬 크리티컬 피해량 +30%. 자신을 제외한 정신력이 가장 낮은 아군 1명의 정신력 2 ~ 4 회복 (턴 당 1회. 정신력이 -40 이하인 아군 제외)

### 81. 로보토미 E.G.O:: 잔향・외로움 — 채워지지 않는 공허
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 상시 적용 : 탄환 - 고독 6개 보유

탄환 - 고독이 1 이상일 때, 자신 또는 아군의 공격 종료시 적의 정신력이
-40미만이거나 흐트러짐 상태면 '탕. 탕.'으로 일방공격 (턴당 1회)

자신의 공격 종료시 탄환 - 고독이 0이면, 대상을 '멈추지 않는 이야기'로 일방공격하고 정신력을 10 소모하여 재장전

### 82. 남부 디에치 협회 4과 부장 — 자율 학습 지시
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신을 제외한 아군이 스킬을 버릴 때마다 대상과 자신에게 지식 단련 1을 부여 (스킬 당 1회, 턴 당 3회)
턴 종료 시, 자신을 제외하고 스킬을 버린 아군의 수만큼 다음 턴에 관통 피해량 증가, 타격 피해량 증가 얻음 (최대 3)

### 83. 동부 엄지 카포IIII — 맹호의 도약
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger
- 분류: target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 탄환을 소모하는 스킬 사용 시 대상보다 속도가 3 이상 높다면, 가하는 피해량 +(대상과의 속도 차이 x 2)% (최대 10%)
(탄환이 없으면 적용되지 않음. 단, 탄환 버프는 보유하였으나 수치가 0인 경우에는 효과가 적용됨)

### 84. 동부 엄지 카포IIII — 맹호의 도약
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger
- 분류: target_selection, resource_transform, stack_threshold, cross_identity
- 원문: 속도가 가장 빠른 아군 1명이 탄환을 소모하는 스킬 사용 시 대상보다 속도가 3 이상 높다면, 가하는 피해량 +(대상과의 속도 차이 x 3)% (최대 15%)
(탄환이 없으면 적용되지 않음. 단, 탄환 버프는 보유하였으나 수치가 0인 경우에는 효과가 적용됨)

### 85. N사 작은 망치 — 젠장...
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 아군이 사망하면 다음 턴 시작 시 정신력이 10 감소하고, 타격 위력 증가 1을 얻음

### 86. 중지 작은 형님 — 앙갚음 장부
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신 또는 중지 소속의 아군 인격이 적에게 피격 시, 대상에게 복수 대상을 1 부여하고 앙갚음 장부 [히스클리프] 1 얻음 (스킬당 1회)
아군 인격 사망시, 앙갚음 장부 [히스클리프] 3 얻음

### 87. 중지 작은 형님 — 원한 문신 공명
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger
- 분류: action_trigger, skill_transform, special_state, cross_identity
- 원문: 전투 시작시 수비 스킬을 장착한 중지 소속 아군 인격이 이번 턴 동안 일방공격으로 받는 피해량 -20%

전투 시작시 질투 공명 4 이상이면, 조작 패널에서 자신의 양 옆의 중지 소속 아군 인격이 사용할 수 있는 반격 스킬이 있는 동안 피해로 인해 흐트러짐 상태가 되지 않음 (강제 흐트러짐 제외)
- 질투 공명 6 이상이면, 모든 중지 소속 아군 인격에게 적용됨

### 88. 거미집 중지 제자 — 중지는 잊지 않는다구요
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, trigger, effect, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 턴 종료시 해당 턴에 아군에게 스킬로 가장 많이 피해를 준 적 1명에게 앙갚음 대상을 부여

자신이 적에게 피격당할 때마다, 중지 - 원한 2 얻음 (턴당 2회)
자신을 제외한 중지 소속 아군이 적에게 피격당할 때마다, 중지 - 원한 1 얻음 (인격 별로 턴당 1회)

자신이 중지 - 원한을 5 소모할 때마다 중지식 강화 문신 1 얻음 (턴당 2회)

전투 시작시 자신에게 열선이 없으면, 질투 공명 수의 합이 3 이상일 때, 다음 턴에 열선 2 얻음
전투 시작시 자신에게 열선이 있으면, 턴 종료시 (질투 공명 수 / 3)만큼 열선 얻음 (최대 2)

### 89. 거미집 중지 제자 — 중지는 잊지 않는다구요
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, trigger, effect, trigger, effect, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 턴 종료시 해당 턴에 아군에게 스킬로 가장 많이 피해를 준 적 1명에게 앙갚음 대상을 부여

자신이 적에게 피격당할 때마다, 중지 - 원한 2 얻음 (턴당 2회)
자신을 제외한 중지 소속 아군이 적에게 피격당할 때마다, 중지 - 원한 1 얻음 (인격 별로 턴당 1회)
- 자신이나 아군을 공격한 대상이 앙갚음 대상이면, 추가로 1 얻음
- 전투 시작시 질투 완전 공명이 있으면, 이번 턴에 중지 - 원한을 2배로 얻음

자신이 중지 - 원한을 5 소모할 때마다 중지식 강화 문신 1 얻음 (턴당 2회)

전투 시작시 자신에게 열선이 없으면, 질투 공명 수의 합이 3 이상일 때, 다음 턴에 열선 2 얻음
전투 시작시 자신에게 열선이 있으면, 턴 종료시 (질투 공명 수 / 3)만큼 열선 얻음 (최대 2)

### 90. LCD 현장추리팀 — 림버스 컴퍼니 제작 특수 의체 시제품 mk5 - 도깨비팔
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 전투 시작 시 도깨비팔을 얻으며, 자신을 제외한 검계 소속 아군 인격의 정신력을 (오만 공명 수)만큼 회복
전투 시작 시 자신을 제외한 현재 체력이 최대 체력의 50% 미만인 아군이 있으면, 원호 방어 1 얻음 (턴당 1회)
스킬 종료시 자신의 호흡 위력 3당, 묵 공방 - 예[銳] 2식 발도 / 추력:도깨비불 1 얻음 (최대 5, 턴당 2회)

### 91. 거미집 중지 아비 — 앙갚음 장부 - 거미집 특별 조항
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, trigger, effect, effect, trigger, effect, effect, trigger, trigger, trigger, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 턴 종료 시 해당 턴에 아군에게 스킬로 가장 많이 피해를 준 적 1명에게 앙갚음 대상을 부여
턴 종료 시 해당 턴에 자신에게 스킬로 가장 많이 피해를 준 적 1명에게 앙갚음 장부 [거미집]을 부여
전투 시작 시 질투 공명 1당 중지 - 원한 1 얻음 (최대 7)
전투 중 아래 조건을 만족 시 중지 - 원한 2 얻음
- 자신이 다른 캐릭터의 스킬로 피격 시 (턴당 2회)
- 거미집 중지 제자 이스마엘이 다른 캐릭터의 스킬로 피격 시 (턴당 1회)
전투 중 아래 조건을 만족 시 중지 - 원한 1 얻음 (자신과 중지 제자 이스마엘은 대상에서 제외)
- 중지 소속 아군이 다른 캐릭터의 스킬로 피격 시 (인격별 턴당 1회)
- 거미집 소속 아군이 다른 캐릭터의 스킬로 피격 시 (인격별 턴당 1회)
자신이 중지 - 원한을 얻을 때 대상이 앙갚음 대상이면, 추가로 1 얻음
자신이 중지 - 원한을 5 소모할 때마다 중지 - 원한 문신 [큰 누님] 1 얻음
[거미집 중지 제자 이스마엘 전용 효과]
거미집 중지 아비 오티스가 다른 캐릭터의 스킬로 피격 시, 이스마엘이 중지 - 원한 2 얻음 (턴당 1회)

### 92. 흑운회 부조장 — 흑운검법
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, stack_threshold, cross_identity
- 원문: 속도가 가장 느린 아군 1명이 출혈이 10 이상 부여된 적에게 공격 적중 시 다음 턴에 공격 레벨 감소 1 부여 (턴 당 3회)

### 93. 밤의 송곳 카피타노 — 패밀리의 숙청인
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신이 적 처치 또는 부위 파괴 시, 다음 턴에 관통 위력 증가 1 얻음 (턴당 1회)

기본 공격 스킬 사용 시 대상의 속도가 자신보다 느리면 속도 차이 2당, 대상에게 수비 위력 감소 1 부여 (턴당 최대 1)

아군이 적에게 기본 공격 스킬 종료 시 적(본체)의 체력이 20% 이하인 경우, 대상에게 ‘메르체’ 사용 (턴당 1회)

### 94. 밤의 송곳 카피타노 — 패밀리의 숙청인
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect, effect
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신이 적 처치 또는 부위 파괴 시, 다음 턴에 관통 위력 증가 2 얻음 (턴당 1회)

기본 공격 스킬 사용 시 대상의 속도가 자신보다 느리면 속도 차이 2당, 대상에게 수비 위력 감소 1 부여 (턴당 최대 2)

아군이 적에게 기본 공격 스킬 종료 시 적(본체)의 체력이 20% 이하인 경우, 대상에게 ‘메르체’ 사용 (턴당 1회)
- 공격 종료 시 생존한 적이 1명이면, 대상이 흐트러짐 상태일 때에도 발동

### 95. 새벽 사무소 대표 — 모르겐포이어 [스티그마 공방]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, effect, effect, effect, trigger
- 분류: action_trigger, resource_transform, cross_identity
- 원문: 자신에게 새벽맞이가 있을 때 기본 공격 스킬 적중시 새벽불 2 얻음

자신 이외의 새벽 사무소 소속 인격이 다음 조건 만족 시, 새벽 사무소 대표 그레고르가 대상 적에게 '여명의 섬광' 사용
- 기본 스킬 공격 종료 시 적중한 적이 흐트러졌을 때, 대상에게 사용 (해당 스킬 공격 시작 전 이미 흐트러짐 상태였으면, 발동하지 않음)
- 새벽 사무소 해결사 파우스트의 '사출', '사출-정오', '정오의 해체' 또는 새벽 사무소 해결사 싱클레어의 '낙인', '타오르는 일격' 공격 종료 시, 적중한 적에게 사용 (흐트러진 대상 우선)

새벽 사무소 해결사 싱클레어가 전장에 있으면, 새벽 사무소 대표 그레고르가 사용하는 기본 스킬의 추가된 코인 적중 시 대상 적의 화상 위력만큼 분노 피해를 추가로 입힘 (최대 10, 턴당 최대 20)
- 화상이 발동된 것으로 취급

### 96. 흑수 - 오 필두 — 흑풍마각 [黑風馬脚]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, trigger, effect, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 아래의 조건 만족 시 적진 주파 1 얻음
- 공격 시작 시 대상보다 속도가 2 이상 높을 때
- 자신의 스킬로 진동 폭발 효과 2회 발동시 (E.G.O 스킬 포함)
- 각력【오】를 보유 중인 상태로 합 승리 시
※ 적진 주파는 턴 당 최대 3까지 얻을 수 있으며, ‘흑풍마각월참’ 스킬로는 얻을 수 없음

### 97. 흑수 - 오 필두 — 흑풍마각 [黑風馬脚]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, trigger, effect, trigger, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 아래의 조건 만족 시 적진 주파 1 얻음
- 공격 시작 시 대상보다 속도가 2 이상 높을 때
- 자신의 스킬로 진동 폭발 효과 2회 발동시 (E.G.O 스킬 포함)
- 각력【오】를 보유 중인 상태로 합 승리 시
※ 적진 주파는 턴 당 최대 3까지 얻을 수 있으며, ‘흑풍마각월참’ 스킬로는 얻을 수 없음

자신에게 보호막이 있을 때, 방어 레벨이 (보호막 수치 / 10)만큼 증가 (최대 5, 소수점 버림)

### 98. LCE E.G.O:: 홍염살 — 불나방
- 상태: **partial** / 컴파일 규칙 4개
- 미지원: effect, effect, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, multi_target, special_state, stack_threshold
- 원문: 전투 시작 시 자신의 잃은 체력이 80% 이상이고 화상이 30 미만이면, 화상을 30까지 얻음. (스테이지 당 1회)

턴 종료 시 자신의 화상 6당, 다음 턴에 공격 레벨 증가 1 얻음 (최대 5)

사망 시 아래의 효과 발동
- 모든 적에게 화상 2 부여. 자신의 화상을 나누어 부여 (1명당 최대 3)
- 가장 부족한 속성의 E.G.O 자원 2종 2개씩 획득

홍염살 최대 감응 【열화침식】 스킬의 효과로 사망하였으면, 효과가 강화됨
- 모든 적에게 화상 3 부여. 자신의 화상을 나누어 부여 (1명당 최대 5)
- 가장 부족한 속성의 E.G.O 자원 2종 2개씩 획득
- 자신의 화상이 30 이상이었으면, 대기 해제되는 인원 1명에게 공격 레벨 증가 3 부여

### 99. 거미집 약지 제자 — 보호와 억제를 위한 갑주
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 스테이지에 첫 등장 시 아이언 메이든 얻음

턴 종료 시 자신에게 작품명: 파시아가 있으면, 아이언 메이든이 소멸하고, 구속 해제 - 창작 몰입 얻음 (전투당 1회)
- 흐트러짐 상태면, 흐트러짐 해제 (강제 흐트러짐 제외)

### 100. 남부 리우 협회 4과 — 전화
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger
- 분류: action_trigger, target_selection, probability_random, multi_target, cross_identity
- 원문: 속도가 가장 느린 아군 1명이 화상이 부여된 적 처치 시 무작위 적 2명에게 화상 3 부여 (턴 당 1회)
- 집중 전투에서는 부위에 부여

### 101. N사 E.G.O:: 경멸, 경외 — 너희 모두 재밌는 걸 보여주지
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 전투 시작 시 N사 E.G.O::흉탄 이상의 ‘대상 조정 사격’이 아래 효과 얻음
- 사용 전 N사 E.G.O::경멸, 경외 료슈가 시선의 경멸을 보유 중이고, 기본 스킬을 사용할 수 있으면, 대신 ‘쏘아내겠소 / 언제든지’를 료슈에게 사용함 (턴 당 1회. ‘쏘아내겠소 / 언제든지’는 이상의 동기화 단계가 적용됨)
- 사용 전 N사 E.G.O::경멸, 경외 료슈가 메인 타겟이 아니고, 기본 스킬을 사용할 수 있으면, 료슈가 메인 타겟을 스킬 1로 일방공격함 (턴 당 1회. [피아식별불가]. 스킬 1의 피해량 -50%. 해당 스킬로 메인 타겟이 사망하지 않음)

### 102. 동부 엄지 카포IIII — 삽시호 [揷翅虎]
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect, trigger, trigger, trigger, trigger, effect, effect
- 분류: action_trigger, resource_transform, special_state
- 원문: 상시 적용 : 호표탄 12개 보유

호표탄, 맹호표탄을 소모하는 코인을 굴릴 때, 해당 특수 탄환이 없는 경우에도 공격을 취소하지 않는 대신 해당 코인의 적중 시 화상 부여, 화상 횟수 증가 효과가 발동하지 않음

이번 전투에서 처음으로 수비 스킬을 장착하였거나 호표탄을 전부 사용, 또는 흐트러졌다면, 해당 턴 종료 시 맹호표탄 8발을 장전하고 천퇴성[天退星] 1 얻음 (전투당 1회)
- 흐트러짐 상태에서 효과 발동 시, 흐트러짐 상태 해제 (강제 흐트러짐 제외)
- 호표탄이 남아있으면 전부 소멸
- 자신이 소모한 호표탄과 맹호표탄의 합이 8 이상이면, 천퇴성[天退星]이 신(心) - 천퇴성[天退星]으로 변경

맹호표탄의 마지막 탄환을 소모하는 기본 공격 스킬을 사용할 경우,
- 공격 시작 전 공격 가중치 +2
- 다음 턴에 오버히트 1 얻음

### 103. 라만차랜드 왕자 — 왕자였던 자가 해야하는 일
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, trigger, trigger
- 분류: action_trigger, resource_transform, special_state, cross_identity
- 원문: 턴 시작 시 경혈 갑주가 최대인 라만차랜드 소속 인격에게 아래 효과 적용
· 연기 집중 1 얻음
· 피해로 인한 흐트러짐 상태일 때, 흐트러짐 해제하고 경혈 갑주 전부 소모 (스테이지 및 인격당 1회, 강제 흐트러짐 제외)

전투 인원에 라만차랜드 공주 로쟈가 있다면, 라만차랜드 공주 로쟈와 라만차랜드 왕자 뫼르소의 스킬 3 피해량 +15% (강화 스킬 포함)

### 104. 남부 디에치 협회 4과 — 깨달음의 빛
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, effect
- 분류: action_trigger, resource_transform, special_state
- 원문: 이번 턴 동안 받은 피해량에 비례하여 다음 턴에 타격 피해량 증가를 얻음.
(보호막으로 받은 피해도 받은 피해량에 포함됨. 턴 시작 시 체력의 25%만큼 피해를 받았을 때 최대로 획득. 최대 획득 값: 5)
턴 종료 시 탐구한 지식이 3 이면, 자신에게 부여된 부정적인 효과 중 1개를 제거

### 105. 약지 야수파 도슨트 — 부서지진 않게 조심조심…
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: trigger, trigger, trigger
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 편성 순서가 가장 빠른 인격에게 아래 효과 적용
- 색욕 공명 수가 홀수면, 출혈 위력 부여량 +1
- 색욕 공명 수가 짝수면, 침잠 위력 부여량 +1
- 해당 인격이 약지 소속 인격이면, 전투 시작시 공격 레벨 증가 1 또는 방어 레벨 증가 1을 얻음

### 106. 로보토미 E.G.O:: 홍적 — 기원부
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger
- 분류: target_selection, skill_transform, cross_identity
- 원문: 현재 체력이 가장 높은 아군 1명이 공격, 반격 스킬로 부여하는 파열 위력 부여 값 +1

### 107. 북부 제뱌찌 협회 3과 — 잠시만 부탁드려요...
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, resource_transform, special_state
- 원문: 턴 시작시 속도가 6 이상이거나 신속을 보유하였다면, 자신의 최대 체력의 (딜리버리 캐리어 - 싱클레어)%만큼 보호막을 얻음 (최대 20%)

### 108. 중지 작은 아우 — 빽
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 전투 시작 시, 현재 체력 비율이 가장 낮은 아군 1명이 방어 레벨 증가 2 얻음
- 대상이 중지 소속이면, 공격 레벨 증가 2 추가로 얻음

### 109. 거미집 소지 제자 — 정신일도
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect
- 분류: action_trigger, resource_transform, special_state
- 원문: 턴 종료시 25를 초과하는 호흡 위력을 최대 15까지 월하청도로 전환

전투 시작시 자신이 이번 턴에 (E.G.O 스킬 포함) 공격 스킬을 장착하지 않았으면, 정신력을 5 회복하고 다음 턴에 참격 위력 증가 1 얻음

### 110. 약지 점묘파 스튜던트 — 여러 점
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, probability_random, multi_target
- 원문: 전투 시작 시 부정적인 효과를 가장 적게 보유한 적 2명에게 화상, 출혈, 진동, 파열, 침잠 중 무작위 1개 효과 2 부여
(집중 전투인 경우, 부위로 판정)

### 111. LCA 우제트 선봉 3팀 팀장 — 호루스의 셉터 - 레플리카
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 턴 시작 시 적에게 패닉 타입 변경 효과가 있으면, 우제트의 눈 [선봉] 1 얻음

자신에게 우제트의 눈 [선봉]이 있으면, 기본 공격 스킬 적중 시 셰우트의 균열 1 부여 (턴당 최대 15)

자신의 기본 스킬, 우제트의 눈 [선봉]을 통해 얻는 보호 수치의 총합은 매턴마다 최대 5를 넘을 수 없음

### 112. LCA 우제트 선봉 3팀 팀장 — 호루스의 셉터 - 레플리카
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, effect, trigger, trigger
- 분류: action_trigger, resource_transform, special_state
- 원문: 턴 시작 시 적에게 패닉 타입 변경 효과가 있으면, 우제트의 눈 [선봉] 1 얻음

자신에게 우제트의 눈 [선봉]이 있으면, 기본 공격 스킬 적중 시 셰우트의 균열 1 부여 (턴당 최대 15)
- LCA 균열탄을 소모한 경우, 소모한 LCA 균열탄만큼 추가 부여

자신의 기본 스킬, 우제트의 눈 [선봉]을 통해 얻는 보호 수치의 총합은 매턴마다 최대 5를 넘을 수 없음

### 113. 로보토미 E.G.O:: 램프 — 아직 구해야 할 생명이 더 남아있었나
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect
- 분류: action_trigger, target_selection, resource_transform, cross_identity
- 원문: 턴 종료 시 부정적인 효과를 보유한 아군 중 편성 순서가 가장 빠른 아군에게 아래 효과 적용
- 다음 턴에 가장 왼쪽 슬롯이 도발치 4 얻음
- 다음 턴에 타격 피해량 증가 1 얻음

### 114. LCE E.G.O:: AEDD — 교류 방출 지원
- 상태: **partial** / 컴파일 규칙 1개
- 미지원: effect, effect, trigger
- 분류: action_trigger, resource_transform, special_state, cross_identity
- 원문: 턴 시작 시 E.G.O 장비를 착용한 아군이 자신 포함 셋 이상이면,
자신과 해당 아군 전부 공격 레벨 증가 1 얻음

그레고르의 E.G.O인 AEDD의 패시브 효과로 충전 횟수를 소모할 때 자신의 충전 횟수가 12 이하면, 앞면 적중 시 자신의 충전 횟수 2를 소모하는 대신, 보호막 또는 체력을 4씩 감소하여 효과 발동
- 체력이 25% 이상인 경우에만 발동

### 115. 어금니 사무소 해결사 — 벌려진 일 수습
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect
- 분류: action_trigger, target_selection, cross_identity
- 원문: 최대 체력이 가장 낮은 아군 1명이 적에게 진동 폭발 시 입히는 흐트러짐 손상 4 당 다음 턴에 방어 레벨 1 감소 부여 (턴마다 적 1명당 최대 3)

### 116. 흑수 - 오 필두 — 검은 갑각이 살을 째고 돋아 날 지키리
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, effect
- 분류: action_trigger, target_selection, cross_identity
- 원문: 최대 체력이 가장 높은 아군 1명에게 아래 효과 적용
- 전투 시작 시 방어 레벨이 (해당 캐릭터의 이전 턴과 이번 턴 속도 차이 x 2) 만큼 증가 (최대 5. 이전 턴에 전투 인원이 아니었다면, 해당 캐릭터의 기본 속도 최솟값으로 계산)
- 전투 시작 시 현재 체력이 최대 체력의 50% 미만이고, 이전 턴과 이번 턴 속도 차이가 3 이상이면, 체력 50 회복 (전투 당 1회)

### 117. 거미집 검지 아비 — 모조된 삶
- 상태: **partial** / 컴파일 규칙 2개
- 미지원: effect, effect, effect, effect, effect
- 분류: action_trigger, resource_transform, skill_transform
- 원문: 자신의 지령의 가호 1당 지령 표식 스킬 피해량 +2% (최대 16%)
 - 지령의 가호가 9일 경우, 대신 기본 스킬의 피해량 +20%

기본 공격 스킬의 파괴 불가 코인 적중 시, 대행 [헤르메스] 1 얻음
- 공격 종료 시, 남은 파괴 불가 코인 수만큼 대행 [헤르메스] 얻음
- ‘Furioso-Replica’ 공격 종료 시, 해당 스킬의 (남은 파괴 불가 코인 수/2)만큼 다음 턴에 대행 [헤르메스] 얻음 (소수점 버림)

턴 종료 시 이번 턴에 대행 [헤르메스]가 증가하여 9가 되었을 때,
다음 턴 시작 시 조작 슬롯에 스킬 3이 없으면, 기본 스킬 하나를 스킬 3으로 변경 (가장 왼쪽 슬롯의 아래 스킬 우선)

### 118. 남부 츠바이 협회 4과 — 보호 요청 수신
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: effect, trigger
- 분류: action_trigger, target_selection, cross_identity
- 원문: 전투 시작 시 체력 비율이 가장 낮은 아군 1명에게 방어 레벨 증가 2 부여
대상의 체력이 50% 미만이면 추가로 2 부여

### 119. 검지 수행자: 【쪽지】 — 지령이 이끄는 대로…
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, trigger, effect, trigger
- 분류: action_trigger, target_selection, cross_identity
- 원문: 편성 순서가 가장 빠른 인격에게 효과 적용
- 검지 소속 인격이 있으면, 해당 인격에게 우선 적용

전투 시작 시 자신의 조작 슬롯 중 가장 왼쪽 스킬로 지정한 적 슬롯을 다른 아군이 같이 지정했으면, 해당 스킬의 피해량이 자신을 제외하고 해당 슬롯을 타겟한 인원 수 1명당 5% 증가
(최대 15%, 자신과 아군 모두 기본 공격 스킬로 메인 타겟할 때 적용)

### 120. 로보토미 E.G.O:: 사랑과 증오의 이름으로 — 사랑과 증오의 이름으로 - !E.G.O 장비 동기화율 초과주의!
- 상태: **unsupported** / 컴파일 규칙 0개
- 미지원: trigger, effect, effect, effect, trigger, trigger, trigger
- 분류: action_trigger, resource_transform, stack_threshold
- 원문: 전투 중 누적으로 자신의 사랑/증오 횟수 10을 소모할 때마다, 사랑/증오 1 얻음

스테이지 시작시 히스테리가 없다면, 히스테리 효과를 얻음

스테이지 시작시 사랑/증오가 없다면, 사랑/증오 효과를 얻음

턴 시작시
- 정신력이 0 이상이면, 마법소녀 등장! 얻음, 역변-리버스드 제거
- 정신력이 0 미만이면, 역변-리버스드 얻음, 마법소녀 등장! 제거

자신의 기본 공격 스킬의 정신력 소모 효과에 의해서 정신력이 -40 미만으로 내려가지 않음
