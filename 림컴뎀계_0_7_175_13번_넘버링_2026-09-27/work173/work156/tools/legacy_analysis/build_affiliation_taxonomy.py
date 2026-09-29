import json,re
from pathlib import Path
ROOT=Path(__file__).parent
cat=json.loads((ROOT/'identity_catalog_v2.json').read_text(encoding='utf-8'))['identities']
manifest=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
# Normalized taxonomy based strictly on affiliation values/name evidence in the catalog.
# Combat status is conservative: only groups already backed by implemented cross-identity
# mechanics are marked confirmed. Everything else is an audit candidate, not auto-loaded.
ALIASES={
 'limbus_company': ['림버스 컴퍼니','LCB','LIMBUS COMPANY LCC','LIMBUS COMPANY LCA'],
 'blade_lineage':['BLADE LINEAGE'], 'thumb':['THUMB FINGER'], 'middle':['MIDDLE FINGER'],
 'ring':['RING FINGER','RING FINGER POINTILLISM','RING FINGER PHYSICAL','RING FINGER FAUVISM'],
 'index':['INDEX FINGER'], 'pinky':['PINKY'], 'pequod':['PEQUOD CREW'],
 'black_cloud':['BLACK CLOUD'], 'spider_house':['SPIDER HOUSE'],
 'seven':['SEVEN'], 'cinq':['CINQ'], 'zwei':['ZWEI'], 'liu':['LIU'], 'dieci':['DIECI'], 'shi':['SHI'],
 'n_corp':['N사','N사 광신도'], 'w_corp':['W CORP'], 'h_corp':['H CORP'], 'l_corp':['L CORP'],
 'r_corp':['R사'], 't_corp':['T사'], 'g_corp':['G CORP'], 'k_corp':['K사'],
 'lce':['LCE'], 'oufi':['OUFI','OUFI COOP'], 'devyat':['DEVYAT'],
 'family_ga':['FAMILY GA','FAMILY GA CANCELED'], 'multi_crack':['MULTI CRACK'],
 'full_stop':['FULL STOP'], 'molar':['MOLAR'], 'hook_office':['HOOK OFFICE'],
 'jeong_office':['JEONG OFFICE'], 'firepunch_office':['FIREPUNCH OFFICE'],
 'trouble_shooter':['TROUBLE SHOOTER'], 'fang_hunt':['FANG HUNT'], 'mariachi':['MARIACHI'],
 'kong_kong':['KONG KONG'], 'backstreet_cook':['BACKSTREET COOK'],
 'linton':['LINTON'], 'wuthering_heights':['WUTHERING HEIGHTS'], 'wild_hunt':['WILD HUNT'],
 'la_mancha_land':['LA MANCHA LAND'], 'atl':['ATL'], 'lca':['LIMBUS COMPANY LCA'],
 'nightstiletto':['NIGHTSTILETTO'], 'dual_hook_pirate':['DUAL HOOK PIRATE'],
 'dead_rabbits':['DEAD RABBITS'], 'black_beast_rabbit':['BLACK BEAST RABBIT'],
 'black_beast_chicken':['BLACK BEAST CHICKEN'], 'black_beast_snake':['BLACK BEAST SNAKE'],
 'black_beast_horse':['BLACK BEAST HORSE'], 'black_beast_sheep':['BLACK BEAST SHEEP'],
 'yurodivy':['YURODIVY'], 'mari':['MARIACHI'],
 'dawn_office':['DAWN'],
}
# confirmed means an implemented cross-identity combat rule currently references the group.
CONFIRMED={'dawn_office','middle','pequod','ring','spider_house','black_cloud','blade_lineage','thumb','index','seven','zwei','liu','n_corp','w_corp','full_stop','la_mancha_land'}
# category taxonomy for browsing/audit only.
CAT={
 'limbus_company':'organization','blade_lineage':'finger_faction','thumb':'finger_faction','middle':'finger_faction','ring':'finger_faction','index':'finger_faction','pinky':'finger_faction','pequod':'crew_faction','black_cloud':'syndicate','spider_house':'syndicate',
 'seven':'association','cinq':'association','zwei':'association','liu':'association','dieci':'association','shi':'association','n_corp':'corporation','w_corp':'corporation','h_corp':'corporation','l_corp':'corporation','r_corp':'corporation','t_corp':'corporation','g_corp':'corporation','k_corp':'corporation','lce':'organization','oufi':'association','devyat':'association','family_ga':'syndicate','multi_crack':'syndicate','full_stop':'syndicate','molar':'office','hook_office':'office','jeong_office':'office','firepunch_office':'office','trouble_shooter':'office','fang_hunt':'association','mariachi':'group','kong_kong':'group','backstreet_cook':'group','linton':'group','wuthering_heights':'location_group','wild_hunt':'group','la_mancha_land':'location_group','atl':'organization','lca':'organization','nightstiletto':'group','dual_hook_pirate':'crew_faction','dead_rabbits':'syndicate','black_beast_rabbit':'beast_group','black_beast_chicken':'beast_group','black_beast_snake':'beast_group','black_beast_horse':'beast_group','black_beast_sheep':'beast_group','yurodivy':'group','mari':'group','dawn_office':'office'}
