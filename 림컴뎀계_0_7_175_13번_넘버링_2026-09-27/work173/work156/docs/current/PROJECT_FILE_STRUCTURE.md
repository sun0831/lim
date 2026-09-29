# 프로젝트 파일 구조 (0.7.108 정리본)

## 목적
기능 코드는 건드리지 않고, 과거 문서·감사 결과·백업·캐시를 실행 영역과 분리한다.

## 현재 영역
- `*.py` : 기존 실행 코드와 테스트. 이번 정리에서는 import 관계를 건드리지 않기 위해 위치를 유지한다.
- `gimmick_modules/` : 기믹 모듈.
- `tools/` : 기존 도구.
- `*.json` : 현재 계산에 필요한 핵심 데이터/설정과 기존 테스트가 직접 참조하는 기준 데이터.
- `docs/current/` : 현재 참고해야 하는 문서.

## 보관 영역
- `docs/archive/history/` : 과거 README, CHANGELOG, 설계/작업 보고서.
- `docs/archive/reports/` : 현재 테스트가 직접 참조하지 않는 과거 audit/report JSON.
- `docs/archive/outputs/` : 과거 txt 결과물.
- `docs/archive/backups/` : `.bak*` 백업 파일.

## 제외
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`

이번 단계에서는 Python import 경로와 Runtime 코드 위치를 변경하지 않았다. 따라서 기능 변경 없이 파일 정리만 수행한 단계다.
