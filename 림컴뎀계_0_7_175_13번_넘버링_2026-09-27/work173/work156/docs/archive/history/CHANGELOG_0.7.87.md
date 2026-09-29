# 0.7.87 — 실제 원문 `호흡` 위력/횟수 오판 수정

## 감사 목적
이번 수정은 신규 기믹 추가가 아니라, 실제 인격/스킬 원문과 기존 계산기 해석이 다른 사례를 수정한다.

## 확정 오판

실제 원문에서:
- `호흡 N 얻음/증가` = 호흡 **위력(Poise potency)**
- `호흡 횟수 N 증가` = 호흡 **횟수(Poise count)**

기존 `passive_compiler_v29.py`는 두 문법을 모두 `AddPoise(count=...)`로 처리했다.
`skill_text_parser_v19.py`도 같은 방식으로 bare `호흡 N`을 count로 기록했다.

### 실제 확인 사례
- `identity-10808` `선장의 명령`: `호흡 2 얻음` → 기존 count 2 → 수정 potency 2
- `identity-10916` `보냐텔리 가문의 수치`: `호흡 2 얻음, 자신의 호흡 횟수 2 증가` → 기존 두 효과 모두 count → 수정 potency 2 + count 2
- `identity-10415` `재회 [再會]`: `기본 공격 스킬 사용시 호흡 2 얻음` → potency 2로 정합화
- E.G.O/스킬 원문에도 동일 문법이 존재하므로 skill parser도 동일 규칙으로 정합화

## 수정
- `passive_compiler_v29.py`
  - bare `호흡` → `AddPoise(potency=...)`
  - explicit `호흡 횟수` → `AddPoise(count=...)`
- 공명 스케일링의 `호흡`/`호흡 횟수`도 동일하게 분리
- `skill_text_parser_v19.py`의 자원 획득 파서도 동일하게 분리

## 검증
- 신규 `test_actual_poise_source_audit_086.py`: **4 PASS / 0 FAIL**
- 관련 기존 감사 테스트 묶음: **21 PASS / 0 FAIL**

## 주의
`(오만 공명 수 / 2) + 1만큼 호흡 얻음`처럼 더 복잡한 공명 산식 자체는 별도 파서 범위이며, 이번 변경에서 임의로 확장하지 않았다. 이번 버전은 `호흡`의 potency/count 축 오판만 수정한다.
