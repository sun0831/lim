"""Identity catalog construction for the v29 one-turn calculator.

Extracted from the solver as a behavior-preserving C-phase split.
"""
from __future__ import annotations
import json
import re
from copy import deepcopy
from typing import Any

from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData
from skill_text_parser_v19 import SkillTextParserV19

SIN = {"lust":"lust","envy":"envy","wrath":"wrath","sloth":"sloth","gluttony":"gluttony","gloom":"gloom","pride":"pride",
       "색욕":"lust","질투":"envy","분노":"wrath","나태":"sloth","폭식":"gluttony","우울":"gloom","오만":"pride"}
ATK={"참격":"slash","관통":"pierce","타격":"blunt","slash":"slash","pierce":"pierce","blunt":"blunt"}

class IdentityCatalogV29:
    def __init__(self, records): self.records={str(r['id']):r for r in records}; self.by_name={str(r['name']):r for r in records}
    @classmethod
    def from_json(cls,path='identity_database_v2.json'):
        return cls(json.load(open(path,encoding='utf-8'))['identities'])
    def get_record(self,key): return self.records.get(str(key),self.by_name.get(str(key))) or (_ for _ in ()).throw(KeyError(key))
    def build_identity(self,key,offense_level=0,level=60,speed=None):
        r=self.get_record(key); skills={}; parser=SkillTextParserV19(); parse_meta={}
        raw_skills=r.get('skills',{}) or {}
        if isinstance(raw_skills, list):
            skill_items=[(str(s.get('slot', 'S'+str(i+1))), s) for i,s in enumerate(raw_skills)]
        else:
            skill_items=list(raw_skills.items())
        # Defense skills are executable skills too. Include them in the same
        # IdentityData catalog so generated defense/forecast skills (e.g. 예지)
        # can be resolved by name/ID without inventing a separate action model.
        raw_defense=r.get('defenseSkills', r.get('defense_skills', [])) or []
        if isinstance(raw_defense, list):
            for i, ds in enumerate(raw_defense):
                dslot=str(ds.get('slot', '수비 '+str(i+1)))
                skill_items.append((dslot, ds))
        elif isinstance(raw_defense, dict):
            skill_items.extend((str(k),v) for k,v in raw_defense.items())
        stats=r.get('stats',{}) or {}
        def first_int(value, default):
            m=re.search(r'-?\d+', str(value)) if value is not None else None
            return int(m.group()) if m else default
        for slot,s in skill_items:
            # v2 catalog uses camelCase fields; retain compatibility with the older snake_case form.
            cps=s.get('coin_powers') or s.get('coinPowers') or [s.get('coin_power',s.get('coinPower',0))]*int(s.get('coin_count',s.get('coinCount',0)))
            cps=list(cps or [])
            parsed,rep=parser.parse(s.get('effects',[]) or [],len(cps)); coins=[]
            kill_reuse_rules = list(parsed.get('kill_reuse_rules', []))
            added_coin_rules = list(parsed.get('added_coin_rules', []))
            attack_raw=s.get('attack_type',s.get('attackType','slash'))
            sin_raw=s.get('sin',s.get('affinity',''))
            for i,cp in enumerate(cps):
                q=parsed['coin_defs'][i]; coins.append(CoinData(int(cp),ATK.get(attack_raw,attack_raw),SIN.get(sin_raw,sin_raw),unbreakable=bool(q.get('unbreakable',False)),damage_bonus=float(q.get('damage_bonus',0.0)),crit_damage_bonus=float(q.get('crit_damage_bonus',0.0)),stagger_damage_ratio=float(q.get('stagger_damage_ratio',0.0)),effects=q['effects'],heads_effects=q['heads_effects'],tails_effects=q['tails_effects'],damage_conditions=deepcopy(q.get('damage_conditions',[])),resource_cost=dict(q.get('resource_cost',{})),resource_cost_max=dict(q.get('resource_cost_max',{})),resource_cost_all=list(q.get('resource_cost_all',[]))))
            markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_condition_marker"]
            damage_markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_damage_condition_marker"]
            final_markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_final_power_condition_marker"]
            clash_power_markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_clash_power_condition_marker"]
            dynamic_clash_power_markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_clash_power_dynamic_marker"]
            unbreakable_markers=[e for e in parsed["effects_on_use"] if e.get("type")=="_skill_unbreakable_condition_marker"]
            final_marker=next((e for e in parsed["effects_on_use"] if e.get("type")=="final_power_marker"),None)
            parsed_use=[e for e in parsed['effects_on_use'] if e.get('type') not in ('_skill_condition_marker','final_power_marker','effects_on_clash_win','effects_on_clash_lose')]
            clash_win_effects=[e.get('effect') for e in parsed['effects_on_use'] if e.get('type')=='effects_on_clash_win' and e.get('effect')]
            clash_lose_effects=[e.get('effect') for e in parsed['effects_on_use'] if e.get('type')=='effects_on_clash_lose' and e.get('effect')]
            last_coin_reuse_rules = list(parsed.get('last_coin_reuse_rules', []))
            last_coin_reuse_rules.extend({k:v for k,v in e.items() if k!='type'} for e in parsed_use if e.get('type')=='last_coin_reuse')
            parsed_use=[e for e in parsed_use if e.get('type')!='last_coin_reuse']
            resource_cost={e['resource']:int(e['amount']) for e in parsed_use if e.get('type')=='resource_cost'}
            resource_gain={e['resource']:int(e['amount']) for e in parsed_use if e.get('type')=='resource_gain'}
            resource_cost_max={e['resource']:int(e['amount']) for e in parsed_use if e.get('type')=='resource_cost_max'}
            resource_cost_all=[e['resource'] for e in parsed_use if e.get('type')=='resource_cost_all']
            resource_conditional_costs=[e for e in parsed_use if e.get('type')=='resource_conditional_cost']
            resource_conditional_cost_max=[e for e in parsed_use if e.get('type')=='resource_conditional_cost_max']
            consumption_bonus = {}
            static_crit_bonus = sum(float(e.get('amount',0.0)) for e in parsed_use if e.get('type')=='_skill_static_crit_damage_bonus')
            ammo_base_power_rules = [e for e in parsed_use if e.get('type')=='_skill_base_power_from_ammo']
            parsed_use = [e for e in parsed_use if e.get('type') not in ('_skill_static_crit_damage_bonus','_skill_base_power_from_ammo')]
            source_text = " | ".join(str(x) for x in (s.get('effects',[]) or []))
            resource_pattern = '|'.join(re.escape(x) for x in sorted(SkillTextParserV19.SPECIAL_RESOURCE_NAMES,key=len,reverse=True))
            for rb in re.finditer(r'(' + resource_pattern + r').*?소모한\s*수치\s*1당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', source_text):
                consumption_bonus[rb.group(1)] = float(rb.group(2)) / 100.0
            if '소모한 수치 1당' in source_text and not consumption_bonus:
                inferred = list(resource_conditional_cost_max) or list(resource_conditional_costs)
                if len(inferred) == 1:
                    mrb=re.search(r'소모한\s*수치\s*1당,?\s*피해량\s*\+\s*(\d+(?:\.\d+)?)%', source_text)
                    if mrb:
                        consumption_bonus[str(inferred[0]['resource'])] = float(mrb.group(1))/100.0
            skill=SkillData(id=str(s.get('id',slot)),name=s.get('name',slot),base_power=int(s.get('base_power',s.get('basePower',0))),coins=coins,attack_type=ATK.get(attack_raw,attack_raw),sin=SIN.get(sin_raw,sin_raw),effects_on_use=[e for e in parsed_use if e.get('type') not in ('resource_cost','resource_gain','resource_cost_max','resource_cost_all','resource_conditional_cost')],effects_on_clash_win=clash_win_effects,effects_on_clash_lose=clash_lose_effects,resource_cost=resource_cost,resource_gain=resource_gain,resource_cost_max=resource_cost_max,resource_cost_all=resource_cost_all,resource_conditional_costs=resource_conditional_costs,resource_conditional_cost_max=resource_conditional_cost_max,resource_consumption_damage_per=consumption_bonus,coin_ammo_spend={i+1:q.get('ammo_spend',0) for i,q in enumerate(parsed['coin_defs']) if q.get('ammo_spend',0)},crit_damage_bonus=static_crit_bonus,final_power_bonus=int(final_marker.get('amount',0)) if final_marker else 0,attack_weight=max(1,int(s.get('weight',1) or 1)),coin_target_policies=list(parsed.get('coin_target_policies',[])),last_coin_reuse_rules=deepcopy(last_coin_reuse_rules),last_coin_damage_rules=deepcopy(parsed.get('last_coin_damage_rules', [])),kill_reuse_rules=deepcopy(kill_reuse_rules),added_coin_rules=deepcopy(added_coin_rules))
            skill._source_effects=list(s.get('effects',[]) or []); skill._parse_report=rep; skill._slot=str(slot); skill._ammo_base_power_rules=deepcopy(ammo_base_power_rules)
            skill.conditions=[{"effect":"coin_power","condition":e["condition"],"amount":int(e["condition"].get("amount",1))} for e in markers]
            for e in markers:
                if e.get("type") == "_skill_condition_marker":
                    if "damage_bonus" in e:
                        skill.conditions.append({"effect":"damage_bonus","condition":e["condition"],"amount":float(e["damage_bonus"])})
                    if "crit_damage_bonus" in e:
                        skill.conditions.append({"effect":"crit_damage_bonus","condition":e["condition"],"amount":float(e["crit_damage_bonus"])})
            skill.conditions.extend({"effect":"damage_bonus","condition":e["condition"],"amount":float(e["condition"].get("amount",0.0)),"max":float(e["condition"].get("max",999999))} for e in damage_markers)
            skill.conditions.extend({"effect":"final_power","condition":e["condition"],"amount":int(e["condition"].get("amount",0)),"max":int(e["condition"].get("max",999999))} for e in final_markers)
            skill.conditions.extend({"effect":"clash_power","condition":e["condition"],"amount":int(e["condition"].get("amount",0)),"max":int(e["condition"].get("max",999999))} for e in clash_power_markers)
            skill.conditions.extend({"effect":"clash_power_dynamic","condition":e["condition"],"amount":0,"max":int(e["condition"].get("max",999999))} for e in dynamic_clash_power_markers)
            skill.conditions.extend({"effect":"unbreakable","condition":e["condition"]} for e in unbreakable_markers)
            skill_key=str(slot)
            if skill_key in skills:
                skill_key=str(skill.id)
                if skill_key in skills:
                    skill_key=f'{skill_key}#{i+1}'
            skills[skill_key]=skill; parse_meta[skill_key]={'slot':str(slot),'supported':rep.supported,'unsupported':rep.unsupported}
        ident=IdentityData(str(r['id']),r['name'],int(offense_level or 0),skills,r.get('passives',[])); ident._parse_meta=parse_meta; ident._catalog_meta={'defaulted_offense_level':True}
        ident.full_name = str(r.get('fullName', r.get('full_name', r.get('name', r['id']))))
        ident.affiliation = list(r.get('affiliation',[]) or [])
        if speed is not None: ident._scenario_speed=speed
        else: ident._scenario_speed=first_int(stats.get('speed'),0)
        ident._catalog_level=first_int(stats.get('level'),level)
        ident._catalog_hp=first_int(stats.get('hp'),0)
        return ident
