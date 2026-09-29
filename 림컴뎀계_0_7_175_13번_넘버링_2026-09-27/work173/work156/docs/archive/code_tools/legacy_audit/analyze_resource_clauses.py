import json,re,collections
src='/tmp/e18/GIMMICK_GAP_REPORT_v4.md.json'
d=json.load(open(src))
rows=[x for x in d['gaps'] if 'resource_transform' in x.get('categories',[])]
patterns=collections.Counter(); examples=collections.defaultdict(list)
for r in rows:
    for line in re.split(r'\n+',r['source_text']):
        s=line.strip().lstrip('- ').strip()
        if not s: continue
        low=s.lower()
        p=[]
        if re.search(r'(피격|적중|처치|사망|공격 종료|턴 시작|턴 종료|합 승리|사용 시|공격 시작)',s): p.append('TRIGGER')
        if re.search(r'(얻음|획득|증가|부여|회복)',s): p.append('GAIN')
        if re.search(r'(소모|소비|사용|차감)',s): p.append('CONSUME')
        if re.search(r'(변경|전환|취급|간주)',s): p.append('TRANSFORM')
        if re.search(r'(0|없으면|없을 경우|없을 때)',s) and re.search(r'(자원|재료|충전|조망|예지안|장부|원한|탄환|횟수)',s): p.append('ZERO')
        if re.search(r'(소속|아군|인격)',s): p.append('AFFILIATION')
        if re.search(r'(가장 적|가장 낮|최저|최대|가장 높)',s): p.append('SELECTOR')
        if re.search(r'(무작위|랜덤)',s): p.append('RANDOM')
        if re.search(r'(\d+|하나당|마다|비례|×|당)',s): p.append('SCALING')
        if re.search(r'(피해량|피해|공격 레벨|방어 레벨|위력|코인 위력)',s) and re.search(r'(증가|감소|추가|더)',s): p.append('MODIFIER')
        if re.search(r'(스킬.*변경|변경.*스킬|스킬로)',s): p.append('SKILL')
        key='+'.join(p) if p else 'OTHER'
        patterns[key]+=1
        if len(examples[key])<3: examples[key].append((r['identity_name'],s))
print('rows',len(rows),'clauses',sum(patterns.values()))
for k,n in patterns.most_common():
 print(f'{k}\t{n}')
 for e in examples[k]: print('  ',e[0],':',e[1][:160])
