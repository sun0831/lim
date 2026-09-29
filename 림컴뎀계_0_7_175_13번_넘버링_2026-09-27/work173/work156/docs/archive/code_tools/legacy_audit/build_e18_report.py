import json
from resource_clause_decomposer_v1 import decompose_records
src='GIMMICK_GAP_REPORT_v4.md.json'
d=json.load(open(src,encoding='utf-8'))
rows=[x for x in d['gaps'] if 'resource_transform' in x.get('categories',[])]
res=decompose_records(rows)
res['source']=src
res['resource_transform_records']=len(rows)
res['unique_source_texts']=len({x.get('source_text','') for x in rows})
res['method']='Conservative clause candidate extraction; candidates overlap by design and do not assert full rule coverage.'
json.dump(res,open('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(res['record_count'],res['clause_candidate_count'],res['unresolved_count'])
print(res['candidate_counts'])
