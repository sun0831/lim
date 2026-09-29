from __future__ import annotations
import json,re
from pathlib import Path
from resource_clause_decomposer_v1 import decompose_records

ROOT=Path(__file__).resolve().parent
GAP=ROOT/'GIMMICK_GAP_REPORT_v4.md.json'
CAT=ROOT/'status_effect_catalog_v1.json'
OUT=ROOT/'STATUS_SIDE_CLAUSE_AUDIT_E26.json'
MD=ROOT/'STATUS_SIDE_CLAUSE_AUDIT_E26.md'

def load():
    gaps=json.loads(GAP.read_text(encoding='utf-8'))['gaps']
    records=[r for r in gaps if 'resource_transform' in r.get('categories',[])]
    dec=decompose_records(records)
    return [x for x in dec['clauses'] if x['kind']=='status_effect']

def primary(text):
    # Routing only: this audit does not claim semantic execution coverage.
    if re.search(r'스킬.*(?:변경|간주|취급)|(?:취급|간주).*스킬',text):
        return 'skill_or_classification'
    if re.search(r'(무작위|랜덤|메인 타겟|대상으로 지정|가장 낮|가장 높)',text):
        return 'target_or_action_compound'
    if re.search(r'사용함|사용한다|공격함|일방 공격|추가로.*공격',text):
        return 'action_trigger_compound'
    if re.search(r'(레벨|위력|피해량|코인|저항|크리티컬 피해|공격력|방어력).*(증가|감소|부여)|(?:증가|감소|부여).*(레벨|위력|피해량|코인)',text):
        return 'buff_debuff_modifier'
    if re.search(r'(호흡|침잠|화상|출혈|진동|파열|충전|혈흔|혈귀|잔영|얽힘|원한|문신|생체 재료|절연|조망|포자|파편|보호막|버프|디버프).*(얻음|부여|증가|감소|획득|제거|해제)',text):
        return 'status_effect'
    if re.search(r'(얻음|부여|증가|감소|획득|제거|해제|버프|디버프)',text):
        return 'status_effect_or_effect'
    return 'status_effect_compound'

rows=load()
counts={}
for r in rows:
    p=primary(r['text']); counts[p]=counts.get(p,0)+1
report={
 'stage':'E26', 'source':'GIMMICK_GAP_REPORT_v4.md.json',
 'input_resource_transform_records':sum(1 for r in json.loads(GAP.read_text(encoding='utf-8'))['gaps'] if 'resource_transform' in r.get('categories',[])),
 'status_effect_side_clause_candidates':len(rows),
 'unique_clause_texts':len(set(r['text'] for r in rows)),
 'routing_counts':counts,
 'policy':[
  '149 clauses are removed from Resource semantic scope; this is routing/audit, not execution coverage.',
  'Compound clauses may route to Buff/Status plus Action/Target/Skill systems.',
  'No new Status Runtime primitive is asserted solely from this audit.',
  'Existing status_effect_catalog_v1.py/status_effect_runtime_v1.py remain the execution source for catalog-backed common semantics; identity-specific effects remain deferred.'
 ],
 'clauses':rows,
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# E26 — Status Side Clause Audit','',f'- Resource-transform source records: {report["input_resource_transform_records"]}',f'- Status side clause candidates: **{len(rows)}**',f'- Unique clause texts: **{report["unique_clause_texts"]}**','', '## Routing counts']
for k,v in sorted(counts.items(),key=lambda x:(-x[1],x[0])): md.append(f'- `{k}`: {v}')
md += ['', '## Scope','- These 149 candidates are removed from the Resource Runtime scope and routed to the Buff/Status audit.','- Routing categories are conservative and may identify compound clauses; they are not claims that the entire clause is already executable.','- No new Status Runtime primitive is introduced in E26. Existing catalog/runtime is reused; unresolved identity-specific semantics remain explicit.']
MD.write_text('\n'.join(md)+'\n',encoding='utf-8')
print('wrote',OUT,MD)
print(counts)
