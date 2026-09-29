from e35_unsupported_classifier_v1 import classify

def test_existing_selector_gap():
    assert classify('현재 체력 비율이 가장 낮은 아군에게 부여', ['trigger']) == 'existing_primitive_parser_gap'

def test_compound_skill_gap():
    assert classify('변경된 스킬이 다른 스킬로 변경되어 사용할 수 없게 되면 다시 발동', ['trigger']) == 'compound_clause_decomposition'

def test_true_visual_gap():
    assert classify('이번 턴이 종료될 때까지 전투 BGM을 변경', ['trigger']) == 'true_runtime_gap'

def test_unresolved_does_not_guess():
    assert classify('정체불명의 특수 현상', ['x']) == 'unresolved'
