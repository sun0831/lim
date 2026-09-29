# 림컴뎀계 0.6.19

## Combat affiliation axis expansion
- Promoted all 16 combat-confirmed normalized affiliations from the 0.6.16 audit into `combat_affiliations`.
- Updated the runtime fallback aliases to recognize all 16 confirmed affiliations.
- Kept raw/catalog affiliations separate from the combat-affiliation axis.
- Preserved seven generic keywords as an independent axis.

## Confirmed combat affiliations
- 검계 / blade_lineage
- 엄지 / thumb
- 중지 / middle
- 약지 / ring
- 검지 / index
- 피쿼드호 / pequod
- 흑운회 / black_cloud
- 거미집 / spider_house
- 새벽 사무소 / dawn_office
- 세븐 / seven
- 츠바이 / zwei
- 리우 / liu
- N사 / n_corp
- W사 / w_corp
- 마침표 / full_stop
- 라만차랜드 / la_mancha_land

## Verification
- 184 identities covered
- 16/16 confirmed combat affiliations represented on the manifest axis
- 16/16 affiliation provider modules importable
- Full suite: 280 passed
