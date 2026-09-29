# 림컴뎀계 0.6.58 — Legacy Event Compatibility 분리

## 목적
`special_gimmick_v2.py`에 남아 있던 이벤트별 수동 compatibility 처리부를 별도 모듈로 추출했다.

### 분리된 이벤트
- `after_received_attack`
- `after_kill`
- `after_coin`
- `after_resource_event`
- `after_lifecycle_event`

새 모듈:
- `legacy_event_compat_v1.py`

## 구조

```text
special_gimmick_v2.py
  ├─ Rule IR compile/bridge
  ├─ Generic migration boundary
  ├─ Production event dispatch
  └─ Compatibility delegate
          ↓
legacy_event_compat_v1.py
  └─ 기존 수동/호환 이벤트 처리
```

`special_gimmick_v2.py`는 기존 공개 API를 유지하며 compatibility handler를 호출한다. 따라서 동작 변경 없이 분리 경계를 확보한다.

## 검증
- 신규 boundary test: 2 passed
- 전체 regression: 382 passed
- Python compile: PASS

## 다음 단계
분리된 `legacy_event_compat_v1.py`의 각 effect type을 실제 Generic `EffectExecutor`가 이미 처리하는 것과 비교해 중복 처리를 단계적으로 제거한다. 단순 삭제가 아니라 event/effect별 parity test를 유지하면서 Production 의존성을 0으로 만드는 것이 목표다.
