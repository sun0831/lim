import json,re,collections
D=json.load(open('/tmp/e22/RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json'))
cs=[x for x in D['clauses'] if x['kind']=='resource_consume']

def cls(t):
 if '누적으로' in t and '소모할 때마다' in t: return 'cumulative_spend_reward'
 if '소모하면' in t or '소모했다면' in t or '소모할 때' in t or '소모하는 스킬' in t or '소모하는 코인' in t or '소모하는 기본 공격' in t or '마지막 탄환을 소모' in t or '소모할 경우' in t or '소모하였' in t:
  # effects/transform after consumption
  if '변경' in t or '변환' in t or '얻음' in t or '부여' in t or '증가' in t or '추가 피해' in t or '피해량 +' in t or '위력 +' in t or '회복' in t or '발동' in t or '재장전' in t or '소모하여' in t:
   return 'consume_triggered_effect'
 if '소모' in t and ('전부 소모' in t or '소모하고' in t or '소모하여' in t):
  return 'consume_with_direct_effect'
 if '소모' in t and ('적용' in t or '취급' in t or '경우에도' in t or '없는 경우' in t):
  return 'consume_condition_or_fallback'
 return 'other_consumption'

cnt=collections.Counter();
for x in cs:
 c=cls(x['text']);cnt[c]+=1;x['e22_class']=c
print(cnt)
for c in cnt:
 print('\n###',c,cnt[c])
 for i,x in enumerate([z for z in cs if z['e22_class']==c],1): print(i,x['identity_name'],'|',x['text'])
