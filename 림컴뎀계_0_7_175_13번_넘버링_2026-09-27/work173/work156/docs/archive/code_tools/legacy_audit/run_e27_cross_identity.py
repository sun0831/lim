import json
from pathlib import Path
from cross_identity_clause_audit_v1 import audit_records
root=Path(__file__).parent
src=root/'GIMMICK_GAP_REPORT_v4.md.json'
d=json.loads(src.read_text(encoding='utf8'))
records=[g for g in d['gaps'] if 'cross_identity' in g.get('categories',[])]
res=audit_records(records)
res['source']='GIMMICK_GAP_REPORT_v4.md.json'
res['axis']='cross_identity'
res['record_count']=len(records)
res['unique_source_texts']=len({r['source_text'] for r in records})
res['note']='Counts are overlapping clause-level semantic hits, not coverage percentages. Existing_* means the semantic component appears representable by an existing common runtime; it does not prove the full clause is executable.'
(root/'CROSS_IDENTITY_AUDIT_E27.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
lines=[]
lines.append('# E27 Cross-Identity Audit')
lines.append('')
lines.append(f'- Source records: {len(records)}')
lines.append(f'- Unique source texts: {res["unique_source_texts"]}')
lines.append(f'- Clause candidates: {res["clause_count"]}')
lines.append('')
lines.append('## Semantic cluster hits (overlap allowed)')
for k,v in sorted(res['cluster_counts'].items(), key=lambda x:-x[1]): lines.append(f'- `{k}`: {v}')
lines.append('')
lines.append('## Primitive/runtime matching')
for k,v in sorted(res['match_counts'].items(), key=lambda x:-x[1]): lines.append(f'- `{k}`: {v}')
lines.append('')
lines.append('## Interpretation')
lines.append('- Cross-identity is treated as an analysis axis, not a standalone runtime.')
lines.append('- Affiliation membership/count is already backed by `AffiliationResolver`; target/event/resource/status/action components should be composed with common runtimes.')
lines.append('- Formation-order, owner/participant, and explicit identity-reference predicates remain partial until a common Condition/Selector contract is finalized.')
lines.append('- Do not treat clause counts as executable coverage; a single clause can contain several semantic primitives.')
(root/'CROSS_IDENTITY_AUDIT_E27.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({k:res[k] for k in ['record_count','unique_source_texts','clause_count','cluster_counts','match_counts']},ensure_ascii=False,indent=2))
