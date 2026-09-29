import json, unittest
import passive_compiler_v29 as pc
from skill_text_parser_v19 import SkillTextParserV19

class TestActualPoiseSourceAudit086(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    def _find(self, ident, needle):
        i=next(x for x in self.cat['identities'] if x['id']==ident)
        return next(p for p in i.get('passives',[]) if needle in p.get('effect',''))
    def test_plain_poise_is_potency(self):
        p=self._find('identity-10808','호흡 2 얻음')
        rules,_,_=pc.compile_one(p,'identity-10808',0)
        eff=[e for r in rules for e in r.effects if type(e).__name__=='AddPoise']
        self.assertTrue(any(e.potency.resolve(None,None,'identity-10808')==2 and e.count.resolve(None,None,'identity-10808')==0 for e in eff))
    def test_plain_poise_and_explicit_count_are_separate(self):
        p=self._find('identity-10916','가속탄 소모한 수치 1당')
        rules,_,_=pc.compile_one(p,'identity-10916',0)
        eff=[e for r in rules for e in r.effects if type(e).__name__=='AddPoise']
        self.assertGreaterEqual(sum(e.potency.resolve(None,None,'identity-10916') for e in eff),2)
        self.assertGreaterEqual(sum(e.count.resolve(None,None,'identity-10916') for e in eff),2)
    def test_resonance_plain_poise_is_potency(self):
        eff=[x.effect for x in pc.parse_effects('(최대 공명 수)만큼 호흡 얻음 (최대 7)') if type(x.effect).__name__=='AddPoise']
        self.assertTrue(any(e.potency.__class__.__name__=='ResonanceValue' and e.count.resolve(None,None,'identity-11015')==0 for e in eff))
    def test_skill_parser_plain_poise_is_potency(self):
        p=SkillTextParserV19()
        out=p._use_effect('기본 공격 스킬 효과로 호흡 2 얻음')
        self.assertIn({'type':'poise','potency':2},out)
        out=p._use_effect('기본 공격 스킬 효과로 호흡 횟수 2 증가')
        self.assertIn({'type':'poise','count':2},out)

if __name__=='__main__': unittest.main()
