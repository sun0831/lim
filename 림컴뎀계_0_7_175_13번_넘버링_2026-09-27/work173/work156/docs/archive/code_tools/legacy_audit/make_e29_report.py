import json,collections
from pathlib import Path
from stack_threshold_audit_v1 import route_clause
root=Path('/tmp/e29'); d=json.loads((root/'GIMMICK_GAP_REPORT_v4.md.json').read_text(encoding='utf-8'))['gaps']
rs=[r for r in d if 'stack_threshold' in r['categories']]
rows=[]; c=collections.Counter()
for r in rs:
 routes=route_clause(r['source_text'])
 for x in routes:c[x.route]+=1
 rows.append({'identity_id':r['identity_id'],'identity_name':r['identity_name'],'source_text':r['source_text'],'routes':[x.__dict__ for x in routes]})
out={'axis':'stack_threshold','records':len(rs),'unique_source_texts':len(set(r['source_text'] for r in rs)),'cluster_counts':dict(c),'new_axis_runtime_required':False,'rationale':'Existing ConditionRuntime supports generic numeric comparisons, resource thresholds, status count/potency thresholds, HP percentage thresholds, resonance conditions; activation limits are handled by trigger/ledger semantics. Therefore stack_threshold is an analysis axis, not a standalone runtime.','rows':rows}
(root/'STACK_THRESHOLD_AUDIT_E29.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# E29 Stack Threshold Audit','',f'- records: {out["records"]}',f'- unique source texts: {out["unique_source_texts"]}','- new standalone StackThreshold Runtime: **not required**','', '## Routing']
for k,v in c.items(): md.append(f'- `{k}`: {v}')
md += ['', '## Contract decision','Thresholds are routed to existing Condition/Resource/Status/Trigger contracts. No new axis-specific runtime is introduced.']
(root/'STACK_THRESHOLD_AUDIT_E29.md').write_text('\n'.join(md),encoding='utf-8')
