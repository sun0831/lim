# 0.7.111 — 핵심 코드 경량화 2차

## 변경
- `one_turn_solver_v29.py`
  - 실제 사용되지 않는 `reuse_probability_runtime_v1` import 2개 제거.
  - 공명 보너스 계산에 남아 있던 죽은 코드(`if False` 분기) 제거.
  - 계산 결과와 외부 공개 API는 변경하지 않음.
- `passive_compiler_v29.py`
  - 실제 사용되지 않는 `deepcopy` import 제거.
- 큰 핵심 파일을 임의로 분할하거나 계산 로직을 이동하지 않음.
  - 의존성 위험이 큰 대규모 구조 변경은 다음 단계에서 별도 검토.

## 검증
- Python 문법 검사 PASS
- fast regression: 957 passed, 9 deselected
