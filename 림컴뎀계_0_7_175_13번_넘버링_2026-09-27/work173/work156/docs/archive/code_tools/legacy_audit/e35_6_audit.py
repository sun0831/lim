import json, sys
sys.path.insert(0,'.')
from rule_ir_compiler_v1 import compile_compound_clause
src=json.load(open('E35_5_DECOMPOSITION_AUDIT.json'))
rows=src['rows']
counts={'implemented':0,'partial':0,'none':0}
examples=[]
for row in rows:
    r=compile_compound_clause(row['clause'], row.get('identity_id','unknown'), f"e35_6:{len(examples)}")
    if r is None:
        counts['none']+=1
    else:
        counts[r.status]=counts.get(r.status,0)+1
        if len(examples)<20 and r.status=='implemented': examples.append({'clause':row['clause'],'rule':r.to_dict()})
out={'version':'E35-6','input':len(rows),'lowering_counts':counts,'examples':examples}
json.dump(out,open('E35_6_COMPOUND_LOWERING_AUDIT.json','w'),ensure_ascii=False,indent=2)
print(out['lowering_counts'])
