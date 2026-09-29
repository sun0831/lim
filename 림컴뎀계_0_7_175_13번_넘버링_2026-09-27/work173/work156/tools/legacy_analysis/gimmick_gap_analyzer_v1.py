import json,re,sys
from collections import Counter,defaultdict
from passive_compiler_v29 import compile_one

KEYWORDS={
 'action_trigger':['사용 후','공격 종료','공격 시작','적중 시','합 승리','피격','사망 시','흐트러','턴 시작','턴 종료','전투 시작','전투 종료','스킬 종료','회피 성공','처치','부위 파괴'],
 'target_selection':['가장 높은','가장 낮은','가장 빠른','가장 느린','편성 순서','무작위','아군 1명','아군 2명','아군 3명'],
 'resource_transform':['소모','교체','변경','전환','재장전','보급','얻음','획득'],
 'skill_transform':['스킬 3으로 변경','스킬로 변경','변경됨','강화된 스킬','일방 공격','추가 공격','원호 공격','보조 공격','반격'],
 'probability_random':['확률','무작위','랜덤'],
 'multi_target':['각 대상','모든 아군','모든 적','2명','3명'],
 'special_state':['E.G.O','침식','패닉','행동 불가','강제 흐트러짐','보호막','초근성'],
 'stack_threshold':['5 이상','10 이상','15 이상','20 이상','25 이상','30 이상','5를 소모','10을 소모','횟수마다','수치가 0'],
 'cross_identity':['아군','동료','소속','편성','자신 이외','다른 캐릭터'],
}

def classify(text):
 out=[]
 for k,ks in KEYWORDS.items():
  if any(x in text for x in ks): out.append(k)
 return out

def main(src,outjson,outmd):
 cat=json.load(open(src,encoding='utf-8'))
 rows=[]; summary=Counter(); by_ident=defaultdict(lambda:Counter()); gaps=[]
 for ident in cat.get('identities',[]):
  for i,p in enumerate(ident.get('passives') or []):
   text=str(p.get('effect','')).strip()
   rules,reasons,unsupported=compile_one(p,ident['id'],i)
   # compile_one may compile some clauses while leaving others unsupported.
   status='full' if not unsupported else ('partial' if rules else 'unsupported')
   cats=classify(text)
   rec={'identity_id':ident['id'],'identity_name':ident.get('name',''),'passive_name':p.get('name',''),'passive_id':p.get('id'),'status':status,'compiled_rules':len(rules),'unsupported_reasons':list(unsupported),'parsed_reasons':list(reasons),'categories':cats,'source_text':text}
   rows.append(rec); summary[status]+=1; by_ident[(ident['id'],ident.get('name',''))][status]+=1
   if status!='full': gaps.append(rec)
   for u in unsupported: summary['unsupported:'+u]+=1
 # prioritize gaps: actual dynamic/combat complexity first
 def priority(r):
  s=0
  for c,w in [('skill_transform',6),('action_trigger',5),('resource_transform',5),('cross_identity',4),('target_selection',3),('special_state',3),('probability_random',3),('multi_target',2),('stack_threshold',2)]:
   if c in r['categories']: s+=w
  if r['status']=='unsupported': s+=4
  return -s
 gaps.sort(key=priority)
 report={'version':1,'catalog_identities':len(cat.get('identities',[])),'passive_records':len(rows),'summary':dict(summary),'gap_count':len(gaps),'gaps':gaps,'identity_summary':[{'identity_id':i,'identity_name':n,**dict(c)} for (i,n),c in by_ident.items()]}
 json.dump(report,open(outjson,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 lines=['# 림컴뎀계 특수기믹 구현 공백 분석 v1','',f"- 인격: {report['catalog_identities']}개",f"- 패시브 레코드: {report['passive_records']}개",f"- 완전 컴파일: {summary['full']}개",f"- 부분 컴파일/미지원 요소 포함: {summary['partial']}개",f"- 완전 미지원: {summary['unsupported']}개",'']
 lines += ['## 미지원 사유','']
 for k,v in sorted(summary.items()):
  if k.startswith('unsupported:'): lines.append(f'- `{k.split(":",1)[1]}`: {v}')
 lines += ['', '## 우선 구현 후보','', '아래 목록은 단순히 미지원 개수 순서가 아니라, 1턴 데미지 계산에 영향을 크게 주는 동적 트리거/자원/스킬 변환/연계 기믹을 우선 표시한다.','']
 for n,r in enumerate(gaps[:120],1):
  lines += [f"### {n}. {r['identity_name']} — {r['passive_name']}",f"- 상태: **{r['status']}** / 컴파일 규칙 {r['compiled_rules']}개",f"- 미지원: {', '.join(r['unsupported_reasons']) or '부분 미지원'}",f"- 분류: {', '.join(r['categories']) or '기타'}",f"- 원문: {r['source_text']}",'']
 open(outmd,'w',encoding='utf-8').write('\n'.join(lines))
 print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
 print('gap_count',len(gaps))

if __name__=='__main__': main(*sys.argv[1:])
