# 림컴뎀계 0.5.14

## 이번 버전
특수자원 후보를 실제 실행 규칙과 분리하고, ResourceRuntime의 lifecycle 표현력을 확장했다.

### ResourceRuntime
- `gain()` / `consume()` 명시적 API 추가
- 임계값 연산자 `>=`, `>`, `<=`, `<`, `==` 지원
- 자원 변화와 별도로 `resource_threshold_reached` 이벤트 생성
- 스킬 변형/다음 행동 Resolve에서 현재 자원값을 그대로 조회 가능
- 기존 시나리오의 `resource_specs`와 하위 호환

### 특수자원 데이터
`SPECIAL_RESOURCE_CATALOG_v1.json`은 자동 추출된 고신뢰 후보를 **검증 대기 큐**로 저장한다.

중요: 후보 데이터는 게임 규칙 확정 데이터가 아니므로 자동으로 실행하지 않는다. 실제 규칙 검증 후 `executable=true`로 승격하는 방식이다.

- 고신뢰 후보: 35개
- 실행 확정 규칙: 0개

## 테스트
`python run_tests.py`

- Python compile: PASS
- pytest: **29 passed**
