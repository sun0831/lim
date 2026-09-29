# 0.7.59 — 도발치 Target Selector 정합화

- 실제 `identity_catalog_v2.json`에서 `도발치가 가장 높은 슬롯을 보유한 아군 1명` 문구 2건 확인.
- `target_selector_v1.py`에 `taunt_max` 공통 selector 추가.
- alias: `highest_taunt`, `highest_provoke`.
- 정규 입력 `taunt`와 호환 입력 `taunt_value` / `provoke`를 지원.
- 특정 인격 전용 로직은 추가하지 않고 대상 선택 primitive만 공통화.
- 1턴 계산에서 사용자/시나리오가 제공한 도발치를 기준으로 결정론적으로 대상 선택.
