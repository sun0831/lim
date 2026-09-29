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

# 1턴 딜 계산의 '미구현 기믹' 우선순위에서 제외할 비전투/비딜성 효과.
# 혼합 패시브 전체를 버리지 않고, 아래 표현이 유일한 미지원 근거일 때만 gap에서 제외한다.
NON_DAMAGE_PATTERNS=[
 '회복','체력을 회복','최대 체력','보호막','피해를 받지 않고','체력이 1','사망하지 않','체력 1로 유지',
 'E.G.O 자원','전투 BGM','BGM','음악','도주 장치','패닉','행동 불가',
 '방어 레벨 증가','방어 레벨 감소','방어 레벨 +','방어 레벨 -',
]
DAMAGE_RELEVANCE_PATTERNS=[
 '피해량','피해','공격 레벨','공격 위력','최종 위력','코인 위력','크리티컬','치명타','관통','취약','내성',
 '출혈','화상','침잠','진동','파열','호흡','충전','탄환','추가 공격','일방 공격','원호 공격','보조 공격','반격',
 '스킬로 변경','스킬 3으로 변경','강화된 스킬','공격 종료','적중','흐트러','합 승리','처치','대상에게',
]

def classify(text):
 out=[]
 for k,ks in KEYWORDS.items():
  if any(x in text for x in ks): out.append(k)
 return out

def damage_relevance(text):
 hits=[p for p in DAMAGE_RELEVANCE_PATTERNS if p in text]
 non=[p for p in NON_DAMAGE_PATTERNS if p in text]
 return hits,non

def should_exclude_gap(rec):
 text=rec['source_text']
 hits,non=damage_relevance(text)
 # 완전히 비딜성인 레코드만 제외. 혼합 패시브는 유지.
 return bool(non) and not hits

def main(src,outjson,outmd):
 cat=json.load(open(src,encoding='utf-8'))
 rows=[]; summary=Counter(); by_ident=defaultdict(lambda:Counter()); gaps=[]; excluded=[]
 for ident in cat.get('identities',[]):
  for i,p in enumerate(ident.get('passives') or []):
   text=str(p.get('effect','')).strip()
   rules,reasons,unsupported=compile_one(p,ident['id'],i)
   status='full' if not unsupported else ('partial' if rules else 'unsupported')
   cats=classify(text)
   hits,non=damage_relevance(text)
   excluded_gap=(status!='full' and should_exclude_gap({'source_text':text}))
   rec={'identity_id':ident['id'],'identity_name':ident.get('name',''),'passive_name':p.get('name',''),'passive_id':p.get('id'),'status':status,'compiled_rules':len(rules),'unsupported_reasons':list(unsupported),'parsed_reasons':list(reasons),'categories':cats,'damage_relevance_hits':hits,'non_damage_hits':non,'excluded_from_damage_gap':excluded_gap,'source_text':text}
   rows.append(rec); summary[status]+=1; by_ident[(ident['id'],ident.get('name',''))][status]+=1
   if status!='full':
    if excluded_gap:
     excluded.append(rec); summary['excluded_non_damage']+=1
    else: gaps.append(rec)
   for u in unsupported: summary['unsupported:'+u]+=1
 def priority(r):
  s=0
  for c,w in [('skill_transform',8),('action_trigger',7),('resource_transform',6),('cross_identity',5),('target_selection',4),('special_state',3),('probability_random',3),('multi_target',3),('stack_threshold',3)]:
   if c in r['categories']: s+=w
  if r['status']=='unsupported': s+=4
  s += min(4,len(r['damage_relevance_hits']))
  return -s
 gaps.sort(key=priority)
 report={'version':2,'catalog_identities':len(cat.get('identities',[])),'passive_records':len(rows),'summary':dict(summary),'gap_count':len(gaps),'excluded_non_damage_count':len(excluded),'gaps':gaps,'excluded_non_damage':excluded,'identity_summary':[{'identity_id':i,'identity_name':n,**dict(c)} for (i,n),c in by_ident.items()]}
 json.dump(report,open(outjson,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 lines=['# 림컴뎀계 특수기믹 구현 공백 분석 v2','',f"- 인격: {report['catalog_identities']}개",f"- 패시브 레코드: {report['passive_records']}개",f"- 완전 컴파일: {summary['full']}개",f"- 부분 컴파일: {summary['partial']}개",f"- 완전 미지원: {summary['unsupported']}개",f"- 비딜성으로 우선순위 분석에서 제외: {summary['excluded_non_damage']}개",f"- 1턴 딜 관련 구현 공백 후보: **{len(gaps)}개**",'', '## 제외 기준','', '회복/최대 체력/보호막/생존 유지/BGM 등 1턴 피해량 산출에 직접 기여하지 않는 효과는 단독 미지원 항목일 경우 우선순위 목록에서 제외한다. 단, 같은 패시브에 공격·피해·스킬 변형·자원 등 딜에 영향을 주는 효과가 섞여 있으면 제외하지 않는다.','', '## 우선 구현 후보','', '스킬 변형, 추가·원호 공격, 흐트러짐 Trigger, 자원 변화, 인격 간 연계를 우선한다.','']
 for n,r in enumerate(gaps[:120],1):
  lines += [f"### {n}. {r['identity_name']} — {r['passive_name']}",f"- 상태: **{r['status']}** / 컴파일 규칙 {r['compiled_rules']}개",f"- 미지원: {', '.join(r['unsupported_reasons']) or '부분 미지원'}",f"- 분류: {', '.join(r['categories']) or '기타'}",f"- 딜 관련 키워드: {', '.join(r['damage_relevance_hits']) or '없음'}",f"- 원문: {r['source_text']}",'']
 open(outmd,'w',encoding='utf-8').write('\n'.join(lines))
 print(json.dumps(report['summary'],ensure_ascii=False,indent=2)); print('gap_count',len(gaps)); print('excluded_non_damage',len(excluded))

if __name__=='__main__': main(*sys.argv[1:])
