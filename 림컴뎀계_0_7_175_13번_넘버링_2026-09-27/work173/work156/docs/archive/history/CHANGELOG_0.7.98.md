# 0.7.98 — Plus/Minus Coin Power 원문 오판 수정

## 감사 발견

버프/디버프 원문은 `Plus Coin Boost`와 `Minus Coin Boost`를 별개의 효과로 정의한다. 또한 `Plus Coin Drop`과 `Minus Coin Drop`도 각각 대응하는 코인 위력에 적용된다.

원문:
- Plus Coin Boost → `Plus Coin Power +X`
- Minus Coin Boost → `Minus Coin Power +X`
- Plus Coin Drop → `Plus Coin Power -X`
- Minus Coin Drop → `Minus Coin Power -X`

기존 구현은 `plus_coin_power`와 `minus_coin_power`를 모두 공통 `coin_power`로 접어 넣어, 반대 극성의 코인에도 효과가 적용될 수 있는 구조였다.

## 수정

- `status_effect_runtime_v1.py`
  - `plus_coin_power` → 별도 modifier
  - `minus_coin_power` → 별도 modifier
- `damage_modifier_runtime_v1.py`
  - 두 modifier 채널 추가
- `limbus_damage_engine_v29.py`
  - Plus Coin은 plus coin에만
  - Minus Coin은 minus coin에만
  적용하도록 분리
- 관련 테스트 갱신 및 polarity-scope 회귀 테스트 추가
- `VERSION`을 0.7.98로 정합화

## 검증

- `test_status_effect_runtime.py`
- `test_buff_debuff_runtime.py`
- 결과: **35 passed / 0 failed**

## 보류

`Multiply Coin Boost/Drop`은 원문에 존재하지만 현재 공통 modifier 체계에서 별도 의미 채널이 없으므로 이번 수정에서 임의로 `coin_power`에 합치지 않았다.
