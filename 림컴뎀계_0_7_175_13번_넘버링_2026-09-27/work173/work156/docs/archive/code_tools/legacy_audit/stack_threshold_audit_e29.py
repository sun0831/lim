import json,re,collections
from pathlib import Path
ROOT=Path(__file__).parent
src=ROOT/'GIMMICK_GAP_REPORT_v4.md.json'
d=json.loads(src.read_text(encoding='utf-8'))['gaps']
rs=[r for r in d if 'stack_threshold' in r['categories']]
clusters=collections.Counter(); rows=[]
for r in rs:
 t=r['source_text']
 cs=[]
 if re.search(r'충전|생체 재료|예지안|호흡 횟수|호흡 위력|사랑/증오|경혈|지령의 가호|꽃잎|적안|참회|분노 공명|연료|자원|주살',t): cs.append('resource_or_stack_threshold')
 if re.search(r'화상 위력|화상 횟수|출혈이? ?\d+|침잠 위력|진동 횟수|잔향|도발치',t): cs.append('status_threshold')
 if re.search(r'정신력.*\d+|정신력이?\s*[-]?\d+|정신력.*이상|정신력.*미만',t): cs.append('mental_threshold')
 if re.search(r'체력.*\d+%|현재 체력 비율|체력이? \d+%|체력의',t): cs.append('hp_threshold')
 if re.search(r'속도가?.*\d+|속도.*\d+',t): cs.append('speed_threshold')
 if re.search(r'누적|\d+을 소모할 때마다|\d+ 이상|\d+ 미만|\d+ 이하|\d+이 되|\d+이? 되면',t): cs.append('count_threshold')
 if re.search(r'공명 수|공명',t): cs.append('resonance_threshold')
 if re.search(r'턴당|전투당|최대 \d+회|최대 \d+명|최대 \d+%',t): cs.append('activation_cap')
 if not cs: cs=['unresolved']
 for c in cs: clusters[c]+=1
 rows.append({'identity':r['identity_name'],'source_text':t,'clusters':cs})
print('records',len(rs),'unique',len(set(r['source_text'] for r in rs)))
print(clusters)
for i,x in enumerate(rows,1): print(i,x['clusters'],x['identity'],x['source_text'].split('\n')[0][:180])
(Path(ROOT)/'STACK_THRESHOLD_AUDIT_E29.json').write_text(json.dumps({'records':len(rs),'unique_source_texts':len(set(r['source_text'] for r in rs)),'cluster_counts':clusters,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
