# 림컴뎀계 0.5.86

0.5.85 기반. 조건부 합 위력(Clash Power) 공통 패턴을 실제 Clash 판정에 연결.

검증: pytest 181 passed.

## 0.5.91 코인별 명시 대상
- `coin_target_ids`: 코인 순서별 대상 ID를 지정한다.
- `coin_target_indices`: 대상 슬롯의 0-based index를 사용할 수 있는 별칭이다.
- 예: `coin_target_ids: ["t1", "t2"]` → 1코인은 t1, 2코인은 t2.
- 명시된 코인 대상은 일반 `target_count`보다 우선한다.
- 현재는 코인 1개당 대상 1개 지정만 지원하며, 1코인을 여러 대상에게 동시에 적용하는 별도 규칙은 아직 분리되어 있다.
