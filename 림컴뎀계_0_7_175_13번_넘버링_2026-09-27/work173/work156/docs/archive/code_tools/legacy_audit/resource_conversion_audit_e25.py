from __future__ import annotations
import json,re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).parent
SRC=ROOT/'GIMMICK_GAP_REPORT_v4.md.json'
OUT=ROOT/'RESOURCE_CONVERSION_AUDIT_E25.json'
D=json.loads(SRC.read_text())['gaps']
records=[]
for r in D:
    t=r.get('source_text','')
    hits=[]
    if re.search(r'\b소모하여\b',t) and re.search(r'\b얻음\b|\b얻는다\b',t):
        hits.append('fixed_or_proportional_conversion')
    if '얻을 때, 대신' in t or '획득할 때, 대신' in t:
        hits.append('substitution')
    if '소모한 만큼' in t and ('보급' in t or '증가' in t or '얻' in t):
        hits.append('transfer')
    if '전환되어' in t or '전환되어 얻음' in t:
        hits.append('substitution')
    if '변환' in t and any(x in t for x in ['자원','충전','탄환','포자탄','호흡','눈물','적안','참회','고전압 외피']):
        hits.append('named_conversion')
    if hits:
        records.append({
            'identity_name':r.get('identity_name',''),
            'passive_name':r.get('passive_name',''),
            'source_text':t,
            'conversion_candidates':sorted(set(hits)),
        })
# de-duplicate exact source text for semantic audit
unique={x['source_text']:x for x in records}
counts=Counter(c for x in unique.values() for c in x['conversion_candidates'])
report={
 'stage':'E25',
 'source':'GIMMICK_GAP_REPORT_v4.md.json',
 'all_gap_records':len(D),
 'raw_conversion_candidate_records':len(records),
 'unique_conversion_candidate_texts':len(unique),
 'candidate_kind_counts':dict(counts),
 'confirmed_patterns':[
   {'kind':'fixed_or_proportional_conversion','examples':['포자탄[기본] 2 소모하여, 포자탄[산탄] 1 얻음','가속탄 소모한 수치 1당, 호흡 2 얻음']},
   {'kind':'substitution','examples':['충전 횟수를 획득할 때, 대신 깊은 눈물을 얻음','충전 횟수를 획득할 때, 대신 적안 또는 참회를 얻음','충전 역장을 얻을 때, 고전압 외피로 전환되어 얻음']},
   {'kind':'transfer','examples':['작열 추진탄을 소모한 만큼 해당 인격이 사용하는 탄환을 보급함','초과 충전 횟수를 소모하고 ... 아군의 충전 횟수 증가']},
 ],
 'decision':{
   'new_primitive_required':True,
   'primitive':'RESOURCE_CONVERSION',
   'reason':'Existing SkillTextParserV19 already has resource_convert/resource_gain_from_consumed executable effect kinds, but resource_primitive_v1.py did not normalize those kinds into the common ResourcePrimitive registry.',
   'not_a_new_runtime':'Conversion is represented as a composable primitive; execution remains in existing Effect/Resource runtime paths.',
 },
 'records':list(unique.values())
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2))
# concise md
md=ROOT/'RESOURCE_CONVERSION_AUDIT_E25.md'
md.write_text(f'''# E25 Resource Conversion Audit\n\n- Source: `GIMMICK_GAP_REPORT_v4.md.json`\n- Total gap records: {len(D)}\n- Raw candidate records: {len(records)}\n- Unique candidate texts: {len(unique)}\n\n## Decision\n\nA real common primitive is required: `RESOURCE_CONVERSION`.\n\nThis is **not** a new standalone runtime. Existing parser execution already supports `resource_convert` and `resource_gain_from_consumed`; E25 normalizes those effects into the common primitive registry.\n\n### Modes\n- `fixed`: A amount -> B amount\n- `proportional`: consumed A unit(s) -> B amount per unit\n- `substitution`: acquisition of A is replaced by B\n- `transfer`: A is consumed from one holder and B is supplied to another holder/target\n\nThe mode is explicit; no semantic guessing is performed.\n''')
