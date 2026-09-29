from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re, json
from pathlib import Path
from typing import Any, Iterable

class Cluster(str, Enum):
    ALL_TARGETS='all_targets'
    TARGET_COUNT='target_count'
    RANDOM_MULTI='random_multi_target'
    SAME_POLICY_MULTI='same_selector_multiple'
    FOCUSED_PART='focused_battle_part'
    CONDITIONAL_COUNT='conditional_target_count'
    TARGET_INHERIT='inherited_target_set'
    SINGLE_TARGET='single_target'
    UNRESOLVED='unresolved_multi_target'

class Match(str, Enum):
    EXISTING_SELECTOR='existing_target_selector'
    EXISTING_COUNT='existing_target_count'
    EXISTING_RANDOM='existing_random_selector'
    EXISTING_ACTION_TARGET='existing_action_target'
    EXISTING_PART_TARGET='existing_part_target'
    CONDITION_PLUS_SELECTOR='condition_plus_selector'
    UNRESOLVED='unresolved'

@dataclass(frozen=True)
class Hit:
    cluster: Cluster
    match: Match
    confidence: str
    evidence: tuple[str,...]
    missing: tuple[str,...]=()

ALL=re.compile(r'모든 아군|모든 적|각 대상|전체 아군|전체 적|모든 적군|모든 아군 인격')
COUNT=re.compile(r'\d+명당|\d+명|최대\s*\d+명|\d+명까지|\d+명에게')
RANDOM=re.compile(r'무작위|랜덤')
PART=re.compile(r'집중 전투|부위')
TARGET=re.compile(r'대상|아군|적에게|적 중|인격에게|타겟')
CONDITION=re.compile(r'처치|사망|피격|적중|흐트러|발동|조건|이상|미만|이하|이후|때')

def split_clauses(text:str)->list[str]:
    out=[]
    for b in re.split(r'\n+|\s+/-\s+', text or ''):
        b=b.strip(' /-•')
        if b:
            out.extend(x.strip() for x in re.split(r'(?<=다)\.\s+|(?<=음)\.\s+', b) if x.strip())
    return out

def classify(s:str)->tuple[Hit,...]:
    h=[]
    if ALL.search(s):
        h.append(Hit(Cluster.ALL_TARGETS,Match.EXISTING_SELECTOR,'high',('all-target marker',)))
    if COUNT.search(s):
        h.append(Hit(Cluster.TARGET_COUNT,Match.EXISTING_COUNT,'high',('explicit target count',)))
    if RANDOM.search(s) and (COUNT.search(s) or ALL.search(s)):
        h.append(Hit(Cluster.RANDOM_MULTI,Match.EXISTING_RANDOM,'high',('random + multi-target marker',)))
    if PART.search(s):
        h.append(Hit(Cluster.FOCUSED_PART,Match.EXISTING_PART_TARGET,'medium',('focused-battle part routing',)))
    if COUNT.search(s) and CONDITION.search(s):
        h.append(Hit(Cluster.CONDITIONAL_COUNT,Match.CONDITION_PLUS_SELECTOR,'medium',('condition + target-count',)))
    if not h:
        if TARGET.search(s):
            h.append(Hit(Cluster.UNRESOLVED,Match.UNRESOLVED,'low',('target marker without explicit multi-target semantics',),('selector semantics',)))
        else:
            h.append(Hit(Cluster.SINGLE_TARGET,Match.EXISTING_ACTION_TARGET,'high',('no multi-target marker; handled by action target',)))
    return tuple(h)

def audit_records(records:Iterable[dict[str,Any]])->dict[str,Any]:
    records=list(records); rows=[]; cc={x.value:0 for x in Cluster}; mc={x.value:0 for x in Match}; total=0
    for i,r in enumerate(records):
        for clause in split_clauses(r.get('source_text','')):
            total += 1
            for hit in classify(clause):
                cc[hit.cluster.value]+=1; mc[hit.match.value]+=1
                rows.append({'record_index':i,'identity_id':r.get('identity_id'),'identity_name':r.get('identity_name'),'passive_name':r.get('passive_name'),'text':clause,**asdict(hit),'cluster':hit.cluster.value,'match':hit.match.value})
    return {'record_count':len(records),'unique_source_texts':len({r.get('source_text','') for r in records}),'clause_count':total,'cluster_counts':cc,'match_counts':mc,'new_primitive_candidate':0,'rows':rows}

def main(src:Path,out_json:Path,out_md:Path):
    data=json.loads(src.read_text(encoding='utf-8'))
    records=[r for r in data['gaps'] if 'multi_target' in r.get('categories',[])]
    result=audit_records(records)
    out_json.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    c=result['cluster_counts']; m=result['match_counts']
    md=['# E31 Multi-Target Audit','',f"- Source: `GIMMICK_GAP_REPORT_v4.md.json`",f"- Records tagged `multi_target`: {result['record_count']}",f"- Unique source texts: {result['unique_source_texts']}",f"- Clause count: {result['clause_count']}",'','## Cluster counts']
    md += [f'- `{k}`: {v}' for k,v in c.items() if v]
    md += ['','## Primitive match counts'] + [f'- `{k}`: {v}' for k,v in m.items() if v]
    md += ['- `new_primitive_candidate`: 0','','## Interpretation','Multi-target is not a standalone identity Runtime. Explicit target counts are already represented by the existing target-selection count contract and `one_turn_solver_v29` target_count flow. All-target and random-N cases compose existing selectors with count. Focused-battle part routing is a target-resolution concern. Conditional multi-target clauses compose Condition + Target Selector. No new multi-target Primitive is introduced.','', 'Unresolved clauses are not claimed as implemented.']
    out_md.write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('record_count','unique_source_texts','clause_count','cluster_counts','match_counts')},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    main(root/'GIMMICK_GAP_REPORT_v4.md.json',root/'MULTI_TARGET_AUDIT_E31.json',root/'MULTI_TARGET_AUDIT_E31.md')
