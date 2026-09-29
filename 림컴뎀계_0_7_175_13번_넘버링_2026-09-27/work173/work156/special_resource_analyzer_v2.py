"""Normalized audit for identity-specific 1-turn resources/counters.

v0.5.13: turns noisy text candidates into canonical resource records and
separates real resource-like counters from incidental phrases.
"""
from __future__ import annotations
import json,re
from functools import lru_cache

SIN={'분노','색욕','나태','탐식','우울','오만','질투'}
EGO=re.compile(r'E\.?G\.?O',re.I)
# Strong Korean resource nouns. Keep status counters such as "진동 횟수" out of
# this report unless they behave like an identity-owned resource.
RESOURCE_WORDS=(
    '새벽불','예지안','가속탄','작품명','생체 재료','문신','장부','얽힘','전투 기록',
    '혈흔','피의 잔재','못','검지의 지령','지령','광기','연성','기억','열기','불꽃나비의 관',
    '탄환','충전','호흡','진동','침잠','화상','파열','출혈','마비','속박','파편','스택'
)
LIFE={
 'gain':re.compile(r'(얻음|얻는다|획득|증가|부여|추가)',re.M),
 'loss':re.compile(r'(소모|감소|잃음|잃는다|차감|제거)',re.M),
 'threshold':re.compile(r'(\d+\s*(?:이상|이하)|수치가\s*0|없으면|있을\s*때|보유하고\s*있을\s*때|\d+\s*이상일\s*때)',re.M),
 'transform':re.compile(r'(변경|전환|교체|강화|변형|해금)',re.M),
}
NOISE=('피해','공격','스킬','체력','효과','보호막','턴','코인','정신력','속도','합','위력','피격','적중','남은 코인','수치 1당','감소한 수치')

def canon(token:str)->str:
    x=re.sub(r'^\s*(?:자신의|자신에게|자신은|자신이|대상의|대상에게|적의|적에게)\s*','',token.strip())
    x=re.sub(r'\s+',' ',x)
    x=x.strip(" -:[]()")
    # normalize common inflected/fragmented forms
    x=re.sub(r'^(?:소모|감소|증가|획득|보유|남은|최대)\s+','',x)
    if x.endswith(' 수치'): x=x[:-3].strip()
    if x.endswith(' 횟수') and x[:-3] in ('호흡','진동','화상','출혈','침잠','파열'): return ''
    return x

def _tokens(text):
    quoted=re.findall(r"['‘’\"]([^'‘’\"]{1,32})['‘’\"]",text)
    found=[]
    for q in quoted: found.append(q)
    for w in RESOURCE_WORDS:
        if w in text: found.append(w)
    return list(dict.fromkeys(found))

def _valid(x):
    x=canon(x)
    if not x or len(x)<2 or EGO.search(x) or x in SIN or any(n in x for n in NOISE): return False
    # avoid pure status names unless the text clearly treats it as a count/resource.
    if x in {'화상','진동','출혈','침잠','파열','마비','속박','호흡','충전'}: return False
    return True

def scan(text):
    out={}
    for token in _tokens(text):
        if not _valid(token): continue
        # Require lifecycle language in a local window, preventing unrelated quoted names.
        positions=[m.start() for m in re.finditer(re.escape(token),text)]
        d=out.setdefault(token,{'gain':0,'loss':0,'threshold':0,'transform':0,'evidence':[],'mentions':0})
        d['mentions']+=len(positions)
        for pos in positions:
            window=text[max(0,pos-100):min(len(text),pos+120)]
            hit=False
            for k,rx in LIFE.items():
                n=len(rx.findall(window)); d[k]+=n; hit |= n>0
            if hit and len(d['evidence'])<3: d['evidence'].append(window.strip())
    return {k:v for k,v in out.items() if any(v[x] for x in LIFE)}

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
        for typ,name,text in blocks:
            if not text or EGO.search(text): continue
            for r,d in scan(text).items():
                x=resources.setdefault(r,{'gain':0,'loss':0,'threshold':0,'transform':0,'evidence':[],'mentions':0,'sources':set()})
                for k in ('gain','loss','threshold','transform','mentions'): x[k]+=d[k]
                x['sources'].add(f'{typ}/{name}')
                for e in d['evidence']:
                    if len(x['evidence'])<3: x['evidence'].append(f'{typ}/{name}: {e}')
        for d in resources.values():
            d['lifecycle_coverage_pct']=25*sum(bool(d[k]) for k in LIFE)
            d['source_count']=len(d['sources']); del d['sources']
        rows.append({'identity_id':ident['id'],'identity_name':ident.get('name',''),'resources':resources})
    allr=[d for r in rows for d in r['resources'].values()]
    # Confidence: 4 lifecycle dimensions, repeated mentions, and multiple source blocks.
    for d in allr:
        score=d['lifecycle_coverage_pct']
        if d['mentions']>=3: score+=10
        if d['source_count']>=2: score+=10
        d['confidence_pct']=min(100,score)
    return {'version':'0.5.13','catalog_identities':len(cat.get('identities',[])),
            'identities_with_candidates':sum(bool(r['resources']) for r in rows),
            'candidate_resources':len(allr),'fully_structured_candidates':sum(d['lifecycle_coverage_pct']==100 for d in allr),
            'high_confidence_candidates':sum(d['confidence_pct']>=80 for d in allr),
            'average_lifecycle_coverage_pct':round(sum(d['lifecycle_coverage_pct'] for d in allr)/len(allr),1) if allr else 0,
            'rows':rows}

def write(src,out_json,out_md):
    r=analyze(src)
    json.dump(r,open(out_json,'w',encoding='utf8'),ensure_ascii=False,indent=2)
    lines=['# 특수자원 정규화 감사 v2 (0.5.13)','',f"- 인격: {r['catalog_identities']}개",f"- 후보 인격: {r['identities_with_candidates']}개",f"- 정규화 후보: **{r['candidate_resources']}개**",f"- 4요소 모두 식별: {r['fully_structured_candidates']}개",f"- 고신뢰 후보(80+): **{r['high_confidence_candidates']}개**",f"- 평균 lifecycle 식별률: **{r['average_lifecycle_coverage_pct']}%**",'', '※ 자동 추출 감사이며 실제 게임 기믹의 확정 목록이 아니다. E.G.O/Sin 자원과 일반 전투 상태이상 자체는 제외한다.','']
    for row in sorted(r['rows'],key=lambda x:-len(x['resources'])):
        if not row['resources']: continue
        lines.append(f"## {row['identity_name']} ({row['identity_id']})")
        for name,d in sorted(row['resources'].items(),key=lambda kv:(-kv[1]['confidence_pct'],kv[0])):
            lines.append(f"### {name} — 신뢰도 {d['confidence_pct']}% / lifecycle {d['lifecycle_coverage_pct']}%")
            lines.append(f"- 획득 {d['gain']} / 소모·감소 {d['loss']} / 임계값 {d['threshold']} / 변형 {d['transform']} / 언급 {d['mentions']} / 출처 블록 {d['source_count']}")
            for e in d['evidence']: lines.append(f"- 근거: {e}")
            lines.append('')
    open(out_md,'w',encoding='utf8').write('\n'.join(lines))
    return r