# Fix aliases collision: use normalized first-match exact affiliation; preserve all matching tags.
entries={}
for aid, aliases in ALIASES.items():
 entries[aid]={'id':aid,'aliases':aliases,'category':CAT.get(aid,'other'),'combat_relevance':'confirmed' if aid in CONFIRMED else 'unverified','combat_module':aid if aid in CONFIRMED else None}

# map identities to normalized affiliation tags from explicit affiliation fields, plus known name-only groups
rows={}
for x in cat:
 aff=[str(a).strip() for a in (x.get('affiliation',[]) or [])]
 tags=[]
 for aid,e in entries.items():
  if any(a.upper() in {z.upper() for z in aff} for a in e['aliases']): tags.append(aid)
 # Some existing combat participants have missing raw affiliation metadata; preserve those from prior manifest.
 old=next((r for r in manifest['identities'] if r['identity_id']==x['id']),None)
 for aid in (old.get('combat_affiliations',[]) if old else []):
  if aid not in tags: tags.append(aid)
 rows[x['id']]={'identity_id':x['id'],'full_name':x.get('full_name',x.get('name','')),'affiliation_raw':aff,'affiliation_tags':sorted(tags)}

# taxonomy summary
for e in entries.values():
 e['members']=[iid for iid,r in rows.items() if e['id'] in r['affiliation_tags']]
 e['member_count']=len(e['members'])

tax={'version':'0.6.15','principle':'Affiliation taxonomy is independent from seven generic keywords. combat_relevance=confirmed is conservative and only means an implemented cross-identity combat rule exists; unverified groups are not auto-loaded.','categories':sorted(set(e['category'] for e in entries.values())),'affiliations':entries,'identities':rows}
(ROOT/'affiliation_taxonomy_v1.json').write_text(json.dumps(tax,ensure_ascii=False,indent=2),encoding='utf-8')
# enrich manifest with normalized tags while preserving old axes
for r in manifest['identities']:
 r['affiliation_tags']=rows.get(r['identity_id'],{}).get('affiliation_tags',[])
manifest['version']='0.6.15'
manifest['affiliation_taxonomy']='affiliation_taxonomy_v1.json'
manifest['affiliation_policy']='multi-label; seven keywords and affiliations are independent; only confirmed combat affiliations are auto-loaded'
(ROOT/'identity_module_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# audit report
report={'version':'0.6.15','total_identities':len(cat),'unique_raw_affiliations':len(set(a for x in cat for a in x.get('affiliation',[]) or [])),'normalized_affiliations':len(entries),'confirmed_combat_affiliations':sorted(CONFIRMED),'unverified_affiliations':sorted(a for a,e in entries.items() if e['combat_relevance']=='unverified'),'groups':{a:{k:v for k,v in e.items() if k not in ('aliases','members')} | {'aliases':e['aliases'],'members':e['members']} for a,e in sorted(entries.items())}}
(ROOT/'AFFILIATION_TAXONOMY_AUDIT_0.6.15.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('wrote',len(rows),'identity rows',len(entries),'affiliation entries')
print('confirmed counts', {a:entries[a]['member_count'] for a in sorted(CONFIRMED)})
