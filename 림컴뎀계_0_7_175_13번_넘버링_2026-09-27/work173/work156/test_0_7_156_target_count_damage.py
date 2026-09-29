import sys
sys.path.insert(0, '.')
from skill_text_parser_v19 import SkillTextParserV19

def test_0_7_156_target_wording_target_count_damage_condition():
    parser = SkillTextParserV19()
    parsed, report = parser.parse([
        '타겟이 1명이면, 피해량 +100% (집중 전투에서는 부위로 판정)'
    ], 4)
    assert report.unsupported == []
    conds = parsed['effects_on_use']
    assert conds == [{
        'type': '_skill_damage_condition_marker',
        'condition': {'type': 'target_count_eq', 'value': 1, 'amount': 1.0}
    }]
