"""Skill-text parsing for the v29 one-turn calculator.

Extracted from the solver as a behavior-preserving C-phase split.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

STATUS={"출혈":"Bleed","화상":"Burn","파열":"Rupture","침잠":"Sinking","진동":"Tremor","호흡":"Poise","충전":"Charge","속박":"Bind","취약":"Damage Taken Up","못":"Nails","광신":"광신"}

@dataclass
class ParseReport:
    supported: List[str]
    unsupported: List[str]

class SkillTextParserV19:
    """Conservative parser for high-frequency skill text patterns."""
    SPECIAL_RESOURCE_NAMES = {
        "새벽불", "불꽃나비의 관", "지령", "작품명", "생체 재료", "섬궁",
        "탄환", "얽힘", "흑풍마각월참", "마탄", "천구성도", "문신", "장부",
        "가속탄", "예지", "예지안", "처분", "각력【오】", "적진 주파", "앙갚음 장부 [히스클리프]", "원한 문신", "로직 아틀리에", "짝패", "열기", "지령의 가호", "각력【오】", "적진 주파", "폐장 - 설치미술 제 1호 ", "내 헤어쿠포오오오온!!!!", "새벽녘", "즉결처형", "원한 스탬핑",
    }
    coin_re=re.compile(r'(?:(\d+)코인)?\s*\[(적중시|앞면 적중시|뒷면 적중시)\]\s*(.+)', re.S)
    def parse(self, raw_effects: Sequence[str], coin_count: int) -> tuple[Dict[str,Any], ParseReport]:
        on_use=[]; last_coin_reuse_rules=[]; last_coin_damage_rules=[]; kill_reuse_rules=[]; pending_reuse_hit_effects=[]; added_coin_rules=[]; pending_added_coin_rule=None; pending_resource_damage_context=None
        coin_target_policies=[None for _ in range(coin_count)]
        coins=[{"effects":[],"heads_effects":[],"tails_effects":[],"damage_bonus":0.0,"damage_conditions":[],"crit_damage_bonus":0.0,"stagger_damage_ratio":0.0,"final_power_bonus":0,"unbreakable":False,"ammo_spend":0,"resource_cost":{},"resource_cost_max":{},"resource_cost_all":[],"reuse_rules":[]} for _ in range(coin_count)]
        supported=[]; unsupported=[]
        pending_condition=None
        for text in raw_effects or []:
            t=str(text).strip()
            # Catalog exports sometimes prefix an entire clause with a Markdown-style
            # bullet (`- `). The bullet is formatting, not part of the game rule.
            # Keep numeric continuation lines such as `- 1당 ...` intact because
            # those are used by the split-resource context parser below.
            t=re.sub(r'^[-–—]\s+(?=(?:\[|자신|대상|메인\s*타겟|적|파티|생존|이\s*스킬|이\s*코인|코인|피해|피격|현재|아군))', '', t)
            m=self.coin_re.search(t)
            # Carry a resource context split across catalog bullet lines, e.g.
            # `불꽃나비의 관 수치에 따라` followed by `- 1당, 피해량 +2%`.
            ctx = re.search(r'^([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,40}?)\s*(?:수치|횟수|위력)?\s*에\s*따라\s*$', t)
            if ctx:
                pending_resource_damage_context = re.sub(r'^\[(?:사용시|사용 전|사용전)\]\s*', '', ctx.group(1)).strip(' ,')
                supported.append(t); continue
            if pending_resource_damage_context and re.match(r'^[-–—]\s*\d+\s*당,?\s*피해량\s*\+?\s*\d+(?:\.\d+)?%', t):
                pm = re.search(r'^[-–—]\s*(\d+)\s*당,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%', t)
                capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', t)
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_per','resource':pending_resource_damage_context,'target':'self','per':int(pm.group(1)),'amount':float(pm.group(2))/100,'max':float(capm.group(1))/100 if capm else 999999}})
                supported.append(t); pending_resource_damage_context=None; continue
            if t and not t.startswith(('-', '–', '—')):
                pending_resource_damage_context = None

            # Explicit per-coin target roles. Exact user coin_target_ids override these.
            tm=re.match(r'^(\d+)코인\s*(.*)$', t)
            if tm:
                ci=int(tm.group(1))-1; body=tm.group(2)
                if 0 <= ci < coin_count:
                    if re.search(r'이\s*코인에는\s*메인\s*타겟만\s*피해', body) or re.search(r'이\s*코인은\s*1명의\s*대상에게만\s*적중함\s*\(메인\s*타겟\s*우선', body):
                        coin_target_policies[ci]='single_main'; supported.append(t); continue
                    if re.search(r'이\s*코인에는\s*서브\s*타겟만\s*피해', body):
                        coin_target_policies[ci]='sub'; supported.append(t); continue
            # Action-level status changes tied to Clash results.
            cmatch = re.search(r'^\[(합 승리시|합 패배시)\]\s*(.+)$', t)
            if cmatch:
                eff = self._status_effect(cmatch.group(2))
                if eff:
                    eff = dict(eff)
                    eff['target'] = 'self' if '자신' in cmatch.group(2) else 'enemy'
                    target_list = 'effects_on_clash_win' if cmatch.group(1) == '합 승리시' else 'effects_on_clash_lose'
                    on_use.append({'type': target_list, 'effect': eff})
                    supported.append(t); continue
            # Catalogs often split a Korean conditional sentence across bullets:
            # "속도가 높으면," followed by "- 코인 위력 +1". Carry that context
            # to the immediately following modifier instead of treating it as
            # unrelated prose.
            if re.search(r'자신의\s*속도가\s*대상보다\s*(?:높|빠르).*?면\s*,?$',t):
                pending_condition={"type":"speed_difference_gte","value":1}
                supported.append(t); continue
            if re.search(r'자신의\s*속도가\s*대상보다\s*(?:낮|느리).*?면\s*,?$',t):
                pending_condition={"type":"speed_difference_lte","value":-1}
                supported.append(t); continue
            # Coin-local modifiers/resource consumption.
            cm=re.search(r'^(\d+)코인\s*(.*)$',t,re.S)
            if cm:
                ci=int(cm.group(1))-1; body0=cm.group(2)
                if 0 <= ci < coin_count:
                    q = coins[ci]
                    # Source-backed identity rule: LCCB 대리 료슈 S3's third coin
                    # doubles both Tremor and Rupture potency/count when the coin
                    # is a critical hit. Store this on the coin definition so the
                    # later status clauses on the same coin inherit it; do not
                    # create a global/identity-wide multiplier.
                    if re.search(r'진동\s*,?\s*파열\s*의?\s*위력과\s*횟수가\s*2배로\s*부여됨', body0):
                        q['keyword_application_multipliers'] = {'Tremor': {'potency': 2, 'count': 2}, 'Rupture': {'potency': 2, 'count': 2}, '_condition': {'type': 'critical_hit'}}
                        supported.append(t); continue
                    # Source-backed dynamic Tremor application patterns.
                    # These are only enabled for exact identity-text clauses; no
                    # generic inference is made from arbitrary Tremor wording.
                    mself = re.search(r'\(자신의\s*진동\s*횟수\s*/\s*2\)만큼\s*진동\s*부여\s*\(최대\s*(\d+)\)', body0)
                    if mself:
                        q['effects'].append({'type':'tremor_apply_from_self_count_div', 'name':'Tremor', 'target':'enemy', 'divisor':2, 'cap':int(mself.group(1))})
                        supported.append(t); continue
                    if re.search(r'자신의\s*진동\s*횟수를\s*전부\s*소모하여,?\s*소모한\s*값만큼\s*진동\s*부여', body0):
                        capm=re.search(r'진동\s*부여\s*\.?\s*\(최대\s*(\d+)\)', body0)
                        q['effects'].append({'type':'tremor_apply_from_self_count_all', 'name':'Tremor', 'target':'enemy', 'cap':int(capm.group(1)) if capm else None})
                        continue
                    # Source-backed conditional Tremor Burst forms.
                    mcond = re.search(r'대상의\s*진동\s*횟수가\s*(\d+)\s*이상.*?진동\s*폭발\s*\.\s*대상의\s*진동\s*횟수\s*(\d+)\s*감소', body0)
                    if mcond:
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'status','name':'Tremor','target':'enemy','count_gte':int(mcond.group(1))},'count_cost':int(mcond.group(2))}); supported.append(t); continue
                    mcond = re.search(r'정신력이\s*있는\s*대상이면,\s*진동\s*폭발\s*\.\s*진동\s*횟수\s*(\d+)\s*감소', body0)
                    if mcond:
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'target_has_sp'},'count_cost':int(mcond.group(1))}); supported.append(t); continue
                    mcond = re.search(r'대상에게\s*속박이\s*있으면,\s*진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소', body0)
                    if mcond:
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'status','name':'Bind','target':'enemy','count_gte':1},'count_cost':int(mcond.group(1))}); supported.append(t); continue
                    mcond = re.search(r'대상의\s*진동\s*위력이\s*(\d+)\s*이상.*?진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소', body0)
                    if mcond:
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'status','name':'Tremor','target':'enemy','potency_gte':int(mcond.group(1))},'count_cost':int(mcond.group(2))}); supported.append(t); continue
                    mcond = re.search(r'완성되어가는\s*교본이\s*있거나\s*대상에게\s*결투\s*고조가\s*있으면,\s*진동\s*폭발\s*(\d+)?회?\s*\.\s*진동\s*횟수\s*(\d+)\s*감소', body0)
                    if mcond:
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'or','conditions':[{'type':'resource_gte','resource':'완성되어가는 교본','value':1},{'type':'status','name':'결투 고조','target':'enemy','count_gte':1}]},'burst_count':int(mcond.group(1) or 1),'count_cost':int(mcond.group(2))}); supported.append(t); continue
                    if '이 스킬에서 고독을 부여할 때' in body0 and '대신 진동 폭발' in body0:
                        cm=re.search(r'진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소',body0)
                        q['effects'].append({'type':'tremor_burst_replacement','name':'Tremor','target':'enemy','replacement_status':'고독','condition':{'type':'loneliness_present_current_or_next_turn'},'count_cost':int(cm.group(1)) if cm else 0}); supported.append(t); continue
                    if '추가된 코인 적중 시 진동 폭발' in body0:
                        cm=re.search(r'진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소',body0)
                        q['effects'].append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'added_coin_hit'},'count_cost':int(cm.group(1)) if cm else None}); supported.append(t); continue
                    # Per-coin identity-specific resource spending.
                    for resource in sorted(self.SPECIAL_RESOURCE_NAMES, key=len, reverse=True):
                        rm=re.search(re.escape(resource)+r'\s*(?:횟수|위력)?\s*(\d+)\s*소모',body0)
                        if rm:
                            coins[ci]['resource_cost'][resource]=int(rm.group(1)); supported.append(t); break
                    else:
                        rm=None
                    if rm:
                        continue
                    am=re.search(r'탄환\s*(\d+)\s*소모',body0)
                    if am: coins[ci]['ammo_spend']=int(am.group(1)); supported.append(t); continue
                    # Coin reuse: declarative, state-checked immediately after the coin hits.
                    # Event-sensitive conditions (critical/front-hit) are kept as
                    # runtime conditions so the same rule can be reused by the
                    # deterministic and generated-action executors.
                    # Charge Potency conditional reuse must precede the generic
                    # "this coin reuse" pattern, otherwise the latter erases the
                    # resource condition into an unconditional rule.
                    rpm=re.search(r"자신의\s*충전\s*위력(?:이|가|은|는)?\s*(\d+)\s*이상.*?이\s*코인\s*재사용", body0)
                    if rpm:
                        q["reuse_rules"].append({"condition":{"type":"resource_gte","resource":"충전 위력","value":int(rpm.group(1))},"max_reuses":1,"mode":"same"})
                        supported.append(t); continue
                    reuse_patterns = [
                        (r"이 코인 재사용\s*\(최대\s*(\d+)회\)", {"type":"always"}, "same"),
                        (r"이 코인 재사용\s*\(스킬당\s*(?:최대\s*)?(\d+)회\s*(?:재사용\s*)?가능\)", {"type":"always"}, "same"),
                        (r"이 코인 재사용\s*\(스킬당\s*(?:최대\s*)?(\d+)회\s*(?:발동\s*)?\)", {"type":"always"}, "same"),
                    ]
                    # Critical/front-hit reuse forms. More specific combinations
                    # must be matched before the single-condition forms.
                    rm = re.search(r"(?:\[)?크리티컬\s*앞면\s*적중\s*시(?:\])?.*?이 코인 재사용.*?(?:최대\s*)?(\d+)회", body0)
                    if rm:
                        q["reuse_rules"].append({"condition":{"type":"and","conditions":[{"type":"critical_hit"},{"type":"front_hit"}]},"max_reuses":int(rm.group(1)),"mode":"same"})
                        supported.append(t); continue
                    rm = re.search(r"(?:\[)?크리티컬\s*적중\s*시(?:\])?.*?이 코인 재사용.*?(?:최대\s*)?(\d+)회", body0)
                    if rm:
                        q["reuse_rules"].append({"condition":{"type":"critical_hit"},"max_reuses":int(rm.group(1)),"mode":"same"})
                        supported.append(t); continue
                    rm = re.search(r"(?:\[)?앞면\s*적중\s*시(?:\])?.*?이 코인 재사용.*?(?:최대\s*)?(\d+)회", body0)
                    if rm:
                        q["reuse_rules"].append({"condition":{"type":"front_hit"},"max_reuses":int(rm.group(1)),"mode":"same"})
                        supported.append(t); continue
                    for rp, cond, mode in reuse_patterns:
                        rm=re.search(rp, body0)
                        if rm:
                            q["reuse_rules"].append({"condition":cond,"max_reuses":int(rm.group(1)),"mode":mode})
                            supported.append(t); break
                    else:
                        # Explicit probability + negative-status bonus form must be
                        # matched before the simpler probability-only form.
                        rm=re.search(r'(\d+(?:\.\d+)?)%\s*확률로\s*코인\s*재사용.*?(?:부정적인\s*효과\s*1개당\s*재사용\s*확률\s*\+\s*(\d+(?:\.\d+)?)%).*?(?:스킬당\s*최대\s*(\d+)회)', body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"always"},"probability":float(rm.group(1))/100,"negative_status_bonus":float(rm.group(2))/100,"max_reuses":int(rm.group(3)),"mode":"same","original_probability":float(rm.group(1))/100,"high_point_assumption":True}); supported.append(t); continue
                        rm=re.search(r'(\d+(?:\.\d+)?)%\s*확률로\s*코인\s*재사용', body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"always"},"probability":float(rm.group(1))/100,"max_reuses":1,"mode":"same","original_probability":float(rm.group(1))/100,"high_point_assumption":True}); supported.append(t); continue
                        # Common conditional reuse forms.
                        rm=re.search(r"(?:자신의\s*)?속도가\s*10\s*이상.*?코인\s*(?:1회\s*)?재사용", body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"speed_gte","value":10},"max_reuses":1,"mode":"same"}); supported.append(t); continue
                        rm2=re.search(r"자신의\s*충전\s*위력(?:이|가|은|는)?\s*(\d+)\s*이상.*?코인\s*(?:1회\s*)?재사용", body0)
                        if rm2:
                            q['reuse_rules'].append({'condition':{'type':'resource_gte','resource':'충전 위력','value':int(rm2.group(1))},'max_reuses':1,'mode':'same'})
                            supported.append(t); continue
                        rm=re.search(r"자신의\s*(호흡|충전)(?:\s*횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?코인\s*(?:1회\s*)?재사용", body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"poise_gte" if rm.group(1)=="호흡" else "charge_gte","value":int(rm.group(2))},"max_reuses":1,"mode":"same"}); supported.append(t); continue
                        rm=re.search(r"대상의\s*(출혈|화상|破裂|파열|침잠|진동)\s*(\d+)\s*이상.*?코인\s*(?:1회\s*)?재사용", body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"status","name":STATUS.get(rm.group(1),rm.group(1)),"target":"enemy","potency_gte":int(rm.group(2))},"max_reuses":1,"mode":"same"}); supported.append(t); continue
                        rm=re.search(r"대상의\s*현재\s*체력이\s*최대\s*체력의\s*(\d+(?:\.\d+)?)%\s*(?:미만|이하).*?코인\s*(?:1회\s*)?재사용", body0)
                        if rm:
                            q["reuse_rules"].append({"condition":{"type":"hp_pct_lte","value":float(rm.group(1))},"max_reuses":1,"mode":"same"}); supported.append(t); continue
                    if q["reuse_rules"] and ("재사용" in body0):
                        continue
                    # A coin-local stagger condition is a timing-sensitive modifier,
                    # not a flat coin bonus. Keep it as a skill condition so the
                    # engine evaluates the target state immediately before that coin.
                    smd=re.search(r'대상.*?흐트러짐\s*상태(?:면|라면).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if smd:
                        on_use.append({"type":"_skill_condition_marker","condition":{"type":"enemy_staggered"},"damage_bonus":float(smd.group(1))/100})
                        supported.append(t); continue
                    scm=re.search(r'대상.*?흐트러짐\s*상태(?:면|라면).*?크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if scm:
                        on_use.append({"type":"_skill_condition_marker","condition":{"type":"enemy_staggered"},"crit_damage_bonus":float(scm.group(1))/100})
                        supported.append(t); continue
                    # Attack-weight gap damage: when fewer targets are hit than the
                    # skill's attack weight, each missing target grants a flat damage multiplier.
                    awm=re.search(r'이\s*스킬\s*공격\s*가중치보다\s*낮은\s*공격\s*대상\s*1\s*당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if awm:
                        on_use.append({"type":"_skill_damage_condition_marker","condition":{"type":"attack_weight_gap_damage","amount":float(awm.group(1))/100.0}})
                        supported.append(t); continue
                    # Exact one-target scaling used by several weight-based skills.
                    one_target=re.search(r'공격\s*대상이\s*1(?:명|개)?(?:\s*\(.*?\))?\s*일\s*때.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if one_target:
                        on_use.append({"type":"_skill_damage_condition_marker","condition":{"type":"target_count_eq","value":1,"amount":float(one_target.group(1))/100.0}})
                        supported.append(t); continue
                    # Explicitly targeted final-coin damage modifiers. The source
                    # names the current trigger coin but the recipient is the skill's
                    # final coin, so never store these on q.damage_bonus.
                    lcm = re.search(r'(?:\[(앞면 적중시|합 승리 후 적중시|적중시)\])?\s*마지막\s*코인(?:의)?\s*피해량\s*(?:\+|)(\d+(?:\.\d+)?)%\s*', t)
                    if lcm and '마지막 코인' in t:
                        trigger = lcm.group(1) or '적중시'
                        cond = None if trigger == '적중시' else {'type': 'front_hit' if trigger == '앞면 적중시' else 'clash_result', 'value': 'win' if trigger == '합 승리 후 적중시' else None}
                        last_coin_damage_rules.append({'condition': cond, 'trigger_coin_index': ci+1, 'amount': float(lcm.group(2))/100.0})
                        supported.append(t); continue
                    # Conditional named-resource scaling on the final coin.
                    # Example: '대상의 파열이 15 이상이면, 딜리버리 캐리어 - 싱클레어 1 당
                    # 마지막 코인의 피해량 +4% (최대 120%)'.  The target condition and
                    # named resource must both survive; flattening this into an unconditional
                    # final-coin bonus silently over-applies the effect.
                    fcm = re.search(
                        r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)(?:이|가|은|는)?\s*(?:위력|수치)?\s*(?P<threshold>\d+)\s*이상.*?'
                        r'(?P<resource>[가-힣A-Za-z0-9【】\[\]/・・ -]{1,40}?)\s*(?:수치|횟수|위력)?\s*(?:1\s*)?당\s*마지막\s*코인의\s*피해량\s*\+(?P<amount>\d+(?:\.\d+)?)%.*?'
                        r'(?:최대\s*(?P<cap>\d+(?:\.\d+)?)%)', t)
                    if fcm:
                        threshold = int(fcm.group('threshold'))
                        resource = fcm.group('resource').strip(' ,')
                        cap = float(fcm.group('cap')) / 100.0 if fcm.group('cap') else 999999
                        last_coin_damage_rules.append({
                            'condition': {'type':'status','name':STATUS[fcm.group(1)],'target':'enemy','potency_gte':threshold},
                            'status_scaling': {'name':resource,'per':1,'amount':float(fcm.group('amount'))/100.0,'max':cap,'use_potency':False}
                        })
                        supported.append(t); continue
                    # Same final-coin target with an explicit self-status scaling,
                    # e.g. 발각 수치 1당 마지막 코인의 피해량 +5% (최대 15%).
                    lcm = re.search(r'자신에게\s*발각(?:\[.*?\])?이\s*있으면.*?수치\s*1당.*?마지막\s*코인의\s*피해량\s*\+(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%', t)
                    if lcm:
                        last_coin_damage_rules.append({'condition': {'type':'status','name':'발각','target':'self','count_gte':1}, 'status_scaling': {'name':'발각','per':1,'amount':float(lcm.group(1))/100.0,'max':float(lcm.group(2))/100.0}})
                        supported.append(t); continue
                    # Resource-dependent coin-local damage. This must remain
                    # conditional; flattening it into `damage_bonus` makes the
                    # modifier active even when the resource is absent.
                    tm=re.search(r'눈물\s*벼리기를\s*보유하였거나\s*이\s*코인에서\s*소모하였다면,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if tm:
                        q['damage_conditions'].append({'condition':{'type':'resource_held_or_consumed_this_coin','resource':'눈물 벼리기'},'amount':float(tm.group(1))/100.0})
                        supported.append(t); continue
                    xcm = re.search(r'크리티컬\s*피해량\s*\+\s*\(\s*자신의\s*호흡(?:\s*위력)?\s*\+\s*(?:대상의|메인\s*타겟의)\s*(화상|출혈|침잠|파열|진동)(?:\s*위력)?\s*\)\s*%', body0)
                    if xcm:
                        capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', body0)
                        on_use.append({'type':'_skill_condition_marker','condition':{'type':'cross_status_crit_damage_per','self_status':'Poise','enemy_status':STATUS.get(xcm.group(1),xcm.group(1)),'per':1,'amount':0.01,'max':float(capm.group(1))/100 if capm else 999999,'coin_index':ci+1},'effect':'crit_damage_bonus'})
                        supported.append(t); continue
                    # Cross-scope Poise + target-status critical damage must be
                    # handled before the generic 'critical damage +X%' matcher.
                    xcm = re.search(r'자신의\s*호흡(?:\s*위력)?\s*\+\s*(?:대상의|메인\s*타겟의)\s*(화상|출혈|침잠|파열|진동)(?:\s*위력)?\s*\)?\s*1\s*당\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if xcm:
                        capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', body0)
                        on_use.append({'type':'_skill_condition_marker','condition':{'type':'cross_status_crit_damage_per','self_status':'Poise','enemy_status':STATUS.get(xcm.group(1),xcm.group(1)),'per':1,'amount':float(xcm.group(2))/100,'max':float(capm.group(1))/100 if capm else 999999,'coin_index':ci+1},'effect':'crit_damage_bonus'})
                        supported.append(t)
                    # Reused-coin conditional damage must retain both the reuse/front-hit
                    # trigger and the target-status threshold; otherwise the generic damage
                    # matcher turns a conditional +50% into an unconditional flat bonus.
                    rm=re.search(r'\[재사용\s*앞면\s*적중\s*시\]\s*대상의\s*(출혈|화상|파열|침잠|진동)(?:이|가|은|는)?\s*(?:위력|수치)?\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if rm:
                        q['damage_conditions'].append({'condition':{'type':'and','conditions':[{'type':'reuse_hit'},{'type':'front_hit'},{'type':'status','name':STATUS[rm.group(1)],'target':'enemy','potency_gte':int(rm.group(2))}]},'amount':float(rm.group(3))/100})
                        supported.append(t); continue
                    # Cross-scope status sum damage must remain a dynamic calculation
                    # rather than becoming a flat coin bonus.
                    csm=re.search(r'대상의\s*\((파열|출혈|화상|침잠|진동)\s*위력\s*\+\s*자신의\s*(호흡)\s*위력\s*\)\s*당\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if csm:
                        q['damage_conditions'].append({'condition':{'type':'cross_status_sum_per','self_status':'Poise','enemy_status':STATUS[csm.group(1)],'per':1,'amount':float(csm.group(3))/100,'max':float(csm.group(4))/100 if csm.group(4) else 999999}})
                        supported.append(t); continue
                    # Coin-local OR damage condition combining target HP and a status,
                    # e.g. `대상(본체)의 체력이 25% 이하거나 대상에게 현혹이 있으면, 피해량 +60%`.
                    hp_or_status = re.search(
                        r'대상(?:\(본체\))?의\s*체력(?:이|가|은|는)?\s*(\d+(?:\.\d+)?)%\s*(미만|이하|이상|초과)\s*거나\s*대상에게\s*([^,]+?)\s*(?:이|가)\s*있으면,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%',
                        body0)
                    if hp_or_status:
                        op = hp_or_status.group(2)
                        hp_cond = {'type':'enemy_hp_pct_lte' if op in ('미만','이하') else 'enemy_hp_pct_gte',
                                   'value':float(hp_or_status.group(1)),
                                   'strict':op in ('미만','초과')}
                        status_cond = {'type':'status','name':hp_or_status.group(3).strip(),'target':'enemy','count_gte':1}
                        q['damage_conditions'].append({'condition':{'type':'or','conditions':[hp_cond,status_cond]},'amount':float(hp_or_status.group(4))/100})
                        supported.append(t); continue
                    # Coin-local target threshold scaling, e.g. `대상에게 못이 5 이상 있으면, 피해량 +70%`.
                    threshold_damage = re.search(r'대상에게\s*([가-힣A-Za-z0-9【】\[\]/・・ -]+?)\s*(?:이|가)\s*(\d+)\s*이상\s*있으면,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%', body0)
                    if threshold_damage:
                        raw_name=threshold_damage.group(1).strip(' ,')
                        q['damage_conditions'].append({'condition':{'type':'status','name':raw_name,'target':'enemy','potency_gte':int(threshold_damage.group(2))},'amount':float(threshold_damage.group(3))/100})
                        supported.append(t); continue
                    # Compound unlock-stage text: preserve the damage scaling part as
                    # dynamic even though the separate coin-power transformation is not
                    # represented by this damage-condition field.
                    unlock_damage = re.search(r'해금\s*단계\s*1당,?\s*이\s*코인의\s*위력\s*\+\s*\d+\s*,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%', body0)
                    if unlock_damage:
                        q['damage_conditions'].append({'condition':{'type':'named_stack_per','name':'해금 단계','target':'self','per':1,'amount':float(unlock_damage.group(1))/100,'max':float(unlock_damage.group(2))/100}})
                        supported.append(t); continue
                    # Coin-local target negative-effect count scaling must stay dynamic.
                    nm=re.search(r'(?:대상의\s*)?부정적인\s*효과\s*(\d+)\s*개당,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if nm:
                        q['damage_conditions'].append({'condition':{'type':'negative_status_count_per','target':'enemy','per':int(nm.group(1)),'amount':float(nm.group(2))/100,'max':float(nm.group(3))/100 if nm.group(3) else 999999}})
                        supported.append(t); continue
                    # Coin-local target named status scaling must not fall through
                    # to the flat damage matcher.
                    named_coin=re.search(r'대상의\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if named_coin:
                        raw_name=named_coin.group(1).strip(' ,')
                        if raw_name not in {'부정적인 효과'}:
                            q['damage_conditions'].append({'condition':{'type':'named_stack_per','name':raw_name,'target':'enemy','per':int(named_coin.group(2) or 1),'amount':float(named_coin.group(3))/100,'max':float(named_coin.group(4))/100 if named_coin.group(4) else 999999}})
                            supported.append(t); continue
                    # Coin-local consumed-ammo scaling: the source expresses the
                    # multiplier as `(소모한 탄환 x N)%`, so it must read actual
                    # current-action consumption rather than remaining ammo.
                    ammo_scaled = re.search(r'피해량\s*\+?\s*\(\s*소모한\s*탄환\s*x\s*(\d+(?:\.\d+)?)\s*\)%', body0)
                    if ammo_scaled:
                        q['damage_conditions'].append({'condition':{'type':'resource_consumed_sum_per','resources':['탄환'],'per':1,'amount':float(ammo_scaled.group(1))/100}})
                        supported.append(t); continue
                    # Coin-local target-slower speed-difference scaling.
                    speed_lower = re.search(r'대상의\s*속도가\s*자신보다\s*느리면,?\s*대상과의\s*속도\s*차이\s*1\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if speed_lower:
                        q['damage_conditions'].append({'condition':{'type':'speed_difference_per','direction':'lower','per':1,'amount':float(speed_lower.group(1))/100,'max':float(speed_lower.group(2))/100 if speed_lower.group(2) else 999999}})
                        supported.append(t); continue
                    # Coin-local conditional target-status threshold, e.g.
                    # `대상의 화상이 6 이상이면, 피해량 +50%`.
                    threshold_coin = re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)(?:이|가|은|는)?\s*(?:위력|수치|횟수)?\s*(\d+)\s*이상.*?피해량\s*\+?\s*(\d+(?:\.\d+)?)%', body0)
                    if threshold_coin:
                        q['damage_conditions'].append({'condition':{'type':'status_threshold','name':STATUS[threshold_coin.group(1)],'target':'enemy','field':'potency','value':int(threshold_coin.group(2))},'amount':float(threshold_coin.group(3))/100})
                        supported.append(t); continue
                    target_hp_coin = re.search(r'(?:대상|메인\s*타겟).*?(?:현재\s*)?체력(?:이|가|은|는)?\s*(\d+(?:\.\d+)?)%\s*(미만|이하|이상|초과).*?피해량\s*(?:\+\s*)?(\d+(?:\.\d+)?)%\s*(?:증가)?', body0)
                    if target_hp_coin:
                        op=target_hp_coin.group(2)
                        q['damage_conditions'].append({'condition':{'type':'enemy_hp_pct_lte' if op in ('미만','이하') else 'enemy_hp_pct_gte','value':float(target_hp_coin.group(1)),'strict':op in ('미만','초과')},'amount':float(target_hp_coin.group(3))/100})
                        supported.append(t); continue
                    # Coin-local speed/status scaling.
                    speed_status_coin = re.search(r'자신의\s*속도가\s*대상보다\s*빠르면,?\s*\(대상과의\s*속도\s*차이\s*x\s*대상의\s*(출혈|화상|파열|침잠|진동)\s*위력\)\s*%?\s*만큼\s*피해량(?:이)?\s*증가\s*\(최대\s*(\d+(?:\.\d+)?)%\)', body0)
                    if speed_status_coin:
                        q['damage_conditions'].append({'condition':{'type':'speed_diff_status_damage','status':STATUS[speed_status_coin.group(1)],'cap':float(speed_status_coin.group(2))/100},'amount':0.0})
                        supported.append(t); continue
                    # Coin-local unconditional critical-damage bonus.
                    # The coin number is already separated into `ci`; keep this
                    # effect on that coin only.
                    plain_crit = re.search(r'크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if plain_crit and not any(x in body0 for x in ('자신에게', '대상에게', '당 ', '당,', '위력당', '수치당')):
                        q['crit_damage_bonus'] += float(plain_crit.group(1))/100.0
                        supported.append(t); continue
                    # Coin-local self-status presence -> critical-damage bonus.
                    # Example: `1코인 자신에게 사완이 있으면, 크리티컬 피해량 +100%`.
                    crit_status_presence = re.search(r'자신에게\s*([가-힣A-Za-z0-9【】\[\] -]+?)\s*이\s*있으면,?\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', body0)
                    if crit_status_presence:
                        q['damage_conditions'].append({
                            'effect':'crit_damage_bonus',
                            'condition':{'type':'status','name':crit_status_presence.group(1).strip(), 'target':'self','count_gte':1},
                            'amount':float(crit_status_presence.group(2))/100.0,
                        })
                        supported.append(t); continue
                    # Coin-local bracketed named-resource critical-damage scaling.
                    # Names such as `시[始]` must be captured as one resource; the
                    # generic named matcher can otherwise backtrack to `]`.
                    crit_bracketed = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9]+(?:\[[^\]]+\]|【[^】]+】))\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*크리티컬\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if crit_bracketed:
                        raw_name=crit_bracketed.group(1).strip(' ,-')
                        q['damage_conditions'].append({'effect':'crit_damage_bonus','condition':{'type':'named_stack_per','name':raw_name,'target':'self','per':int(crit_bracketed.group(2) or 1),'amount':float(crit_bracketed.group(3))/100,'max':float(crit_bracketed.group(4))/100 if crit_bracketed.group(4) else 999999}})
                        supported.append(t); continue
                    # Coin-local named critical-damage scaling must not fall through
                    # to the flat critical-damage matcher.
                    crit_named = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*크리티컬\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if crit_named:
                        raw_name=crit_named.group(1).strip(' ,-')
                        if raw_name.startswith('대신하여 '): raw_name=raw_name[len('대신하여 '):].strip()
                        if raw_name and raw_name not in {'부정적인 효과','감소한'} and '첫번째 코인에서' not in raw_name:
                            q['damage_conditions'].append({'effect':'crit_damage_bonus','condition':{'type':'named_stack_per','name':raw_name,'target':'self','per':int(crit_named.group(2) or 1),'amount':float(crit_named.group(3))/100,'max':float(crit_named.group(4))/100 if crit_named.group(4) else 999999}})
                            supported.append(t); continue
                    # Coin-local critical damage from Poise is a common special case.
                    crit_poise = re.search(r'호흡\s*(?:위력)?당\s*,?\s*크리티컬\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if crit_poise:
                        q['damage_conditions'].append({'effect':'crit_damage_bonus','condition':{'type':'named_stack_per','name':'호흡','target':'self','per':1,'amount':float(crit_poise.group(1))/100,'max':float(crit_poise.group(2))/100 if crit_poise.group(2) else 999999}})
                        supported.append(t); continue
                    # Coin-local damage based on resources consumed by the current action.
                    # This must be checked before the generic self-named parser because
                    # `소모한 적안, 참회당` otherwise degenerates into `참회당`.
                    consumed_sum = re.search(r'소모한\s*(적안)\s*,?\s*(참회)당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if consumed_sum:
                        q['damage_conditions'].append({'condition':{'type':'resource_consumed_sum_per','resources':[consumed_sum.group(1),consumed_sum.group(2)],'per':1,'amount':float(consumed_sum.group(3))/100,'max':float(consumed_sum.group(4))/100 if consumed_sum.group(4) else 999999}})
                        supported.append(t); continue
                    # Coin-local named status OR condition, e.g. `대상이 A이나 B 상태면`.
                    status_or = re.search(r'대상(?:이|에게)\s*([^,]+?)\s*(?:이나|또는)\s*([^,]+?)\s*(?:가\s*)?(?:상태면|있으면),?\s*(?:이\s*코인\s*)?피해량\s*\+?\s*(\d+(?:\.\d+)?)%', body0)
                    if status_or:
                        q['damage_conditions'].append({'condition':{'type':'or','conditions':[{'type':'status','name':status_or.group(1).strip(),'target':'enemy','count_gte':1},{'type':'status','name':status_or.group(2).strip(),'target':'enemy','count_gte':1}]},'amount':float(status_or.group(3))/100})
                        supported.append(t); continue
                    # Coin-local prior-damage condition.
                    # `대상이 이번 턴에 피해를 받은 상태면` is evaluated at this
                    # coin's timing, so a previous coin in the same skill can make
                    # a later coin qualify. It is not a static skill-level condition.
                    damaged_this_turn = re.search(r'대상(?:이|에게)\s*이번\s*턴에\s*피해를\s*받은\s*상태면,?\s*(?:이\s*코인\s*)?피해량\s*\+?\s*(\d+(?:\.\d+)?)%', body0)
                    if damaged_this_turn:
                        q['damage_conditions'].append({'condition':{'type':'target_damaged_this_turn'},'amount':float(damaged_this_turn.group(1))/100})
                        supported.append(t); continue
                    # Coin-local target presence condition, e.g. `대상에게 경멸이 있으면, 피해량 +235%`.
                    # The presence requirement must never fall through to the flat damage matcher.
                    target_present = re.search(r'대상에게\s*([^,]+?)\s*(?:이|가)\s*있으면,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%', body0)
                    if target_present:
                        raw_name = target_present.group(1).strip(' ,')
                        q['damage_conditions'].append({'condition':{'type':'status','name':raw_name,'target':'enemy','count_gte':1},'amount':float(target_present.group(2))/100})
                        supported.append(t); continue
                    # Coin-local target status/effect scaling where the source says
                    # `대상에게 X가 있으면, 수치 1당 ...`.
                    target_effect = re.search(r'대상에게\s*(.+?)\s*(?:이|가)\s*있으면,?\s*수치\s*1\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if target_effect:
                        raw_name = target_effect.group(1).strip(' ,')
                        q['damage_conditions'].append({'condition':{'type':'named_stack_per','name':raw_name,'target':'enemy','per':1,'amount':float(target_effect.group(2))/100,'max':float(target_effect.group(3))/100 if target_effect.group(3) else 999999}})
                        supported.append(t); continue
                    # This source pattern depends on the exact amount of a prior
                    # `예지안` reduction tied to remaining coins. It is not equivalent
                    # to the current remaining resource, so never flatten it into a
                    # named-stack damage modifier.
                    if '예지안' in body0 and '감소한 수치' in body0 and '피해량' in body0:
                        unsupported.append(t); continue
                    # Coin-local cumulative resource consumption scaling.
                    # `누적 소모 혈찬` is encounter-scoped consumption, not the
                    # currently held resource and not merely this coin's spend.
                    cumulative_consumed = re.search(r'(?:(자신의|공용)\s*)?누적\s*소모\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if cumulative_consumed:
                        scope, resource, per, amount, cap = cumulative_consumed.groups()
                        q['damage_conditions'].append({'condition':{'type':'cumulative_resource_consumed_per','resource':resource.strip(' ,'),'scope':'shared' if scope=='공용' else 'self','per':int(per or 1),'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999}})
                        supported.append(t); continue
                    # Coin-local cumulative-consumption threshold plus per-unit scaling,
                    # e.g. `공용 누적 소모 혈찬 100이상이면, 1당 피해량 +0.1%`.
                    cumulative_threshold = re.search(r'(?:(자신의|공용)\s*)?누적\s*소모\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(\d+)\s*이상.*?\s*1\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if cumulative_threshold:
                        scope, resource, threshold, amount, cap = cumulative_threshold.groups()
                        q['damage_conditions'].append({'condition':{'type':'cumulative_resource_consumed_per','resource':resource.strip(' ,'),'scope':'shared' if scope=='공용' else 'self','per':1,'min_value':int(threshold),'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999}})
                        supported.append(t); continue
                    # Coin-local scaling from a single resource actually consumed by this action.
                    consumed_single = re.search(r'(?:이\s*스킬에서\s*)?소모한\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if consumed_single:
                        resource_name = consumed_single.group(1).strip(' ,')
                        q['damage_conditions'].append({'condition':{'type':'resource_consumed_sum_per','resources':[resource_name],'per':int(consumed_single.group(2) or 1),'amount':float(consumed_single.group(3))/100,'max':float(consumed_single.group(4))/100 if consumed_single.group(4) else 999999}})
                        supported.append(t); continue
                    # Coin-local self lost-HP percentage scaling must stay dynamic.
                    # This is distinct from current HP and must be evaluated at coin timing.
                    self_lost_coin = re.search(r'(?:자신의\s*)?잃은\s*체력\s*(\d+(?:\.\d+)?)%\s*당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if self_lost_coin:
                        q['damage_conditions'].append({'condition':{'type':'self_lost_hp_per','per':float(self_lost_coin.group(1)),'amount':float(self_lost_coin.group(2))/100,'max':float(self_lost_coin.group(3))/100 if self_lost_coin.group(3) else 999999}})
                        supported.append(t); continue
                    # Coin-local self named-resource/status scaling must stay dynamic.
                    # Examples: `해금 단계 1당 피해량 +20%`, `지령의 가호 1당 피해량 +5%`.
                    self_named = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if self_named and '소모한' not in body0:
                        raw_name = self_named.group(1).strip(' ,-')
                        if raw_name.startswith('자신의 '): raw_name = raw_name[len('자신의 '):].strip()
                        if raw_name not in {'부정적인 효과', '감소한'} and '대상' not in raw_name:
                            q['damage_conditions'].append({'condition':{'type':'named_stack_per','name':raw_name,'target':'self','per':int(self_named.group(2) or 1),'amount':float(self_named.group(3))/100,'max':float(self_named.group(4))/100 if self_named.group(4) else 999999}})
                            supported.append(t); continue
                    # Coin-local target-speed difference scaling must stay dynamic.
                    sm=re.search(r'대상의\s*속도가\s*자신보다\s*(?:느리|낮).*?대상과의\s*속도\s*차이\s*(\d+)\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', body0)
                    if sm:
                        q['damage_conditions'].append({'condition':{'type':'speed_difference_per','direction':'lower','per':int(sm.group(1)),'amount':float(sm.group(2))/100,'max':float(sm.group(3))/100 if sm.group(3) else 999999}})
                        supported.append(t); continue
                    cm2=re.search(r'크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%',body0)
                    if cm2 and not re.search(r'(당|이면|있으면|이상|이하|미만|초과|소모|보유|속도가|대상의|자신의|첫번째|재사용|합 승리)', body0):
                        coins[ci]['crit_damage_bonus']=float(cm2.group(1))/100; supported.append(t); continue
                    dm=re.search(r'피해량\s*\+\s*(\d+(?:\.\d+)?)%',body0)
                    if dm and not re.search(r'(당|이면|있으면|이상|이하|미만|초과|소모|보유|속도가|대상의|자신의|첫번째|재사용|적중|합 승리|지령 표식)', body0):
                        coins[ci]['damage_bonus']=float(dm.group(1))/100; supported.append(t); continue
                    sm=re.search(r'피해량의\s*(\d+(?:\.\d+)?)%만큼\s*흐트러짐\s*손상',body0)
                    if sm: coins[ci]['stagger_damage_ratio']=float(sm.group(1))/100; supported.append(t); continue
                    em=re.search(r'피해량의\s*(\d+(?:\.\d+)?)%만큼\s*추가\s*피해',body0)
                    if em:
                        coins[ci]['effects'].append({'type':'extra_damage_scale','scale':float(em.group(1))/100})
                        supported.append(t); continue
                    # Charge Potency -> coin-final-damage additional Slash damage.
                    # This is a post-hit typed damage component, not a generic
                    # damage multiplier: the source explicitly uses the coin's
                    # final damage as the base and says the result is Slash damage.
                    csm=re.search(r'이\s*코인\s*최종\s*피해량의\s*\(\s*충전\s*위력\s*[x×]\s*(\d+(?:\.\d+)?)\s*\)%만큼\s*참격\s*피해(?:\s*\(\s*최대\s*(\d+(?:\.\d+)?)%\s*\))?', body0)
                    if csm:
                        coins[ci]['effects'].append({
                            'type':'resource_final_damage_scale',
                            'resource':'충전 위력',
                            'scale_per':float(csm.group(1))/100.0,
                            'cap':float(csm.group(2))/100.0 if csm.group(2) else 999999.0,
                            'damage_type':'slash',
                            'target':'enemy',
                        })
                        supported.append(t); continue
                    # Flat additional damage on a successful coin hit, e.g.
                    # "1코인 [앞면 적중시] 추가 피해 +3". This is deliberately
                    # represented as a post-hit fixed-damage effect rather than a
                    # multiplier, preserving the distinction from "피해량 +X%".
                    fm=re.search(r'추가\s*피해\s*\+\s*(\d+(?:\.\d+)?)',body0)
                    if fm:
                        flat_effect={'type':'damage_fixed','amount':float(fm.group(1)),'target':'enemy'}
                        hit_prefix=re.match(r'\[(적중시|앞면 적중시|뒷면 적중시)\]', body0)
                        if hit_prefix and hit_prefix.group(1) != '적중시':
                            bucket='heads_effects' if hit_prefix.group(1)=='앞면 적중시' else 'tails_effects'
                            coins[ci][bucket].append(flat_effect)
                        else:
                            coins[ci]['effects'].append(flat_effect)
                        supported.append(t); continue
                    # Final-coin modifiers can share a clause with another coin property
                    # such as '파괴 불가 코인'. Parse the targeted modifier before
                    # consuming the whole clause as a coin-property flag.
                    lcm = re.search(r'(?:\[(앞면 적중시|합 승리 후 적중시|적중시)\])?.*?마지막\s*코인의\s*피해량\s*(?:\+|)(\d+(?:\.\d+)?)%', t)
                    if lcm and '마지막 코인' in t:
                        trigger = lcm.group(1) or '적중시'
                        cond = None if trigger == '적중시' else {'type': 'front_hit' if trigger == '앞면 적중시' else 'clash_result', 'value': 'win' if trigger == '합 승리 후 적중시' else None}
                        last_coin_damage_rules.append({'condition': cond, 'trigger_coin_index': ci+1, 'amount': float(lcm.group(2))/100.0})
                    lcm = re.search(r'자신에게\s*발각(?:\[.*?\])?이\s*있으면.*?수치\s*1당.*?마지막\s*코인의\s*피해량\s*\+(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%', t)
                    if lcm:
                        last_coin_damage_rules.append({'condition': {'type':'status','name':'발각','target':'self','count_gte':1}, 'status_scaling': {'name':'발각','per':1,'amount':float(lcm.group(1))/100.0,'max':float(lcm.group(2))/100.0}})
                    if '파괴 불가 코인' in body0:
                        coins[ci]['unbreakable']=True
                    if '파괴 불가 코인' in body0 or lcm or xcm:
                        supported.append(t); continue
            if m:
                idx=int(m.group(1))-1 if m.group(1) else None
                typ=m.group(2); body=m.group(3)
                # Specialized unnumbered coin-local Charge Potency -> Slash
                # damage must be handled before the generic status-effect
                # fallback, which otherwise marks the clause unsupported.
                csm_unnum=re.search(r'이\s*코인\s*최종\s*피해량의\s*\(\s*충전\s*위력\s*[x×]\s*(\d+(?:\.\d+)?)\s*\)%만큼\s*참격\s*피해(?:\s*\(\s*최대\s*(\d+(?:\.\d+)?)%\s*\))?', t)
                if csm_unnum and idx is None:
                    effect={
                        'type':'resource_final_damage_scale',
                        'resource':'충전 위력',
                        'scale_per':float(csm_unnum.group(1))/100.0,
                        'cap':float(csm_unnum.group(2))/100.0 if csm_unnum.group(2) else 999999.0,
                        'damage_type':'slash',
                        'target':'enemy',
                    }
                    for q in coins:
                        q['effects'].append(dict(effect))
                    supported.append(t); continue
                # Compound keyword grants such as `진동 4 부여, 진동 횟수 2 증가`
                # carry both axes in one source clause. Preserve both rather than
                # letting the first potency match swallow the count.
                compound=[]
                for ko,en in STATUS.items():
                    pm=re.search(re.escape(ko)+r'\s*(?:위력\s*)?(\d+)\s*부여', body)
                    cm=re.search(re.escape(ko)+r'\s*횟수\s*(\d+)\s*(?:증가|추가|부여)', body)
                    if pm and cm:
                        compound.append({'type':'status','name':en,'potency':int(pm.group(1)),'count':int(cm.group(1))})
                if compound:
                    target="enemy"
                    bucket="heads_effects" if typ=="앞면 적중시" else "tails_effects" if typ=="뒷면 적중시" else "effects"
                    targets=range(coin_count) if idx is None else [idx]
                    for i in targets:
                        if 0<=i<coin_count:
                            for eff2 in compound:
                                applied={**eff2,"target":target}
                                mults=coins[i].get('keyword_application_multipliers',{})
                                mult=mults.get(eff2['name'],{})
                                if mult:
                                    applied['potency_multiplier']=int(mult.get('potency',1))
                                    applied['count_multiplier']=int(mult.get('count',1))
                                    applied['multiplier_condition']=mults.get('_condition')
                                coins[i][bucket].append(applied)
                    supported.append(t); continue
                eff=self._status_effect(body)
                if eff:
                    target="enemy" if any(k in body for k in ["대상","적"] ) else "enemy"
                    bucket="heads_effects" if typ=="앞면 적중시" else "tails_effects" if typ=="뒷면 적중시" else "effects"
                    targets=range(coin_count) if idx is None else [idx]
                    for i in targets:
                        if 0<=i<coin_count:
                            applied = {**eff, "target": target}
                            mults = coins[i].get('keyword_application_multipliers', {})
                            mult = mults.get(str(eff.get('name')), {}) if eff.get('type') == 'status' else {}
                            if mult and eff.get('name') in ('Tremor', 'Rupture'):
                                applied['potency_multiplier'] = int(mult.get('potency', 1))
                                applied['count_multiplier'] = int(mult.get('count', 1))
                                applied['multiplier_condition'] = mults.get('_condition')
                            coins[i][bucket].append(applied)
                    supported.append(t); continue
                unsupported.append(t); continue
            # Skill-level source-backed Tremor Burst boundaries.
            if '이 스킬에서 고독을 부여할 때' in t and '대신 진동 폭발' in t:
                cm=re.search(r'진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소',t)
                on_use.append({'type':'tremor_burst_replacement','name':'Tremor','target':'enemy','replacement_status':'고독','condition':{'type':'loneliness_present_current_or_next_turn'},'count_cost':int(cm.group(1)) if cm else 0}); supported.append(t); continue
            # Source-backed added-coin boundary may be split across catalog
            # effect lines. Keep the condition until the following line names
            # the source coin and then attach added-coin-only hit effects to the
            # generated copy, not the original coin.
            amc=re.search(r'새벽불이\s*(\d+)\s*이상이면', t)
            if amc and '스킬의' not in t:
                pending_added_coin_rule={'condition': {'type':'resource_gte','resource':'새벽불','value':int(amc.group(1))}}
                supported.append(t); continue
            if pending_added_coin_rule is not None:
                acm=re.search(r'스킬의\s*(\d+)코인이\s*파괴\s*불가\s*코인으로\s*1개\s*추가', t)
                if acm:
                    pending_added_coin_rule.update({'source_coin_index':int(acm.group(1))-1,'count':1,'unbreakable':True,'effects':[]})
                    added_coin_rules.append(pending_added_coin_rule); pending_added_coin_rule=None
                    supported.append(t); continue
            if '추가된 코인 적중 시 진동 폭발' in t:
                cm=re.search(r'진동\s*폭발\s*\.\s*대상(?:의)?\s*진동\s*횟수\s*(\d+)\s*감소',t)
                eff={'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'added_coin_hit'},'count_cost':int(cm.group(1)) if cm else None}
                if added_coin_rules and added_coin_rules[-1].get('effects') == []:
                    added_coin_rules[-1]['effects'].append(eff)
                else:
                    on_use.append({'type':'pending_added_coin_burst','name':'Tremor','target':'enemy','condition':{'type':'added_coin_hit'},'count_cost':int(cm.group(1)) if cm else None})
                supported.append(t); continue
            # Identity-10813: a resource-gated last-reuse hit effect.
            if '마지막 재사용 코인 적중시 진동 폭발' in t:
                m=re.search(r'광【光】\s*위력이\s*(\d+)\s*면.*?마지막 재사용 코인 적중시 진동 폭발\s*(\d+)회.*?진동 횟수\s*(\d+)\s*감소',t)
                if not m:
                    m=re.search(r'[-·]?\s*(\d+)면,\s*마지막 재사용 코인 적중시 진동 폭발\s*(\d+)회.*?진동 횟수\s*(\d+)\s*감소',t)
                if m:
                    pending_reuse_hit_effects.append({'type':'tremor_burst','name':'Tremor','target':'enemy','burst_count':int(m.group(2)),'count_cost':int(m.group(3)),'condition':{'type':'reuse_hit'}})
                    last_coin_reuse_rules.append({'condition':{'type':'resource_gte','resource':'광【光】','value':int(m.group(1))},'max_reuses':1,'reuse_hit_effects':list(pending_reuse_hit_effects)})
                    pending_reuse_hit_effects=[]; supported.append(t); continue
            if '완성되어가는 교본이 있거나' in t and '진동 폭발' in t and '진동 횟수' in t and '감소' in t and not re.match(r'^\d+코인', t):
                mcond=re.search(r'완성되어가는\s*교본이\s*있거나\s*대상에게\s*결투\s*고조가\s*있으면,\s*진동\s*폭발\s*(\d+)?회?\s*\.\s*진동\s*횟수\s*(\d+)\s*감소',t)
                if mcond:
                    on_use.append({'type':'tremor_burst','name':'Tremor','target':'enemy','condition':{'type':'or','conditions':[{'type':'resource_gte','resource':'완성되어가는 교본','value':1},{'type':'status','name':'결투 고조','target':'enemy','count_gte':1}]},'burst_count':int(mcond.group(1) or 1),'count_cost':int(mcond.group(2))}); supported.append(t); continue
            # Use-time resource/status gains.
            if "[사용시]" in t:
                body=t.split("[사용시]",1)[1]
                parsed=self._use_effect(body)
                if parsed:
                    on_use.extend(parsed); supported.append(t); continue
                # Resource costs are action-start state changes.
                cmc=re.search(r'(충전|탄환)\s*(?:횟수\s*)?(?:를\s*)?(\d+)\s*소모',body)
                if cmc:
                    typ="charge" if cmc.group(1)=="충전" else "ammo"
                    on_use.append({"type":typ,"amount":-int(cmc.group(2))}); supported.append(t); continue
                spm=re.search(r'정신력\s*(\d+)\s*감소',body)
                if spm:
                    on_use.append({"type":"sp","amount":-int(spm.group(1))}); supported.append(t); continue
            # Kill-triggered skill reuse. It is intentionally marked so the
            # execution layer can suppress recursive triggering on the reused copy.
            if ('적 처치 시' in t or '[적 처치 시]' in t) and '스킬 1회 재사용' in t:
                kill_reuse_rules.append({'condition':{'type':'always'},'max_reuses':1,'mode':'skill','recursive':False})
                supported.append(t); continue
            # Skill-level last-coin reuse. This is distinct from a coin-local
            # reuse because it executes the skill's final coin again after the
            # normal coin sequence. A source clause marked [재사용 적중시]
            # is attached to the reused logical coin rather than the original hit.
            if '[재사용 적중시]' in t:
                body = t.split('[재사용 적중시]', 1)[1].strip()
                eff = self._status_effect(body)
                if eff:
                    eff = dict(eff)
                    eff['condition'] = {'type':'reuse_hit'}
                    if '스킬당 1회' in t or '스킬당 1회만' in t:
                        eff['reuse_hit_limit']=1
                    pending_reuse_hit_effects.append(eff)
                    supported.append(t); continue
            lm=re.search(r"(?:자신의\s*)?(%s)(?:\s*횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?마지막\s*코인\s*재사용" % '|'.join(re.escape(x) for x in sorted(self.SPECIAL_RESOURCE_NAMES,key=len,reverse=True)), t)
            if lm and "외부 효과" not in t:
                rule={"condition":{"type":"resource_gte","resource":lm.group(1),"value":int(lm.group(2))},"max_reuses":1}
                if pending_reuse_hit_effects:
                    rule['reuse_hit_effects']=list(pending_reuse_hit_effects); pending_reuse_hit_effects=[]
                last_coin_reuse_rules.append(rule)
                supported.append(t); continue
            lm=re.search(r"마지막\s*코인\s*재사용(?:\s*\(스킬당\s*최대\s*)?(\d+)회", t)
            if lm and "외부 효과" not in t:
                rule={"condition":{"type":"always"},"max_reuses":int(lm.group(1))}
                if pending_reuse_hit_effects:
                    rule['reuse_hit_effects']=list(pending_reuse_hit_effects); pending_reuse_hit_effects=[]
                last_coin_reuse_rules.append(rule)
                supported.append(t); continue
            lm=re.search(r"마지막\s*코인\s*재사용", t)
            if lm and "외부 효과" not in t:
                rule={"condition":{"type":"always"},"max_reuses":1}
                if pending_reuse_hit_effects:
                    rule['reuse_hit_effects']=list(pending_reuse_hit_effects); pending_reuse_hit_effects=[]
                last_coin_reuse_rules.append(rule)
                supported.append(t); continue
            # Conditional named-resource scaling on the final coin. This must
            # precede the generic final-coin bonus parser so target thresholds and
            # resource scaling are not flattened into an unconditional bonus.
            fcm = re.search(
                r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)(?:이|가|은|는)?\s*(?:위력|수치)?\s*(?P<threshold>\d+)\s*이상.*?'
                r'(?P<resource>[가-힣A-Za-z0-9【】\[\]/・・ -]{1,40}?)\s*(?:수치|횟수|위력)?\s*(?:1\s*)?당\s*마지막\s*코인의\s*피해량\s*\+(?P<amount>\d+(?:\.\d+)?)%.*?'
                r'(?:최대\s*(?P<cap>\d+(?:\.\d+)?)%)', t)
            if fcm:
                last_coin_damage_rules.append({
                    'condition': {'type':'status','name':STATUS[fcm.group(1)],'target':'enemy','potency_gte':int(fcm.group('threshold'))},
                    'status_scaling': {'name':fcm.group('resource').strip(' ,'),'per':1,'amount':float(fcm.group('amount'))/100.0,'max':float(fcm.group('cap'))/100.0 if fcm.group('cap') else 999999,'use_potency':False}
                })
                supported.append(t); continue
            # Skill-level final-coin damage clauses must be consumed before
            # generic unbreakable/skill-property handlers.
            lcm = re.search(r'.*?마지막\s*코인의\s*피해량\s*(?:\+|)(\d+(?:\.\d+)?)%', t)
            if lcm and '마지막 코인' in t:
                if '발각' in t and '자신에게' in t:
                    capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', t)
                    last_coin_damage_rules.append({'condition': {'type':'status','name':'발각','target':'self','count_gte':1}, 'status_scaling': {'name':'발각','per':1,'amount':float(lcm.group(1))/100.0,'max':float(capm.group(1))/100.0 if capm else 999999}})
                else:
                    last_coin_damage_rules.append({'condition': None, 'amount': float(lcm.group(1))/100.0})
                supported.append(t); continue
            # Skill-wide modifiers / coin properties. Conditional unbreakable
            # rules must remain conditional; flattening them into q['unbreakable']
            # would incorrectly make the coins unbreakable for every state.
            if "파괴 불가 코인" in t and not re.match(r'^\d+코인',t):
                if re.search(r'자신의\s*충전\s*위력이\s*(\d+)\s*이상이거나,?\s*현재\s*체력이\s*최대\s*체력의\s*(\d+(?:\.\d+)?)%\s*미만', t):
                    m=re.search(r'자신의\s*충전\s*위력이\s*(\d+)\s*이상이거나,?\s*현재\s*체력이\s*최대\s*체력의\s*(\d+(?:\.\d+)?)%\s*미만', t)
                    on_use.append({'type':'_skill_unbreakable_condition_marker','condition':{'type':'or','conditions':[{'type':'resource_gte','resource':'충전 위력','value':int(m.group(1))},{'type':'self_hp_pct_lte','value':float(m.group(2))}]}})
                else:
                    for q in coins: q['unbreakable']=True
                supported.append(t); continue
            if re.search(r'^[-]?\s*최종 위력\s*\+\s*\d+',t):
                fm=re.search(r'최종 위력\s*\+\s*(\d+)',t)
                if fm: on_use.append({"type":"final_power_marker","amount":int(fm.group(1))}); supported.append(t); continue
            # Generic conditional final-power rules. Unlike a flat final-power
            # marker, these are evaluated from the current state when the skill
            # rolls, allowing status changes before later actions to matter.
            fp=re.search(r'자신의\s*(호흡|화상|출혈|파열|침잠|진동)\s*(?:위력|횟수)?\s*(?:이|가|은|는)?\s*(\d+)\s*이상.*?최종\s*위력\s*\+\s*(\d+)',t)
            if fp:
                name='Poise' if fp.group(1)=='호흡' else STATUS[fp.group(1)]
                field='count' if fp.group(1)=='호흡' else 'potency'
                on_use.append({'type':'_skill_final_power_condition_marker','condition':{'type':'status_threshold','target':'self','name':name,'field':field,'value':int(fp.group(2)),'amount':int(fp.group(3))}})
                supported.append(t); continue
            # Explicit self-Poise damage scaling is a skill-level condition.
            # Poise is stored on FighterState.poise rather than statuses.
            poise_self = re.search(r'자신의\s*호흡\s*(?:위력|수치)?\s*(\d+)\s*당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', t)
            if poise_self:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'named_stack_per','name':'호흡','target':'self','per':int(poise_self.group(1)),'amount':float(poise_self.group(2))/100,'max':float(poise_self.group(3))/100 if poise_self.group(3) else 999999}})
                supported.append(t); continue
            # Explicit status-based damage scaling.  Only unambiguous potency/count
            # wording is parsed; ambiguous status references remain unsupported.
            status_scaling_matched=False
            for ko,en in STATUS.items():
                if en in ('Poise','Charge','Bind','Damage Taken Up'): continue
                sm=re.search(re.escape(ko)+r'\s*(?:위력|수치)\s*(\d+)\s*당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%',t)
                if sm:
                    on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'status_count_per','name':en,'target':'enemy','per':int(sm.group(1)),'amount':float(sm.group(2))/100,'max':float(sm.group(3))/100,'use_potency':True}})
                    supported.append(t); break
                sm=re.search(re.escape(ko)+r'\s*횟수\s*(\d+)\s*당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%',t)
                if sm:
                    on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'status_count_per','name':en,'target':'enemy','per':int(sm.group(1)),'amount':float(sm.group(2))/100,'max':float(sm.group(3))}})
                    supported.append(t); status_scaling_matched=True; break
            else:
                # no explicit status-scaling match
                pass
            if status_scaling_matched:
                continue
            generic_t = t.replace('[사용시]', '').strip()
            # Explicit final-coin targets can be written as skill-level clauses
            # (for example, '[전투 시작시] ... 마지막 코인의 피해량 +X%').
            lcm = re.search(r'(?:\[(?:전투 시작시|사용시)\])?.*?마지막\s*코인의\s*피해량\s*(?:\+|)(\d+(?:\.\d+)?)%', generic_t)
            if lcm and '마지막 코인' in generic_t:
                cond = None
                if '발각' in generic_t and '자신에게' in generic_t:
                    last_coin_damage_rules.append({'condition': {'type':'status','name':'발각','target':'self','count_gte':1}, 'status_scaling': {'name':'발각','per':1,'amount':float(lcm.group(1))/100.0,'max':float((re.search(r'최대\s*(\d+(?:\.\d+)?)%', generic_t) or type('M',(),{'group':lambda self,n: None})()).group(1) or 999999)/100.0}})
                else:
                    last_coin_damage_rules.append({'condition': None, 'amount': float(lcm.group(1))/100.0})
                supported.append(t); continue
            fp=re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:과|와)\s*(출혈|화상|파열|침잠|진동)\s*의\s*합\s*(\d+)\s*당,?\s*최종\s*위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?', generic_t)
            if fp:
                on_use.append({'type':'_skill_final_power_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[fp.group(1)],STATUS[fp.group(2)]],'target':'enemy','per':int(fp.group(3)),'amount':int(fp.group(4)),'max':int(fp.group(5) or 999999),'use_potency':True}})
                supported.append(t); continue
            fp=re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(\d+)\s*당,?\s*최종\s*위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?', generic_t)
            if fp:
                on_use.append({'type':'_skill_final_power_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[fp.group(1)]],'target':'enemy','per':int(fp.group(2)),'amount':int(fp.group(3)),'max':int(fp.group(4) or 999999),'use_potency':True}})
                supported.append(t); continue
            fp=re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(\d+)\s*이상.*?최종\s*위력\s*\+\s*(\d+)', generic_t)
            if fp:
                on_use.append({'type':'_skill_final_power_condition_marker','condition':{'type':'status_threshold','target':'enemy','name':STATUS[fp.group(1)],'field':'potency','value':int(fp.group(2)),'amount':int(fp.group(3))}})
                supported.append(t); continue
            # Generic status-sum / per-status damage scaling.  These are
            # unambiguous when the text explicitly names the statuses and the
            # unit/bonus/cap.  Keep the calculation dynamic so later coins see
            # status changes made by earlier coins.
            sm=re.search(r'대상의\s*(출혈|화상|파열|침잠|진동|속박)\s*(?:위력|수치)?\s*(?:([0-9]+)\s*당|당)?\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%',generic_t)
            if sm and ('이상' not in generic_t) and ('횟수' not in generic_t):
                per=int(sm.group(2) or 1)
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[sm.group(1)]],'target':'enemy','per':per,'amount':float(sm.group(3))/100,'max':float((re.search(r'최대\s*(\d+(?:\.\d+)?)%',generic_t) or type('M',(),{'group':lambda self,n: None})()).group(1) or 999999)/100,'use_potency':True}})
                supported.append(t); continue
            sm=re.search(r'피해량\s*\+\s*\(\s*자신과\s*(?:타겟|대상)의\s*(출혈|화상|파열|침잠|진동|속박)\s*(?:위력|수치)?\s*합\s*\)\s*%',generic_t)
            if sm:
                per=1
                capm=re.search(r'최대\s*(\d+(?:\.\d+)?)%',generic_t)
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'cross_status_sum_per','self_status':STATUS[sm.group(1)],'enemy_status':STATUS[sm.group(1)],'per':per,'amount':1.0,'max':float(capm.group(1))/100 if capm else 999999,'use_potency':True}})
                supported.append(t); continue
            sm=re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)\s*(?:과|와)\s*(출혈|화상|파열|침잠|진동)\s*의\s*합\s*(?:([0-9]+)\s*당)?\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%',generic_t)
            if sm:
                per=int(sm.group(3) or 1)
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[sm.group(1)],STATUS[sm.group(2)]],'target':'enemy','per':per,'amount':float(sm.group(4))/100,'max':float((re.search(r'최대\s*(\d+(?:\.\d+)?)%',generic_t) or type('M',(),{'group':lambda self,n: None})()).group(1) or 999999)/100,'use_potency':True}})
                supported.append(t); continue
            # Self named-resource-per damage scaling, e.g. '자신의 찢어진 추억당 피해량 +15%'.
            for resource in sorted(self.SPECIAL_RESOURCE_NAMES, key=len, reverse=True):
                rm=re.search(re.escape(resource)+r'\s*(?:수치|횟수)?\s*(?:([0-9]+)\s*당|당)?\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%',generic_t)
                if rm and ('소모' not in generic_t):
                    per=int(rm.group(1) or 1)
                    on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_per','resource':resource,'target':'self','per':per,'amount':float(rm.group(2))/100,'max':float((re.search(r'최대\s*(\d+(?:\.\d+)?)%',generic_t) or type('M',(),{'group':lambda self,n: None})()).group(1) or 999999)/100}})
                    supported.append(t); break
            else:
                # no named-resource-per match
                pass
            if supported and supported[-1] == t:
                continue
            # Generic attack-weight gap scaling for skill-level prose without a
            # leading coin number. Keep this ahead of the named-stack parser because
            # '공격 대상 1당' is not a resource/status stack.
            awm=re.search(r'이\s*스킬\s*공격\s*가중치보다\s*낮은\s*공격\s*대상\s*1\s*당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if awm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'attack_weight_gap_damage','amount':float(awm.group(1))/100.0}})
                supported.append(t); continue
            # Target negative-effect count scaling. This must precede the generic
            # named-stack parser because `대상의 부정적인 효과 N개당` is not a
            # named resource/status; it is a count of active negative statuses.
            nm=re.search(r'(?:대상의\s*)?부정적인\s*효과\s*(\d+)\s*개당,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if nm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'negative_status_count_per','target':'enemy','per':int(nm.group(1)),'amount':float(nm.group(2))/100,'max':float(nm.group(3))/100 if nm.group(3) else 999999}})
                supported.append(t); continue
            # Target-speed difference damage scaling must precede generic named-stack
            # parsing. Otherwise `대상과의 속도 차이` is mistaken for a named resource.
            sm=re.search(r'대상의\s*속도가\s*자신보다\s*(?:느리|낮).*?대상과의\s*속도\s*차이\s*(\d+)\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if sm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'speed_difference_per','direction':'lower','per':int(sm.group(1)),'amount':float(sm.group(2))/100,'max':float(sm.group(3))/100 if sm.group(3) else 999999}})
                supported.append(t); continue
            # Do not treat `감소한 수치` as a named resource. The source means
            # the amount of a preceding `예지안` reduction, which is a separate
            # action-state calculation and is intentionally unsupported here.
            if '예지안' in generic_t and '감소한 수치' in generic_t and '피해량' in generic_t:
                unsupported.append(t); continue
            # Cross-scope lost-HP sum: `대상과 자신의 잃은 체력 합 1% 당 피해량 +X%`.
            lost_sum = re.search(r'대상과\s*자신의\s*잃은\s*체력\s*합\s*(\d+(?:\.\d+)?)%\s*당,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if lost_sum:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'cross_lost_hp_sum_per','per':float(lost_sum.group(1)),'amount':float(lost_sum.group(2))/100,'max':float(lost_sum.group(3))/100 if lost_sum.group(3) else 999999}})
                supported.append(t); continue
            # Cross-scope Haste + target Bind sum. Both are count-like statuses.
            hb = re.search(r'자신의\s*신속과\s*대상의\s*속박의\s*합\s*(\d+)\s*당,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if hb:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'cross_status_count_sum_per','self_status':'신속','enemy_status':'Bind','per':int(hb.group(1)),'amount':float(hb.group(2))/100,'max':float(hb.group(3))/100 if hb.group(3) else 999999}})
                supported.append(t); continue
            # Sin resonance count scaling, e.g. `분노 공명당 피해량 10% 증가`.
            res = re.search(r'(분노|색욕|나태|탐식|우울|오만|질투)\s*공명당\s*피해량\s*(?:\+\s*)?(\d+(?:\.\d+)?)%\s*(?:증가)?(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if res:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resonance_per','sin':res.group(1),'per':1,'amount':float(res.group(2))/100,'max':float(res.group(3))/100 if res.group(3) else 999999}})
                supported.append(t); continue
            # Skill-level cumulative resource consumption scaling.
            cumulative_consumed_generic = re.search(r'(?:(자신의|공용)\s*)?누적\s*소모\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if cumulative_consumed_generic:
                scope, resource, per, amount, cap = cumulative_consumed_generic.groups()
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'cumulative_resource_consumed_per','resource':resource.strip(' ,'),'scope':'shared' if scope=='공용' else 'self','per':int(per or 1),'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999}})
                supported.append(t); continue
            # Skill-level cumulative-consumption threshold plus per-unit scaling.
            cumulative_threshold_generic = re.search(r'(?:(자신의|공용)\s*)?누적\s*소모\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(\d+)\s*이상.*?\s*1\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if cumulative_threshold_generic:
                scope, resource, threshold, amount, cap = cumulative_threshold_generic.groups()
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'cumulative_resource_consumed_per','resource':resource.strip(' ,'),'scope':'shared' if scope=='공용' else 'self','per':1,'min_value':int(threshold),'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999}})
                supported.append(t); continue
            # Skill-level scaling from a resource actually consumed by this action.
            consumed_single_generic = re.search(r'(?:이\s*스킬에서\s*)?소모한\s*([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if consumed_single_generic:
                resource_name = consumed_single_generic.group(1).strip(' ,')
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_consumed_sum_per','resources':[resource_name],'per':int(consumed_single_generic.group(2) or 1),'amount':float(consumed_single_generic.group(3))/100,'max':float(consumed_single_generic.group(4))/100 if consumed_single_generic.group(4) else 999999}})
                supported.append(t); continue
            # Bracketed named resources/statuses must be captured as a whole.
            # Without this, `흑수환염[黑獣丸染] 1당` can backtrack to `]` and
            # become a bogus one-character resource.
            bracketed = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9]+(?:\[[^\]]+\]|【[^】]+】))\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%', generic_t)
            if bracketed and '소모한' not in generic_t:
                raw_name = bracketed.group(1).strip(' ,')
                per=int(bracketed.group(2) or 1); amount=float(bracketed.group(3))/100.0
                capm=re.search(r'최대\s*(\d+(?:\.\d+)?)%', generic_t)
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'named_stack_per','name':raw_name,'target':'self','per':per,'amount':amount,'max':float(capm.group(1))/100.0 if capm else 999999}})
                supported.append(t); continue
            # Explicit self lost-HP percentage scaling.
            slhp = re.search(r'자신의\s*잃은\s*체력\s*(\d+(?:\.\d+)?)%\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if slhp:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'self_lost_hp_per','per':float(slhp.group(1)),'amount':float(slhp.group(2))/100,'max':float(slhp.group(3))/100 if slhp.group(3) else 999999}})
                supported.append(t); continue
            # Explicit enemy lost-HP percentage scaling. This must precede the
            # generic named-stack matcher so `잃은 체력` is not parsed as an
            # unnamed resource.
            elhp = re.search(r'(?:대상의|메인\s*타겟의|적\(본체\)의)\s*잃은\s*체력\s*(\d+(?:\.\d+)?)%\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if elhp:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'enemy_lost_hp_per','per':float(elhp.group(1)),'amount':float(elhp.group(2))/100,'max':float(elhp.group(3))/100 if elhp.group(3) else 999999}})
                supported.append(t); continue

            # Resource-multiplier damage scaling. Source forms such as
            # `- (자신의 적진 주파 x 20)%만큼 피해량이 증가` are mathematically
            # the same as a 1-per-stack resource scaling, but may be gated by
            # a preceding bullet-block condition (for example, `자신의 속도가
            # 대상보다 높으면`). Preserve that gate instead of flattening the
            # percentage into a constant bonus.
            resource_mul = re.search(r'\(\s*(?:자신의\s*)?([가-힣A-Za-z0-9【】\[\]/·・・ -]+?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*\)\s*%?\s*만큼\s*피해량(?:이|가)?\s*(?:증가|\+)', t)
            if resource_mul:
                raw_name=resource_mul.group(1).strip(' ,')
                multiplier=float(resource_mul.group(2))/100.0
                capm=re.search(r'최대\s*(\d+(?:\.\d+)?)%',t)
                condition={'type':'resource_per','resource':raw_name,'target':'self','per':1,'amount':multiplier,'max':float(capm.group(1))/100.0 if capm else 999999}
                if pending_condition:
                    condition={'type':'resource_per','resource':raw_name,'target':'self','per':1,'amount':multiplier,'max':float(capm.group(1))/100.0 if capm else 999999,'gate':dict(pending_condition)}
                on_use.append({'type':'_skill_damage_condition_marker','condition':condition})
                supported.append(t); pending_condition=None; continue

            # Generic named-stack damage scaling.  This covers catalog resources
            # and named statuses not included in the fixed status vocabulary, e.g.
            # '자신의 지령의 가호 1당 피해량 +2%' or '사랑/증오당 피해량 +2%'.
            # It is intentionally restricted to explicit `N당 피해량` syntax so
            # ordinary prose is not guessed into a damage modifier.
            named = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:(\d+)\s*)?당\s*,?\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%', generic_t)
            if named and '소모한' not in generic_t:
                raw_name = named.group(1).strip(' ,')
                raw_name = re.sub(r'^(?:대상의|적의|메인\s*타겟의)\s*', '', raw_name).strip()
                excluded = {'출혈','화상','파열','침잠','진동','속박','충전','탄환','호흡','속도','속도 차이','체력','잃은 체력'}
                composite = any(x in raw_name for x in ('합','속도','공격 가중치','공격 대상','대상','자신의'))
                # Cross-identity/affiliation counts are not named resources.
                # Do not mark them supported through the generic stack parser
                # unless a dedicated affiliation-count damage runtime exists.
                affiliation_count_phrase = ('파티의' in generic_t or '생존한' in generic_t or '광신도 수' in generic_t or '소속' in generic_t)
                if raw_name not in excluded and not composite and not affiliation_count_phrase:
                    per=int(named.group(2) or 1); amount=float(named.group(3))/100.0
                    capm=re.search(r'최대\s*(\d+(?:\.\d+)?)%', generic_t)
                    target='enemy' if re.search(r'(?:대상의|적의|메인\s*타겟의)\s*'+re.escape(raw_name), generic_t) else 'self'
                    on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'named_stack_per','name':raw_name,'target':target,'per':per,'amount':amount,'max':float(capm.group(1))/100.0 if capm else 999999}})
                    supported.append(t); continue
            # Current target HP threshold damage bonuses.  These are evaluated
            # at coin timing so previous coins can move the target across the
            # threshold within the same skill.
            hm=re.search(r'(?:대상|적\(본체\)|메인\s*타겟).*?(?:현재\s*)?체력(?:이|가|은|는)?\s*(\d+(?:\.\d+)?)%\s*(미만|이하|이상|초과).*?피해량\s*(?:\+\s*)?(\d+(?:\.\d+)?)%\s*(?:증가)?',generic_t)
            if hm:
                op=hm.group(2); typ='enemy_hp_pct_lte' if op in ('미만','이하') else 'enemy_hp_pct_gte'
                # Strict vs inclusive thresholds are both retained for clarity.
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':typ,'value':float(hm.group(1)),'strict':op in ('미만','초과')},'damage_bonus':float(hm.group(3))/100})
                supported.append(t); continue
            # Attack-weight target-count scaling. These are skill-level modifiers
            # evaluated at action/coin timing from the actual selected target count.
            awm=re.search(r'이\s*스킬\s*공격\s*가중치보다\s*낮은\s*공격\s*대상\s*1\s*당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if awm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'attack_weight_gap_damage','amount':float(awm.group(1))/100.0}})
                supported.append(t); continue
            one_target=re.search(r'(?:공격\s*대상이|타겟이)\s*1(?:명|개)?(?:\s*\(.*?\))?\s*(?:이면|일\s*(?:때|경우)).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if one_target:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'target_count_eq','value':1,'amount':float(one_target.group(1))/100.0}})
                supported.append(t); continue
            # Korean skill text often omits the explicit `자신의` subject for
            # resource/status conditions (e.g. `충전 횟수가 10 이상이면` or
            # `화상 10당 피해량 +10%`). These still refer to the acting identity.
            implicit_resource_threshold = re.search(
                r'(충전|호흡)\s*(?:위력|횟수|수치)?\s*(?:이|가|은|는)?\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%',
                generic_t)
            if implicit_resource_threshold:
                resource, threshold, amount = implicit_resource_threshold.groups()
                condition = {'type':'resource_gte','resource':resource,'value':int(threshold)}
                on_use.append({'type':'_skill_condition_marker','condition':condition,'damage_bonus':float(amount)/100})
                supported.append(t); continue
            implicit_self_status_per = re.search(
                r'(화상|출혈|파열|침잠|진동)\s*(?:위력|수치|횟수)?\s*(\d+)\s*당\s*,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?',
                generic_t)
            if implicit_self_status_per:
                ko, per, amount, cap = implicit_self_status_per.groups()
                on_use.append({'type':'_skill_damage_condition_marker','condition':{
                    'type':'status_count_per','name':STATUS[ko],'target':'self','per':int(per),
                    'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999,
                    'use_potency':True},})
                supported.append(t); continue
            # Critical-damage scaling can likewise omit `자신의` and is evaluated
            # only on a critical hit by the damage runtime.
            implicit_poise_crit = re.search(
                r'호흡\s*(?:위력|수치)?\s*(\d+)\s*당\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?',
                generic_t)
            if implicit_poise_crit:
                per, amount, cap = implicit_poise_crit.groups()
                on_use.append({'type':'_skill_condition_marker','condition':{
                    'type':'status_count_per','name':'Poise','target':'self','per':int(per),
                    'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999,
                    'use_potency':True},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            # `잃은 체력` is also commonly written without an explicit subject.
            implicit_lost_hp = re.search(
                r'잃은\s*체력\s*(\d+(?:\.\d+)?)%\s*당\s*피해량\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?',
                generic_t)
            if implicit_lost_hp:
                per, amount, cap = implicit_lost_hp.groups()
                on_use.append({'type':'_skill_damage_condition_marker','condition':{
                    'type':'self_lost_hp_per','per':float(per),'amount':float(amount)/100,
                    'max':float(cap)/100 if cap else 999999}})
                supported.append(t); continue
            # Target negative-effect count wording varies between `대상의` and
            # `대상이 보유한`; both refer to the same enemy-side count.
            negative_owned = re.search(
                r'대상이\s*보유한\s*부정적인\s*효과\s*(\d+)\s*개당\s*피해량(?:이)?\s*\+?\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?',
                generic_t)
            if negative_owned:
                per, amount, cap = negative_owned.groups()
                on_use.append({'type':'_skill_damage_condition_marker','condition':{
                    'type':'negative_status_count_per','target':'enemy','per':int(per),
                    'amount':float(amount)/100,'max':float(cap)/100 if cap else 999999}})
                supported.append(t); continue
            # Generic target/self threshold damage modifiers. These are deliberately
            # limited to known statuses/resources so arbitrary prose is not guessed.
            generic_damage_threshold = re.search(
                r'(대상의|메인\s*타겟의|적의|자신의)\s*(출혈|화상|파열|침잠|진동|속박|못|호흡|충전|광신)(?:\s*(위력|횟수|수치))?\s*(?:이|가)?\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%',
                generic_t)
            if generic_damage_threshold:
                scope, ko, field, threshold, amount = generic_damage_threshold.groups()
                target = 'self' if scope == '자신의' else 'enemy'
                en = STATUS[ko]
                if ko in ('호흡', '충전'):
                    condition = {'type':'resource_gte','resource':ko,'value':int(threshold)}
                else:
                    condition = {'type':'status','name':en,'target':target}
                    condition['count_gte' if field == '횟수' else 'potency_gte'] = int(threshold)
                on_use.append({'type':'_skill_condition_marker','condition':condition,'damage_bonus':float(amount)/100})
                supported.append(t); continue
            # Skill-level status-presence damage conditions. The status name may be
            # a named game status outside the fixed 7-keyword vocabulary, e.g.
            # `찢긴 상처`, `우제트의 눈 [선봉]`, or `보호막`. This is only for the
            # explicit `...에게/에게 ... 있으면/있을 때, 피해량 +N%` form; it does
            # not infer arbitrary prose as a condition.
            named_status_presence = re.search(
                r'(대상에게|메인\s*타겟에게|적에게|자신에게)\s*([가-힣A-Za-z0-9【】\[\]\s·・_-]+?)\s*(?:이|가)?\s*(?:있으면|있을\s*때).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%',
                generic_t)
            if named_status_presence:
                scope, raw_name, amount = named_status_presence.groups()
                raw_name = raw_name.strip(' ,')
                raw_name = STATUS.get(raw_name, raw_name)
                # Do not classify affiliation-count prose as a status-presence rule.
                if raw_name and not any(x in raw_name for x in ('광신도', '소속', '인원 수')):
                    target = 'self' if scope == '자신에게' else 'enemy'
                    on_use.append({'type':'_skill_condition_marker',
                                   'condition':{'type':'status','name':raw_name,'target':target,'count_gte':1},
                                   'damage_bonus':float(amount)/100})
                    supported.append(t); continue

            # Presence conditions such as '대상에게 못이 있으면, 피해량 +70%'.
            generic_damage_presence = re.search(
                r'(대상에게|메인\s*타겟에게|적에게|자신에게)\s*(출혈|화상|파열|침잠|진동|속박|못|호흡|충전|광신)\s*(?:이|가)?\s*(?:있으면|있을\s*때).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%',
                generic_t)
            if generic_damage_presence:
                scope, ko, amount = generic_damage_presence.groups()
                target = 'self' if scope == '자신에게' else 'enemy'
                en = STATUS[ko]
                if ko in ('호흡', '충전') and target == 'self':
                    condition = {'type':'resource_gte','resource':ko,'value':1}
                else:
                    condition = {'type':'status','name':en,'target':target,'count_gte':1}
                on_use.append({'type':'_skill_condition_marker','condition':condition,'damage_bonus':float(amount)/100})
                supported.append(t); continue
            matched_threshold=False
            for ko,en in STATUS.items():
                if en in ('Poise','Charge','Bind','Damage Taken Up'): continue
                tm=re.search(re.escape(ko)+r'\s*(?:위력|수치)?\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%',t)
                if tm:
                    on_use.append({'type':'_skill_condition_marker','condition':{'type':'status','name':en,'target':'enemy','potency_gte':int(tm.group(1))},'damage_bonus':float(tm.group(2))/100})
                    supported.append(t); matched_threshold=True; break
            if matched_threshold: continue
            # Simple action-level damage conditions whose runtime already has
            # exact predicates. Keep these conditional; never flatten them into
            # an unconditional damage_bonus.
            clash_damage = re.search(r'^\[합\s*승리시\].*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if clash_damage:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'clash_result','value':'win'},'damage_bonus':float(clash_damage.group(1))/100})
                supported.append(t); continue
            # Some catalog entries omit `자신의` in self-speed thresholds.
            # In this skill-level damage context, bare `속도가 N 이상` refers
            # to the acting identity, and the existing speed_gte runtime is the
            # correct execution path.
            speed_damage = re.search(r'(?:자신의\s*)?속도가\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if speed_damage:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'speed_gte','value':int(speed_damage.group(1))},'damage_bonus':float(speed_damage.group(2))/100})
                supported.append(t); continue
            # Direct speed comparison damage condition.
            speed_vs_target = re.search(r'자신의\s*속도가\s*대상보다\s*(?:빠르|높).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if speed_vs_target:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'speed_difference_gte','value':1},'damage_bonus':float(speed_vs_target.group(1))/100})
                supported.append(t); continue
            self_hp_damage = re.search(r'자신의\s*(?:현재\s*)?체력이\s*(\d+(?:\.\d+)?)%\s*(미만|이하|이상|초과).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if self_hp_damage:
                threshold, op, amount = self_hp_damage.groups()
                typ='self_hp_pct_lte' if op in ('미만','이하') else 'self_hp_pct_gte'
                on_use.append({'type':'_skill_condition_marker','condition':{'type':typ,'value':float(threshold),'strict':op in ('미만','초과')},'damage_bonus':float(amount)/100})
                supported.append(t); continue
            # Special named-resource thresholds, e.g. `K사 앰플이 5 이상이면`.
            resource_threshold_damage = re.search(r'(?:자신의\s*)?([가-힣A-Za-z0-9【】\[\]/·・・ -]{1,30}?)\s*(?:수치|횟수|위력)?\s*(?:이|가|은|는)\s*(\d+)\s*이상.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if resource_threshold_damage:
                raw_name, threshold, amount = resource_threshold_damage.groups()
                raw_name = raw_name.strip(' ,')
                if raw_name not in {'대상','체력','속도','피해량'} and not any(x in raw_name for x in ('합','속도 차이')):
                    on_use.append({'type':'_skill_condition_marker','condition':{'type':'resource_gte','resource':raw_name,'value':int(threshold)},'damage_bonus':float(amount)/100})
                    supported.append(t); continue
            # Generic conditional Clash Power rules. These affect only the
            # pre-clash skill power and are kept separate from coin power/damage.
            # The copied SkillData is modified immediately before Clash, so later
            # state changes do not leak into the catalog.
            cmatch = re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(\d+)\s*이상.*?합\s*위력\s*\+\s*(\d+)', generic_t)
            if cmatch:
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'status_threshold','target':'enemy','name':STATUS[cmatch.group(1)],'field':'potency','value':int(cmatch.group(2)),'amount':int(cmatch.group(3))}})
                supported.append(t); continue
            cmatch = re.search(r'자신의\s*충전\s*위력\s*(\d+)\s*이상.*?합\s*위력\s*\+\s*(\d+)', generic_t)
            if cmatch:
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'resource_gte','resource':'충전 위력','value':int(cmatch.group(1)),'amount':int(cmatch.group(2))}})
                supported.append(t); continue
            cmatch = re.search(r'자신의\s*(호흡|화상|출혈|파열|침잠|진동|충전)\s*(?:위력|횟수)?\s*(\d+)\s*이상.*?합\s*위력\s*\+\s*(\d+)', generic_t)
            if cmatch:
                field='count' if cmatch.group(1) in ('호흡','충전') else 'potency'
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'status_threshold','target':'self','name':STATUS[cmatch.group(1)],'field':field,'value':int(cmatch.group(2)),'amount':int(cmatch.group(3))}})
                supported.append(t); continue
            cmatch = re.search(r'자신의\s*('+ '|'.join(re.escape(x) for x in sorted(SkillTextParserV19.SPECIAL_RESOURCE_NAMES,key=len,reverse=True)) + r')\s*(?:횟수|수치)?\s*(\d+)\s*이상.*?합\s*위력\s*\+\s*(\d+)', generic_t)
            if cmatch:
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'resource_gte','resource':cmatch.group(1),'value':int(cmatch.group(2)),'amount':int(cmatch.group(3))}})
                supported.append(t); continue
            cmatch = re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:과|와)\s*(출혈|화상|파열|침잠|진동)\s*의\s*합\s*(\d+)\s*당,?\s*합\s*위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?', generic_t)
            if cmatch:
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[cmatch.group(1)],STATUS[cmatch.group(2)]],'target':'enemy','per':int(cmatch.group(3)),'amount':int(cmatch.group(4)),'max':int(cmatch.group(5) or 999999),'use_potency':True}})
                supported.append(t); continue
            cmatch = re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(\d+)\s*당,?\s*합\s*위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?', generic_t)
            if cmatch:
                on_use.append({'type':'_skill_clash_power_condition_marker','condition':{'type':'status_sum_per','names':[STATUS[cmatch.group(1)]],'target':'enemy','per':int(cmatch.group(2)),'amount':int(cmatch.group(3)),'max':int(cmatch.group(4) or 999999),'use_potency':True}})
                supported.append(t); continue
            # Generic dynamic damage scaling: speed difference x target status potency.
            sm=re.search(r'자신의\s*속도가\s*대상보다\s*빠르면,?\s*\(대상과의\s*속도\s*차이\s*x\s*대상의\s*(출혈|화상|파열|침잠|진동)\s*위력\)\s*%?\s*만큼\s*피해량이?\s*증가\s*\(최대\s*(\d+(?:\.\d+)?)%\)',t)
            if sm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'speed_diff_status_damage','status':STATUS[sm.group(1)],'cap':float(sm.group(2))/100}}); supported.append(t); continue
            # Self lost-HP scaling, e.g. '잃은 체력 1%당 피해량 1% 증가 (최대 30%)'.
            sm=re.search(r'자신의\s*잃은\s*체력\s*1%당\s*피해량\s*([0-9]+(?:\.[0-9]+)?)%\s*증가(?:\s*\(최대\s*([0-9]+(?:\.[0-9]+)?)%\))?',t)
            if sm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'self_lost_hp_per','amount':float(sm.group(1))/100,'max':float(sm.group(2) or 999999)/100}}); supported.append(t); continue
            # Enemy lost-HP scaling. Preserve the source unit explicitly:
            # `대상의 잃은 체력 1% 당 피해량 +0.3% (최대 30%)` means each
            # percentage point of lost HP contributes 0.3% damage, capped at 30%.
            # Do this before the generic named-stack parser so `잃은 체력` is never
            # mistaken for an unnamed resource.
            sm=re.search(r'(?:메인\s*타겟|대상|적\(본체\))의\s*잃은\s*체력\s*(?:(\d+(?:\.\d+)?)%\s*당\s*)?피해량\s*(?:\+\s*)?(\d+(?:\.\d+)?)%\s*(?:증가)?(?:\s*\(최대\s*(\d+(?:\.\d+)?)%\))?',t)
            if sm:
                per=float(sm.group(1) or 1.0)
                amount=float(sm.group(2))/100.0
                cap=float(sm.group(3))/100.0 if sm.group(3) else 999999
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'enemy_lost_hp_per','per':per,'amount':amount,'max':cap}}); supported.append(t); continue
            sm=re.search(r'(?:메인\s*타겟|대상|적\(본체\))의\s*잃은\s*체력(?:\s*비율)?(?:만큼)?\s*피해량\s*(?:\+|증가)?(?:\s*\(최대\s*([0-9]+(?:\.[0-9]+)?)%\))?',t)
            if sm:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'enemy_lost_hp_ratio','cap':float(sm.group(1))/100 if sm.group(1) else 999999}}); supported.append(t); continue
            # Charge Count -> damage scaling. This is evaluated dynamically at coin timing.
            cmg = re.search(r'충전당\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%\s*\(최대\s*(\d+(?:\.\d+)?)%\)', generic_t)
            if cmg:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_per','resource':'충전','target':'self','per':1,'amount':float(cmg.group(1))/100,'max':float(cmg.group(2))/100}})
                supported.append(t); continue
            # Charge Potency -> damage scaling. Keep this on the Potency axis;
            # it must never read Charge Count.
            cpmg = re.search(r'\(\s*충전\s*위력\s*[x×]\s*(\d+(?:\.\d+)?)\s*\)%?\s*만큼\s*피해량\s*(?:이|가)?\s*증가\s*\(최대\s*(\d+(?:\.\d+)?)%\)', generic_t)
            if cpmg:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_per','resource':'충전 위력','target':'self','per':1,'amount':float(cpmg.group(1))/100,'max':float(cpmg.group(2))/100}})
                supported.append(t); continue
            # Natural-language equivalent: "충전 위력당 피해량 +X%".
            cpmg2 = re.search(r'충전\s*위력당\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%\s*\(최대\s*(\d+(?:\.\d+)?)%\)', generic_t)
            if cpmg2:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'resource_per','resource':'충전 위력','target':'self','per':1,'amount':float(cpmg2.group(1))/100,'max':float(cpmg2.group(2))/100}})
                supported.append(t); continue
            # Skill/coin critical-damage scaling from the sum of own Poise and
            # target status. This belongs to the SkillTextParser path too; passive
            # compiler support alone does not reach identity skill coin effects.
            xcm = re.search(r'크리티컬\s*피해량\s*\+\s*\(\s*자신의\s*호흡(?:\s*위력)?\s*\+\s*(?:대상의|메인\s*타겟의)\s*(화상|출혈|침잠|파열|진동)(?:\s*위력)?\s*\)\s*%', generic_t)
            if xcm:
                capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', generic_t)
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'cross_status_crit_damage_per','self_status':'Poise','enemy_status':STATUS.get(xcm.group(1),xcm.group(1)),'per':1,'amount':0.01,'max':float(capm.group(1))/100 if capm else 999999},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            xcm = re.search(r'자신의\s*호흡(?:\s*위력)?\s*\+\s*(?:대상의|메인\s*타겟의)\s*(화상|출혈|침잠|파열|진동)(?:\s*위력)?\s*\)?\s*1\s*당\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', generic_t)
            if xcm:
                capm = re.search(r'최대\s*(\d+(?:\.\d+)?)%', generic_t)
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'cross_status_crit_damage_per','self_status':'Poise','enemy_status':STATUS.get(xcm.group(1),xcm.group(1)),'per':1,'amount':float(xcm.group(2))/100,'max':float(capm.group(1))/100 if capm else 999999},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            # Self resource critical-damage scaling. `목표 조준` is a named
            # action resource, so reuse the existing named_stack_per condition
            # rather than introducing a resource-specific runtime.
            target_aim_crit = re.search(r'목표\s*조준\s*(\d+)\s*당,?\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if target_aim_crit:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'named_stack_per','name':'목표 조준','target':'self','field':'count','per':int(target_aim_crit.group(1)),'amount':float(target_aim_crit.group(2))/100,'max':float(target_aim_crit.group(3))/100 if target_aim_crit.group(3) else 999999},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            # Self stack critical-damage scaling.
            # `신속` is a count-based status, while `호흡` is represented by Poise potency.
            crit_speed = re.search(r'자신의\s*신속\s*(\d+)\s*당,?\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if crit_speed:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'named_stack_per','name':'신속','target':'self','field':'count','per':int(crit_speed.group(1)),'amount':float(crit_speed.group(2))/100,'max':float(crit_speed.group(3))/100 if crit_speed.group(3) else 999999},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            crit_poise = re.search(r'자신의\s*호흡\s*(?:위력)?\s*(\d+)\s*당,?\s*크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if crit_poise:
                on_use.append({'type':'_skill_condition_marker','condition':{'type':'named_stack_per','name':'호흡','target':'self','field':'potency','per':int(crit_poise.group(1)),'amount':float(crit_poise.group(2))/100,'max':float(crit_poise.group(3))/100 if crit_poise.group(3) else 999999},'effect':'crit_damage_bonus'})
                supported.append(t); continue
            # Absolute lost-HP scaling is different from percentage lost-HP scaling.
            # Preserve the source's unit (`잃은 체력 1당`) rather than interpreting
            # it as one percentage point of missing HP.
            lost_hp_flat = re.search(r'자신의\s*잃은\s*체력\s*(\d+(?:\.\d+)?)\s*당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%(?:.*?최대\s*(\d+(?:\.\d+)?)%)?', generic_t)
            if lost_hp_flat:
                on_use.append({'type':'_skill_damage_condition_marker','condition':{'type':'self_lost_hp_flat_per','per':float(lost_hp_flat.group(1)),'amount':float(lost_hp_flat.group(2))/100,'max':float(lost_hp_flat.group(3))/100 if lost_hp_flat.group(3) else 999999}})
                supported.append(t); continue
            # Static critical-damage bonus.  Unlike conditional crit modifiers,
            # this applies whenever the coin is critical and is independent of
            # target state.
            cdb = re.search(r'^크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%$', generic_t)
            if cdb:
                on_use.append({'type':'_skill_static_crit_damage_bonus','amount':float(cdb.group(1))/100})
                supported.append(t); continue
            # Ammo consumed by this skill -> base power.  The amount is resolved
            # from the actual planned per-coin ammo consumption at action start.
            abp = re.search(r'이 스킬에서\s*소모할\s*탄환\s*(\d+)\s*당\s*기본\s*위력\s*\+\s*(\d+)', generic_t)
            if abp:
                on_use.append({'type':'_skill_base_power_from_ammo','per':int(abp.group(1)),'amount':int(abp.group(2))})
                supported.append(t); continue
            # Conditional damage based on the number of negative effects on the target.
            nm=re.search(r'대상의\s*부정적인\s*효과\s*(\d+)개당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%.*?최대\s*(\d+(?:\.\d+)?)%',t)
            if nm:
                on_use.append({"type":"_skill_damage_condition_marker","condition":{"type":"negative_status_count_per","per":int(nm.group(1)),"amount":float(nm.group(2))/100,"max":float(nm.group(3))/100}}); supported.append(t); continue
            # Conditional damage/critical-damage modifiers tied to the target's
            # current stagger state. These are evaluated at coin timing, so a
            # previous coin can newly stagger the target and enable later coins.
            scm = re.search(r'대상(?:이|이)\s*흐트러짐\s*상태(?:면|라면).*?크리티컬\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', t)
            if scm:
                on_use.append({"type":"_skill_condition_marker","condition":{"type":"enemy_staggered"},"crit_damage_bonus":float(scm.group(1))/100,"effect":"crit_damage_bonus"}); supported.append(t); continue
            smd = re.search(r'대상(?:이|이)\s*흐트러짐\s*상태(?:면|라면).*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', t)
            if smd:
                on_use.append({"type":"_skill_condition_marker","condition":{"type":"enemy_staggered"},"damage_bonus":float(smd.group(1))/100}); supported.append(t); continue
            smn = re.search(r'대상(?:이|이)\s*흐트러짐\s*상태(?:가|이)\s*아니면.*?피해량\s*\+\s*(\d+(?:\.\d+)?)%', t)
            if smn:
                on_use.append({"type":"_skill_condition_marker","condition":{"type":"enemy_not_staggered"},"damage_bonus":float(smn.group(1))/100}); supported.append(t); continue
            # Skill-level explicit Tremor Amplitude conversion/entanglement.
            # These catalog bullets may be unnumbered (e.g. "- 진동 - 작열이
            # 없으면...") and therefore do not pass through coin parsing.
            amp = self._amplitude_effect(t.lstrip('- ').strip())
            if amp:
                on_use.append(amp); supported.append(t); continue
            # Static per-skill conditional coin power.
            if "코인 위력" in t:
                c=self._coin_condition(t)
                if c:
                    supported.append(t); on_use.append({"type":"_skill_condition_marker","condition":c}); pending_condition=None; continue
                if pending_condition and re.search(r'코인 위력\s*\+\s*(\d+)',t):
                    c=dict(pending_condition); c["amount"]=int(re.search(r'코인 위력\s*\+\s*(\d+)',t).group(1))
                    supported.append(t); on_use.append({"type":"_skill_condition_marker","condition":c})
                    # A source line such as `자신의 속도가 대상보다 높으면,`
                    # introduces a bullet block. Keep that gate for subsequent
                    # dash-prefixed modifiers instead of applying it to only the
                    # first bullet. A non-bullet effect below will naturally end
                    # the block.
                    if not t.lstrip().startswith('-'):
                        pending_condition=None
                    continue
            unsupported.append(t)
        if pending_reuse_hit_effects and last_coin_reuse_rules:
            last_coin_reuse_rules[-1].setdefault('reuse_hit_effects', []).extend(pending_reuse_hit_effects)
            pending_reuse_hit_effects=[]
        return {"effects_on_use":on_use,"coin_defs":coins,"coin_target_policies":coin_target_policies,"last_coin_reuse_rules":last_coin_reuse_rules,"last_coin_damage_rules":last_coin_damage_rules,"kill_reuse_rules":kill_reuse_rules,"pending_reuse_hit_effects":pending_reuse_hit_effects,"added_coin_rules":added_coin_rules}, ParseReport(supported,unsupported)

    def _amplitude_effect(self, body: str):
        """Parse source-backed Tremor Amplitude conversion/entanglement clauses.

        This is intentionally limited to explicit identity text.  It does not
        infer conversion targets or consume Tremor unless the source says so.
        """
        # Explicit condition: target must not already have a conversion state.
        m = re.search(r'대상이\s*진폭\s*변환\s*상태가?\s*아니면,?\s*진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*변환', body)
        if m:
            return {
                "type": "amplitude_conversion",
                "amplitude": m.group(1).strip(),
                "target": "enemy",
                "condition": {"type": "not", "condition": {"type": "has_amplitude_state", "mode": "conversion", "target": "enemy"}},
            }
        # Explicit Tremor potency+Count threshold used by 1070803.
        m = re.search(r'대상의\s*진동\s*위력과\s*횟수의\s*합이\s*(\d+)\s*이상(?:이면|이라면),?\s*진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*변환', body)
        if m:
            return {
                "type": "amplitude_conversion",
                "amplitude": m.group(2).strip(),
                "target": "enemy",
                "condition": {"type": "tremor_potency_count_sum_gte", "value": int(m.group(1)), "target": "enemy"},
            }
        # Explicit speed condition used by 1030903.
        m = re.search(r'대상의\s*속도가\s*자신보다\s*낮다면,?\s*진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*변환', body)
        if m:
            return {
                "type": "amplitude_conversion",
                "amplitude": m.group(1).strip(),
                "target": "enemy",
                "condition": {"type": "speed_difference_gte", "value": 1},
            }
        # Explicit named-amplitude absence condition used by 1021635.
        m = re.search(r'진동\s*[-–—:]?\s*([^,\.\n]+?)\s*이\s*없으면,?\s*진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*변환', body)
        if m:
            return {
                "type": "amplitude_conversion",
                "amplitude": m.group(2).strip(),
                "target": "enemy",
                "condition": {"type": "not", "condition": {"type": "has_amplitude_state", "amplitude": m.group(1).strip(), "mode": "conversion", "target": "enemy"}},
            }
        # Plain explicit conversion.
        m = re.search(r'진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*변환', body)
        if m:
            return {"type": "amplitude_conversion", "amplitude": m.group(1).strip(), "target": "enemy"}
        # Explicit entanglement.
        m = re.search(r'진동\s*[-–—:]?\s*([^,\.\n]+?)\s*(?:으?로|로)\s*진폭\s*얽힘', body)
        if m:
            return {"type": "amplitude_entanglement", "amplitude": m.group(1).strip(), "target": "enemy"}
        # Existing catalog/compiler vocabulary sometimes refers to the current
        # Tremor as the entanglement source without naming a concrete amplitude.
        if re.search(r'대상의\s*현재\s*진동으로\s*진폭\s*얽힘', body):
            return {"type": "amplitude_entanglement", "amplitude": "current_tremor", "target": "enemy"}
        return None

    def _status_effect(self, body:str):
        m=re.search(r'흐트러짐\s*손상\s*(\d+)',body)
        if m: return {"type":"stagger_damage","amount":int(m.group(1))}
        amp = self._amplitude_effect(body)
        if amp:
            return amp
        # Source-backed dynamic Tremor transfers. These are intentionally
        # narrow: only explicit identity text is converted.
        m = re.search(r'대상의\s*진동을\s*최대\s*(\d+)\s*소모.*?소모한\s*진동\s*[x×*]\s*(\d+)\)?만큼\s*자신의\s*진동\s*횟수\s*증가', body, re.S)
        if m:
            return {"type":"tremor_consume_target_to_self","target":"enemy","cap":int(m.group(1)),"multiplier":int(m.group(2))}
        m = re.search(r'자신의\s*진동\s*횟수를\s*(?:최대\s*)?(\d+)\s*소모.*?소모한\s*진동\s*횟수만큼\s*대상의\s*진동\s*횟수\s*증가', body, re.S)
        if m:
            return {"type":"tremor_consume_self_to_target","target":"enemy","cap":int(m.group(1))}
        if re.search(r'자신의\s*진동\s*횟수를\s*전부\s*소모하여,?\s*소모한\s*값만큼\s*대상(?:의)?\s*진동\s*횟수', body):
            return {"type":"tremor_consume_self_to_target","target":"enemy","cap":999999}
        # Explicit Tremor Burst / status-trigger effects. These are resolved
        # at the hit timing. Count loss is a separate source-explicit effect.
        mb=re.search(r'(진동)\s*폭발(?:\s*(\d+)\s*회)?',body)
        if mb:
            effect={"type":"tremor_burst","name":"Tremor"}
            # Burst itself does not imply Count consumption. Count loss is a
            # separate, source-explicit effect and must only be attached when
            # the identity text explicitly states it. Support both
            # "Burst. Count N 감소" and "Burst 시 Count N 감소" forms.
            cm = re.search(r'진동\s*폭발(?:\s*시)?(?:\s*\d+\s*회)?(?:\.|,)?\s*(?:대상의\s*)?진동\s*횟수\s*(\d+)\s*감소', body, re.S)
            if cm:
                effect["count_cost"]=int(cm.group(1))
            # A source clause may explicitly request multiple Bursts. This is
            # distinct from Count cost: e.g. Burst 2 times + Count 1 decrease.
            if mb.group(2):
                effect["burst_count"]=int(mb.group(2))
            return effect
        for ko,en in STATUS.items():
            if ko in ('화상','파열','침잠'):
                mb=re.search(re.escape(ko)+r'\s*발동(?:\.\s*대상의\s*'+re.escape(ko)+r'\s*횟수\s*1\s*감소)?',body)
                if mb: return {"type":"status_burst","name":en,"count_cost":1}
            m=re.search(re.escape(ko)+r'\s*(?:위력\s*)?(\d+)\s*부여',body)
            if m: return {"type":"status","name":en,"potency":int(m.group(1))}
            # Source semantics: explicit status count wording maps to count;
            # bare/"추가 부여" wording maps to potency.
            m=re.search(re.escape(ko)+r'\s*횟수\s*(\d+)\s*(?:증가|추가|부여)',body)
            if m: return {"type":"status","name":en,"count":int(m.group(1))}
            m=re.search(re.escape(ko)+r'\s*(\d+)\s*(?:추가\s*)?부여',body)
            if m: return {"type":"status","name":en,"potency":int(m.group(1))}
            m=re.search(re.escape(ko)+r'\s*(\d+)\s*추가로?\s*(?:얻음|부여)',body)
            if m: return {"type":"status","name":en,"potency":int(m.group(1))}
            m=re.search(re.escape(ko)+r'\s*(\d+)\s*얻음',body)
            if m: return {"type":"status","name":en,"potency":int(m.group(1))}
        return None

    def _use_effect(self, body:str):
        out=[]
        # Dynamic Clash Power from Charge Potency. Potency is a distinct
        # resource axis and must be read from charge_potency, not Charge Count.
        mcp = re.search(r'자신의\s*충전\s*위력만큼\s*합\s*위력이\s*증가(?:\s*\(최대\s*(\d+)\))?', body)
        if mcp:
            out.append({"type":"_skill_clash_power_dynamic_marker","condition":{"type":"resource_value","resource":"충전 위력","max":int(mcp.group(1)) if mcp.group(1) else 999999}})
            return out
        # Fixed resource consumption that directly grants skill-wide Coin Power.
        # The resource cost is applied at action start; the resulting Coin Power
        # marker is unconditional because the source text explicitly couples
        # the two operations.
        rp='|'.join(re.escape(x) for x in sorted(self.SPECIAL_RESOURCE_NAMES | {"호흡","충전","탄환"}, key=len, reverse=True))
        mc=re.search(r'('+rp+r')\s*(?:횟수\s*)?(?:를\s*)?(\d+)\s*소모(?:하여|해서|하고),?\s*(?:이\s*스킬의\s*)?코인 위력\s*\+(\d+)',body)
        if mc:
            out.append({"type":"resource_cost","resource":mc.group(1),"amount":int(mc.group(2))})
            out.append({"type":"_skill_condition_marker","condition":{"type":"always","amount":int(mc.group(3))}})
        for ko,typ in [("호흡","poise"),("충전","charge"),("탄환","ammo")]:
            m=re.search(re.escape(ko)+r'(\s*횟수)?\s*(\d+)\s*(?:증가|얻음|소모)',body)
            if m:
                n=int(m.group(2));
                if "소모" in m.group(0): n=-n
                if typ!="poise":
                    out.append({"type":typ,"amount":n})
                else:
                    out.append({"type":"poise", "count":n} if m.group(1) else {"type":"poise", "potency":n})
        for ko,en in STATUS.items():
            m=re.search(re.escape(ko)+r'\s*(?:위력\s*)?(\d+)\s*(?:부여|얻음)',body)
            if m: out.append({"type":"status","name":en,"potency":int(m.group(1))})
        for ko,en in STATUS.items():
            m=re.search(r'자신의\s*'+re.escape(ko)+r'\s*횟수\s*(\d+)\s*(증가|추가)',body)
            if m: out.append({"type":"status","name":en,"count":int(m.group(1)),"target":"self"})
        lm=re.search(r"(?:자신의\s*)?(%s)(?:\s*횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?마지막\s*코인\s*재사용" % '|'.join(re.escape(x) for x in sorted(self.SPECIAL_RESOURCE_NAMES,key=len,reverse=True)), body)
        if lm:
            out.append({"type":"last_coin_reuse", "condition":{"type":"resource_gte","resource":lm.group(1),"value":int(lm.group(2))}, "max_reuses":1})
        else:
            lm=re.search(r"(?:마지막\s*코인\s*재사용).*?(?:스킬당\s*)?(?:최대\s*)?(\d+)회", body)
            if lm:
                out.append({"type":"last_coin_reuse", "condition":{"type":"always"}, "max_reuses":int(lm.group(1))})
            elif "마지막 코인 재사용" in body:
                out.append({"type":"last_coin_reuse", "condition":{"type":"always"}, "max_reuses":1})
        # Explicit resource conversion patterns.  These are intentionally
        # limited to unambiguous numeric conversions because they directly
        # affect the resource state used by later coins/actions.
        resource_names = sorted(self.SPECIAL_RESOURCE_NAMES, key=len, reverse=True)
        conversion_names = resource_names + ['호흡','충전','탄환','포자탄[기본]','포자탄[산탄]','깊은 눈물','탐구한 지식','지식 단련','사랑/증오','전투 감각']
        conversion_names = sorted(set(conversion_names), key=len, reverse=True)
        rp = '|'.join(re.escape(x) for x in conversion_names)
        conversion_resources = set()
        # Example: "가속탄 소모한 수치 1당, 호흡 2 얻음".  The actual source
        # resource consumption is calculated by the skill/coin costs first;
        # the runtime later converts the amount actually consumed.
        m = re.search(r'('+rp+r')\s*소모한\s*수치\s*(\d+)\s*당,?\s*('+rp+r')\s*(\d+)\s*(?:얻음|획득|증가)', body)
        if m:
            conversion_resources.update((m.group(1), m.group(3)))
            out.append({'type':'resource_gain_from_consumed','source':m.group(1),
                        'source_per':int(m.group(2)), 'target':m.group(3),
                        'target_amount':int(m.group(4))})
        # Example: "포자탄[기본] 2 소모하여, 포자탄[산탄] 1 얻음".
        m = re.search(r'('+rp+r')\s*(\d+)\s*소모(?:하여|하고),?\s*('+rp+r')\s*(\d+)\s*(?:얻음|획득|증가)', body)
        if m:
            conversion_resources.update((m.group(1), m.group(3)))
            out.append({'type':'resource_convert','source':m.group(1),
                        'source_amount':int(m.group(2)), 'target':m.group(3),
                        'target_amount':int(m.group(4))})
        # Identity-specific resources are deliberately separate from normal
        # statuses.  Only names in the reviewed candidate vocabulary are
        # parsed here; unknown prose is left unsupported rather than guessed.
        for resource in sorted(self.SPECIAL_RESOURCE_NAMES, key=len, reverse=True):
            if resource in conversion_resources:
                continue
            # Conditional fixed consumption: e.g. 'X가 10 이상이면, X 5 소모'.
            cm=re.search(r'자신의\s*'+re.escape(resource)+r'(?:\s*횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?'+re.escape(resource)+r'(?:\s*횟수)?(?:을|를|이|가|은|는)?\s*(\d+)\s*소모',body)
            if cm:
                out.append({"type":"resource_conditional_cost","resource":resource,"threshold":int(cm.group(1)),"amount":int(cm.group(2)),"operator":">="})
                continue
            # Conditional dynamic consumption: X >= N -> consume up to M.
            cm2=re.search(r'자신의\s*'+re.escape(resource)+r'(?:\s*횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?'+re.escape(resource)+r'(?:\s*횟수)?(?:을|를|이|가|은|는)?\s*최대\s*(\d+)\s*까지\s*소모',body)
            if cm2:
                out.append({"type":"resource_conditional_cost_max","resource":resource,"threshold":int(cm2.group(1)),"amount":int(cm2.group(2)),"operator":">="})
                continue
            # Fixed gain/consume.
            m=re.search(re.escape(resource)+r'\s*(?:횟수|위력)?\s*(\d+)\s*(증가|얻음|소모)',body)
            if m:
                amount=int(m.group(1)); op=m.group(2)
                key="resource_gain" if op in ("증가","얻음") else "resource_cost"
                out.append({"type":key,"resource":resource,"amount":amount})
                continue
            # Dynamic forms: "최대 N까지 소모" and "전부 소모".
            m=re.search(re.escape(resource)+r'(?:\s*횟수)?\s*(?:을|를)?\s*최대\s*(\d+)\s*까지\s*소모',body)
            if m: out.append({"type":"resource_cost_max","resource":resource,"amount":int(m.group(1))}); continue
            m=re.search(re.escape(resource)+r'\s*전부\s*소모',body)
            if m: out.append({"type":"resource_cost_all","resource":resource}); continue
        return out

    def _coin_condition(self,t:str):
        # High-impact conditional coin-power patterns. These are evaluated at
        # COIN_START, so earlier coins/actions can change the later result.
        m=re.search(r'자신의\s*충전\s*위력이\s*(\d+)\s*이상이면,?\s*코인 위력\s*\+\s*(\d+)',t)
        if m:
            return {"type":"resource_gte","resource":"충전 위력","value":int(m.group(1)),"amount":int(m.group(2))}
        m=re.search(r'(호흡|출혈|파열|진동|침잠|화상|충전)\s*(?:횟수|위력)?\s*(\d+)당,?\s*코인 위력\s*\+\s*(\d+)\s*\(최대\s*(\d+)\)',t)
        if m:
            ko=m.group(1); st=STATUS[ko]; use_potency=ko not in ('호흡','충전')
            return {"type":"status_count_per","target":"self" if ko in ('호흡','충전') else "enemy","name":st,"per":int(m.group(2)),"amount":int(m.group(3)),"max":int(m.group(4)),"use_potency":use_potency}
        m=re.search(r'자신의\s*호흡과\s*대상의\s*(침잠|진동|출혈|화상|파열)\s*의?\s*합\s*(\d+)당,?\s*코인 위력\s*\+\s*(\d+)\s*\(최대\s*(\d+)\)',t)
        if m:
            return {"type":"status_sum_per","target":"mixed","names":["Poise",STATUS[m.group(1)]],"per":int(m.group(2)),"amount":int(m.group(3)),"max":int(m.group(4)),"use_potency":False}
        m=re.search(r'자신의\s*(호흡)\s*(?:와|과)\s*대상의\s*(침잠|진동|출혈|화상|파열)\s*의?\s*합',t)
        if m:
            # handled above only when the numerical threshold is present
            pass
        m=re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)\s*(?:과|와)\s*(출혈|화상|파열|침잠|진동)\s*의?\s*합\s*(\d+)당,?\s*코인 위력\s*\+\s*(\d+)\s*\(최대\s*(\d+)\)',t)
        if m:
            return {"type":"status_sum_per","target":"enemy","names":[STATUS[m.group(1)],STATUS[m.group(2)]],"per":int(m.group(3)),"amount":int(m.group(4)),"max":int(m.group(5)),"use_potency":True}
        m=re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)\s*(\d+)\s*당.*?코인 위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?',t)
        if m:
            return {"type":"status_count_per","target":"enemy","name":STATUS[m.group(1)],"per":int(m.group(2)),"amount":int(m.group(3)),"max":int(m.group(4) or 999999),"use_potency":True}
        m=re.search(r'대상의\s*(출혈|화상|파열|침잠|진동)\s*(?:이|가)\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m:
            return {"type":"status_threshold","target":"enemy","name":STATUS[m.group(1)],"field":"potency","value":int(m.group(2)),"amount":int(m.group(3))}
        # Main-target aliases are equivalent to the current enemy target in the
        # one-target damage model. Support both potency and count explicitly.
        m=re.search(r'(?:메인\s*타겟|대상)의?\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m:
            return {"type":"status_threshold","target":"enemy","name":STATUS[m.group(1)],"field":"potency","value":int(m.group(2)),"amount":int(m.group(3))}
        m=re.search(r'(?:메인\s*타겟|대상)의?\s*(출혈|화상|파열|침잠|진동)\s*횟수(?:가|는|이)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m:
            return {"type":"status_threshold","target":"enemy","name":STATUS[m.group(1)],"field":"count","value":int(m.group(2)),"amount":int(m.group(3))}
        # Generic self + target status potency/count sum -> coin power.
        m=re.search(r'자신의\s*(호흡|화상|출혈|파열|침잠|진동)\s*(?:위력|횟수)?\s*(?:와|과)\s*(?:메인\s*타겟|대상)의?\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|횟수)?\s*의?\s*합\s*(\d+)\s*당.*?코인 위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?',t)
        if m:
            first=m.group(1); second=m.group(2)
            names=[STATUS[first],STATUS[second]]
            use_potency=first not in ('호흡',) and second not in ('호흡',)
            return {"type":"status_sum_per","target":"mixed","names":names,"per":int(m.group(3)),"amount":int(m.group(4)),"max":int(m.group(5) or 999999),"use_potency":use_potency}
        # Generic two-target-side status sum.
        m=re.search(r'(?:대상의|메인\s*타겟의)\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*(?:와|과)\s*(출혈|화상|파열|침잠|진동)\s*(?:위력|수치)?\s*의?\s*합\s*(\d+)\s*당.*?코인 위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?',t)
        if m:
            return {"type":"status_sum_per","target":"enemy","names":[STATUS[m.group(1)],STATUS[m.group(2)]],"per":int(m.group(3)),"amount":int(m.group(4)),"max":int(m.group(5) or 999999),"use_potency":True}
        # Self lost-HP percentage -> coin power.
        m=re.search(r'자신의\s*잃은\s*체력\s*(\d+(?:\.\d+)?)%\s*당.*?코인 위력\s*\+\s*(\d+)(?:\s*\(최대\s*(\d+)\))?',t)
        if m:
            return {"type":"self_lost_hp_per_coin","per_pct":float(m.group(1)),"amount":int(m.group(2)),"max":int(m.group(3) or 999999)}
        m=re.search(r'자신의\s*속도가\s*대상보다\s*(\d+)\s*이상\s*높으면.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"speed_difference_gte","value":int(m.group(1)),"amount":int(m.group(2))}
        m=re.search(r'대상의\s*속도가\s*자신보다\s*(\d+)\s*이상\s*높으면.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"speed_difference_lte","value":-int(m.group(1)),"amount":int(m.group(2))}
        m=re.search(r'대상의\s*속도가\s*자신보다\s*(?:느리|낮).*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"speed_difference_gte","value":1,"amount":int(m.group(1))}
        m=re.search(r'충전\s*횟수가?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"charge_gte","value":int(m.group(1)),"amount":int(m.group(2))}
        m=re.search(r'자신의\s*호흡(?:이|은|는)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"poise_gte","value":int(m.group(1)),"amount":int(m.group(2))}
        m=re.search(r'충전(?:이|은|는)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"charge_gte","value":int(m.group(1)),"amount":int(m.group(2))}
        # Generic self status threshold -> coin power.
        m=re.search(r'자신의\s*(화상|출혈|파열|침잠|진동)\s*(?:위력|횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m:
            field='count' if '횟수' in m.group(0) else 'potency'
            return {"type":"status_threshold","target":"self","name":STATUS[m.group(1)],"field":field,"value":int(m.group(2)),"amount":int(m.group(3))}
        m=re.search(r'자신의\s*속도가(?:이|가|은|는)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"speed_gte","value":int(m.group(1)),"amount":int(m.group(2))}
        # Generic identity-specific resource threshold -> coin power.
        rp='|'.join(re.escape(x) for x in sorted(SkillTextParserV19.SPECIAL_RESOURCE_NAMES,key=len,reverse=True))
        m=re.search(r'자신의\s*('+rp+r')\s*(?:횟수)?(?:이|가|은|는)?\s*(\d+)\s*이상.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"resource_gte","resource":m.group(1),"value":int(m.group(2)),"amount":int(m.group(3))}
        m=re.search(r'자신의\s*('+rp+r')\s*(?:횟수)?(?:이|가|은|는)?\s*(\d+)\s*이하.*?코인 위력\s*\+\s*(\d+)',t)
        if m: return {"type":"resource_lte","resource":m.group(1),"value":int(m.group(2)),"amount":int(m.group(3))}
        m=re.search(r'자신의\s*속도가\s*대상보다\s*높을수록.*?속도 차이\s*(\d+)\s*당\s*코인 위력\s*\+\s*(\d+).*?최대\s*(\d+)',t)
        if m: return {"type":"speed_difference_per","direction":"higher","per":int(m.group(1)),"amount":int(m.group(2)),"max":int(m.group(3))}
        m=re.search(r'속도 차이\s*(\d+)\s*당\s*코인 위력\s*\+\s*(\d+).*?최대\s*(\d+)',t)
        if m: return {"type":"speed_difference_per","direction":"higher","per":int(m.group(1)),"amount":int(m.group(2)),"max":int(m.group(3))}
        return None
