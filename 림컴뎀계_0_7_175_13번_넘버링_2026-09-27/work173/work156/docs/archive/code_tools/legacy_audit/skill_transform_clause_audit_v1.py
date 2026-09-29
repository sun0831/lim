from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re, json

class SkillClause(str, Enum):
    SWAP='true_skill_swap'
    RECLASSIFY='skill_reclassify'
    NEXT_TURN_SWAP='next_turn_skill_swap'
    SKILL_TAG='skill_tag_or_marker'
    COIN_MOD='coin_or_power_transform'
    FORCED_ACTION='forced_or_followup_skill'
    SKILL_TRIGGER='conditional_skill_trigger'
    OTHER='non_skill_clause'
    UNRESOLVED='unresolved'

@dataclass
class Row:
    source_id:str; text:str; kind:str; evidence:list[str]

def clauses(text):
    # preserve bullet/newline clauses; split long lines at sentence-ish boundaries conservatively
    out=[]
    for part in re.split(r'\n+',text):
        part=part.strip(' -•')
        if not part: continue
        # don't over-split because Korean rule clauses often depend on following bullets
        out.append(part)
    return out

def classify(t):
    ev=[]
    if re.search(r'스킬.*?취급됨|스킬.*?취급|인격.*?취급됨|간주함|간주됨',t):
        return SkillClause.RECLASSIFY,['취급/간주']
    if re.search(r'다음 턴.*?(?:스킬|기본 스킬).*?(?:변경|사용)',t):
        return SkillClause.NEXT_TURN_SWAP,['다음 턴 스킬 변경/사용']
    if re.search(r'(?:기본|반격|스킬).*?(?:하나를|을|이).*?(?:변경|교체|변환)',t) and '스킬' in t:
        return SkillClause.SWAP,['스킬 변경/교체']
    if re.search(r'코인.*?(?:변경|증가|감소|파괴 불가)|최종 위력.*?[+\-]|스킬.*?위력.*?[+\-]',t):
        return SkillClause.COIN_MOD,['코인/위력 변화']
    if re.search(r'(?:일방 공격|원호 공격|반격).*?(?:사용|발동)',t):
        return SkillClause.FORCED_ACTION,['추가/강제 스킬 발동']
    if re.search(r'(?:스킬|공격).*?(?:사용 시|적중 시|승리 시|종료 시)',t):
        return SkillClause.SKILL_TRIGGER,['스킬 이벤트 트리거']
    if re.search(r'스킬|공격',t):
        return SkillClause.UNRESOLVED,['스킬 관련이나 유형 불명']
    return SkillClause.OTHER,[]

D=json.load(open('/tmp/e23/GIMMICK_GAP_REPORT_v4.md.json'))
rows=[]
for i,r in enumerate(D['gaps']):
    if 'skill_transform' not in r.get('categories',[]): continue
    for j,c in enumerate(clauses(r.get('source_text',''))):
        k,e=classify(c)
        if k != SkillClause.OTHER:
            rows.append(Row(f'{i}:{j}',c,k.value,e))
from collections import Counter
print('clause candidates',len(rows)); print(Counter(x.kind for x in rows))
json.dump({'clause_count':len(rows),'counts':Counter(x.kind for x in rows),'rows':[asdict(x) for x in rows]},open('/tmp/e23/SKILL_TRANSFORM_CLAUSE_AUDIT_E23.json','w',encoding='utf8'),ensure_ascii=False,indent=2,default=int)
