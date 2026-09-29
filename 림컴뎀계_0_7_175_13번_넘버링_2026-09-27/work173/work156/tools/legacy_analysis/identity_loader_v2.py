from __future__ import annotations
import json
from pathlib import Path
from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData

SIN_MAP={'slash':'slash','pierce':'pierce','blunt':'blunt','참격':'slash','관통':'pierce','타격':'blunt'}

def load_database(path='identity_database_v2.json'):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def to_identity(record, offense_level=None):
    ol = offense_level if offense_level is not None else record.get('offense_level')
    if ol is None:
        raise ValueError(f"{record['name']}: offense_level is not present in catalog; provide offense_level explicitly")
    skills={}
    for slot,s in record['skills'].items():
        cps=s.get('coin_powers') or [s['coin_power']]*s['coin_count']
        coins=[CoinData(int(cp), SIN_MAP.get(s.get('attack_type'),s.get('attack_type')), s.get('sin','')) for cp in cps]
        skills[slot]=SkillData(str(s['id']),s['name'],int(s['base_power']),coins,
                               SIN_MAP.get(s.get('attack_type'),s.get('attack_type')),s.get('sin',''))
    return IdentityData(str(record['id']),record['name'],int(ol),skills,record.get('passives',[]))

if __name__=='__main__':
    db=load_database(); print(f"records={len(db['identities'])}")
    print('offense_level missing:',sum(x.get('offense_level') is None for x in db['identities']))
