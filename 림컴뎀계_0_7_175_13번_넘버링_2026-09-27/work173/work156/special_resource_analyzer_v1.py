"""Catalog audit for non-E.G.O, non-Sin identity-specific resources/counters."""
from __future__ import annotations
import json,re
from functools import lru_cache

SIN={'분노','색욕','나태','탐식','우울','오만','질투'}
EGO=re.compile(r'E\.G\.O',re.I)
VERBS={
 'gain':re.compile(r'(얻음|획득|증가|부여)',re.M),
 'loss':re.compile(r'(소모|감소|잃음|차감)',re.M),
 'threshold':re.compile(r'(\d+\s*(?:이상|이하)|수치가\s*0|없으면|있을\s*때|보유)',re.M),
 'transform':re.compile(r'(변경|전환|교체|강화)',re.M),
}
# Resource-like quoted/name tokens; excludes ordinary skill/status prose by requiring
# a resource lifecycle verb in the same sentence/block.
TOKEN=re.compile(r"['‘’\"]([^'‘’\"]{1,24})['‘’\"]")
NAME_TOKEN=re.compile(r'([가-힣A-Za-z][가-힣A-Za-z0-9·・\[\] -]{0,16}(?:횟수|수치|장부|문신|재료|탄|불|안|조망|얽힘|작품명|표식|스택))')

def _valid(x):
 x=x.strip(' -:')
 if len(x)<2 or EGO.search(x) or x in SIN: return False
 if any(x==z or x.startswith(z+' ') for z in ('피해','공격','스킬','체력','효과','보호막','턴','코인','정신력')): return False
 return True

def _scan_text(text):
 out={}
 for kind,vr in VERBS.items():
  for m in vr.finditer(text):
   a=max(0,m.start()-28); b=min(len(text),m.end()+28)
   window=text[a:b]
   toks=[t.group(1).strip() for t in TOKEN.finditer(window)] + [t.group(1).strip() for t in NAME_TOKEN.finditer(window)]
   for x in toks:
    if not _valid(x): continue
    d=out.setdefault(x,{'gain':0,'loss':0,'threshold':0,'transform':0,'evidence':[]})
    d[kind]+=1
    if len(d['evidence'])<2: d['evidence'].append(window.strip())
 return out

@lru_cache(maxsize=4)
def analyze(src):
 cat=json.load(open(src,encoding='utf8'))
 rows=[]
 for ident in cat.get('identities',[]):
  resources={}
  blocks=[]
  for p in ident.get('passives') or []: blocks.append(('passive',p.get('name',''),str(p.get('effect',''))))
  for s in ident.get('skills') or []: blocks.append(('skill',s.get('name',''),' '.join(map(str,s.get('effects',[])))))
  for s in ident.get('defenseSkills') or []: blocks.append(('defense',s.get('name',''),' '.join(map(str,s.get('effects',[])))))
  for src_type,name,text in blocks:
   if not text or EGO.search(text): continue
   for r,d in _scan_text(text).items():
    x=resources.setdefault(r,{'gain':0,'loss':0,'threshold':0,'transform':0,'evidence':[]})
    for k in ('gain','loss','threshold','transform'): x[k]+=d[k]
    for e in d['evidence']:
     if len(x['evidence'])<2: x['evidence'].append(f'{src_type}/{name}: {e}')
  # A candidate is retained only if at least one lifecycle signal exists.
  for r,d in resources.items():
   dims=sum(bool(d[k]) for k in ('gain','loss','threshold','transform'))
   d['lifecycle_coverage_pct']=dims*25
  rows.append({'identity_id':ident['id'],'identity_name':ident.get('name',''),'resources':resources})
 total=sum(len(r['resources']) for r in rows)
 full=sum(1 for r in rows for d in r['resources'].values() if d['lifecycle_coverage_pct']==100)
 avg=round(sum(d['lifecycle_coverage_pct'] for r in rows for d in r['resources'].values())/total,1) if total else 0
 return {'version':'0.5.12','catalog_identities':len(cat.get('identities',[])),'identities_with_candidates':sum(bool(r['resources']) for r in rows),'candidate_resources':total,'fully_structured_candidates':full,'average_structural_lifecycle_coverage_pct':avg,'rows':rows}

def write(src,out_json,out_md):
 r=analyze(src); json.dump(r,open(out_json,'w',encoding='utf8'),ensure_ascii=False,indent=2)
 lines=['# 특수자원 구현 커버리지 감사 v1 (0.5.12)','',f"- 카탈로그 인격: {r['catalog_identities']}개",f"- 후보 인격: {r['identities_with_candidates']}개",f"- 후보 자원/카운터: {r['candidate_resources']}개",f"- 4요소 모두 식별된 후보: {r['fully_structured_candidates']}개",f"- 구조적 lifecycle 평균 커버리지: **{r['average_structural_lifecycle_coverage_pct']}%**",'', '※ 이 %는 구현 정확도나 게임 내 완성도를 뜻하지 않고, 카탈로그 텍스트에서 획득/소모/임계값/변형 신호가 식별된 비율이다. E.G.O와 Sin 자원은 제외.','']
 for row in sorted(r['rows'],key=lambda x:-len(x['resources'])):
  if not row['resources']: continue
  lines.append(f"## {row['identity_name']} ({row['identity_id']})")
  for name,d in sorted(row['resources'].items(),key=lambda kv:(-kv[1]['lifecycle_coverage_pct'],kv[0])):
   lines.append(f"### {name} — {d['lifecycle_coverage_pct']}%")
   lines.append(f"- 획득 {d['gain']} / 소모·감소 {d['loss']} / 임계값 {d['threshold']} / 변형 {d['transform']}")
   for e in d['evidence']: lines.append(f"- 근거: {e}")
   lines.append('')
 open(out_md,'w',encoding='utf8').write('\n'.join(lines)); return r
