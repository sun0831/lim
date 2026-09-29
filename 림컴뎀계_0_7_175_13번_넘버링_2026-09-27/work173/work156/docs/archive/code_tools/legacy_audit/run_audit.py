import json,sys
sys.path.insert(0,'/tmp/e23')
from skill_transform_audit_v1 import classify
D=json.load(open('/tmp/e23/GIMMICK_GAP_REPORT_v4.md.json'))
rows=[]
for r in D['gaps']:
    if 'skill_transform' in r.get('categories',[]):
        a=classify(r.get('source_text',''))
        rows.append({'identity_id':r.get('identity_id'),'identity_name':r.get('identity_name'),'source_text':r.get('source_text'),'classification':a.classification.value,'evidence':list(a.evidence),'confidence':a.confidence})
from collections import Counter
print('records',len(rows),'unique texts',len({r['source_text'] for r in rows}))
print(Counter(r['classification'] for r in rows))
for r in rows:
 print('\n###',r['classification'],r['confidence'],r['identity_name']); print(r['source_text'])
json.dump({'records':len(rows),'unique_source_texts':len({r['source_text'] for r in rows}),'classification_counts':Counter(r['classification'] for r in rows),'rows':rows},open('/tmp/e23/SKILL_TRANSFORM_AUDIT_E23.json','w',encoding='utf8'),ensure_ascii=False,indent=2,default=int)
