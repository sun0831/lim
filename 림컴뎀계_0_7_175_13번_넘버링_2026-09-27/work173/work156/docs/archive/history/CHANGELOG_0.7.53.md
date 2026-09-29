# 0.7.53 — Stagger 전이 이벤트 canonical metadata

- `check_stagger()`가 실제 상태 전이를 `stagger_transition` 이벤트로 기록하도록 확장.
- `before_staggered`, `after_staggered`, `newly_staggered`, level/index before/after를 한 이벤트에서 확인 가능하게 함.
- `source`, `forced`를 명시적 metadata로 추가. 강제 흐트러짐 여부를 수치 변화만으로 추측하지 않음.
- 기존 Stagger 상태에서 level/index가 강화되어도 `newly_staggered`는 재발동하지 않음.
- 실제 forced Stagger를 자동으로 만들어내는 규칙은 추가하지 않았으며, 향후 원문 확인 후 명시적 source/forced 인자로 연결할 수 있는 경계만 마련함.
