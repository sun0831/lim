import json,collections,os
from pathlib import Path
src=Path('/tmp/e19/GIMMICK_GAP_REPORT_v4.md.json')
out=Path('/tmp/e19')
d=json.load(src.open(encoding='utf-8'))
rs=[r for r in d['gaps'] if 'resource_transform' in r['categories']]
# E18 clause candidates
c=json.load((out/'RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json').open(encoding='utf-8'))['clauses']
mapk={
 'trigger':'trigger_to_resource_or_effect',
 'resource_gain':'direct_resource_gain',
 'resource_consume':'resource_consumption',
 'resource_transform':'resource_conversion',
 'affiliation_count':'affiliation_scaled_resource',
 'resource_scaled_modifier':'resource_scaled_modifier',
 'resource_zero':'resource_zero_state',
 'lowest_resource_selector':'resource_based_target_selection',
 'random_target':'random_target_selection',
 'count_scaling':'count_or_stack_scaling',
 'skill_transform':'resource_skill_transform',
 'status_effect':'status_effect_side_clause',
 'unresolved':'non_resource_or_special_clause',
}
clusters=collections.defaultdict(list)
for x in c: clusters[mapk[x['kind']]].append(x)
# dedup exact clause text within cluster
cluster_stats=[]
for k,items in clusters.items():
 texts={x['text'] for x in items}
 cluster_stats.append({'cluster':k,'candidate_count':len(items),'unique_clause_texts':len(texts),'examples':[{'identity_name':x['identity_name'],'passive_name':x['passive_name'],'text':x['text']} for x in items[:5]]})
# per record cluster membership
byrec=collections.defaultdict(set)
for x in c: byrec[x['identity_id']].add(mapk[x['kind']])
# identity_id alone may duplicate same passive? use source text+id+passive
bykey=collections.defaultdict(set)
for x in c: bykey[(x['identity_id'],x['passive_name'],x['text'])].add(mapk[x['kind']])
# actual resource primitive clauses exclude trigger/status/unresolved/count? count is primitive parameter, keep.
resource_kinds={'resource_gain','resource_consume','resource_transform','affiliation_count','resource_scaled_modifier','resource_zero','lowest_resource_selector','random_target','count_scaling','skill_transform'}
resource_clause=[x for x in c if x['kind'] in resource_kinds]
records_with_resource={(x['identity_id'],x['passive_name'],x['text']) for x in resource_clause}
report={
 'stage':'E19',
 'source':'GIMMICK_GAP_REPORT_v4.md.json',
 'record_count':len(rs),
 'unique_source_texts':len({r['source_text'] for r in rs}),
 'exact_duplicate_records':len(rs)-len({r['source_text'] for r in rs}),
 'e18_clause_candidate_count':len(c),
 'e18_candidate_counts':c and dict(collections.Counter(x['kind'] for x in c)),
 'semantic_method':'Conservative semantic clustering built from E18 clause decomposition. A source record may belong to multiple clusters; counts are not additive.',
 'clusters':sorted(cluster_stats,key=lambda z:-z['candidate_count']),
 'resource_clause_records':len(records_with_resource),
 'non_resource_or_special_candidate_count':len(clusters.get('non_resource_or_special_clause',[])),
 'unresolved_candidate_count':len(clusters.get('non_resource_or_special_clause',[])),
 'notes':[
  'resource_transform is a broad source category; it contains mixed clauses that are not themselves resource operations.',
  'candidate/cluster counts are structural evidence, not implementation coverage percentages.',
  'No clause was forced into a generic resource conversion primitive when the source text did not specify one.'
 ]
}
json.dump(report,(out/'RESOURCE_SEMANTIC_CLUSTER_E19.json').open('w',encoding='utf-8'),ensure_ascii=False,indent=2)
md=['# E19 Resource Semantic Clustering','',f'- Source records: **{len(rs)}**',f'- Unique source texts: **{len({r["source_text"] for r in rs})}**',f'- Exact duplicate records: **{len(rs)-len({r["source_text"] for r in rs})}**',f'- E18 clause candidates: **{len(c)}**','', '## Method','E19 clusters the E18 clause candidates by the semantic operation represented by the source clause. One record may map to multiple clusters. This is a decomposition map, not a claim that every source rule is already executable.','', '## Clusters']
for s in sorted(cluster_stats,key=lambda z:-z['candidate_count']):
 md += [f"### {s['cluster']}",f"- Candidates: **{s['candidate_count']}**",f"- Unique clause texts: **{s['unique_clause_texts']}**"]
 for e in s['examples'][:3]: md.append(f"- {e['identity_name']} / {e['passive_name']}: {e['text'].replace(chr(10),' ')[:260]}")
md += ['', '## Interpretation','- The large `status_effect_side_clause`, `trigger_to_resource_or_effect`, and `non_resource_or_special_clause` groups show why the original `resource_transform` tag cannot be treated as a single Runtime type.','- `count_or_stack_scaling` is a parameter/condition axis that frequently composes with resource gain/consume rather than being a standalone resource runtime.','- `resource_conversion` remains small because the source must explicitly describe one resource becoming another/state; no generic conversion was inferred from ordinary gain/consume wording.','- Next implementation target should be the reusable primitives already represented in `resource_primitive_v1.py`, then the remaining cross-clause target/condition pieces.']
(out/'RESOURCE_SEMANTIC_CLUSTER_E19.md').write_text('\n'.join(md),encoding='utf-8')
print(report['resource_clause_records'], report['non_resource_or_special_candidate_count'])
