# 0.7.107

## 오판 수정 — 누적 소모 혈찬 피해량 스케일링

- `자신의 누적 소모 혈찬 N당 피해량 +X%`를 현재 보유 혈찬(`FighterState.resources`)으로 읽던 문제 수정.
- encounter-scoped `cumulative_resource_consumed[(identity_id, resource)]`를 읽는 전용 Value를 추가.
- `적중시 자신의 누적 소모 혈찬 10당, 피해량 +1% (최대 20%)` 형태에서 `적중시`가 자원명에 포함되던 generic regex 오인식도 방지.
- `공용 누적 소모 혈찬`은 별도의 shared cumulative counter가 필요하므로 이번 변경 범위에서 구현하지 않음.
