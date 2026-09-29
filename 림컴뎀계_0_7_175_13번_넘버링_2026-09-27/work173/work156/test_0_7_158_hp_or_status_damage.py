from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_text_parser_v19 import SkillTextParserV19

def test_1121403_hp_or_status_is_preserved_as_or_condition():
    p=SkillTextParserV19()
    r,rep=p.parse(['3코인 대상(본체)의 체력이 25% 이하거나 대상에게 현혹이 있으면, 피해량 +60%'],3)
    c=r['coin_defs'][2]['damage_conditions'][0]['condition']
    assert c['type']=='or'
    assert c['conditions'][0]['type']=='enemy_hp_pct_lte'
    assert c['conditions'][1] == {'type':'status','name':'현혹','target':'enemy','count_gte':1}
    assert r['coin_defs'][2]['damage_conditions'][0]['amount']==0.60
    assert not rep.unsupported
