import json
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import SelfSPAtMost, CoinPolarityIs


def test_10913_negative_sp_minus_coin_rules_are_conditioned():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10913')
    hits=[]
    for i,p in enumerate(ident.get('passives') or []):
        if '정신력이 -15 이하면' in p.get('effect','') or '정신력이 -30 이하면' in p.get('effect',''):
            rules,_,_=compile_one(p,ident['id'],i)
            hits.extend(rules)
    assert hits
    def flat(r):
        out=[]
        for c in r.conditions:
            out.extend(getattr(c,'conditions',(c,)))
        return out
    assert all(any(isinstance(c,SelfSPAtMost) for c in flat(r)) for r in hits)
    assert all(any(isinstance(c,CoinPolarityIs) for c in flat(r)) for r in hits)
    assert any(isinstance(c,SelfSPAtMost) and c.value == -15 for c in flat(hits[0]))
    assert any(isinstance(c,SelfSPAtMost) and c.value == -30 for c in flat(hits[-1]))
