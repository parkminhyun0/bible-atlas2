"""갈릴리 호수의 헬레니즘·로마기 항구와 정박지 후보.

Mendel Nun의 '16 harbours and anchorages'는 구조물 조사 수이지 서기 1세기에
동시에 운영된 16개 도시의 수가 아니다. 같은 해안에 복수 시설이 있고 일부는
Roman–Byzantine 범위로만 연대가 잡힌다. 그래서 장소와 증거 등급을 분리한다.

A verified: 1세기 사용을 직접 지지하는 발굴·층위·유물
B probable: 조사된 항만 구조 + 헬레니즘/로마기 사용이 유력
C tentative: 목록에 있으나 구조·연대·정확 좌표가 제한적

좌표 기준: harbour(항만 구조), shore(호안 대표점), site(배후 유적 대표점).
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'harbours-galilee.geojson'

SOURCES = {
    'RABAN1988': 'Raban 1988, The boat from Migdal Nunia and the anchorages of the Sea of Galilee',
    'NUN1999': 'Nun 1999, Ports of Galilee, Biblical Archaeology Review 25.4',
    'DELUCA2014': 'De Luca & Lena 2014, The Harbor of Magdala/Taricheae, BYZAS 19',
    'SARTI2013': 'Sarti et al. 2013, Magdala harbour sedimentation, Quaternary International 303',
    'GALILI2018': 'Galili et al. 2018, Five Decades of Marine Archaeology in Israel',
    'IAA2011': 'Israel Antiquities Authority 2011, The Kinneret Trail survey',
}

# ko, en, lon, lat, side, grade, coordinate_basis, period, description, refs, sources
HARBOURS = [
    ('가버나움 항구', 'Capernaum harbour', 35.5758, 32.8807, '북서안', 'B', 'shore',
     '헬레니즘–로마기 유력',
     '현무암 방파제·부두·계선 시설이 조사된 큰 항구다. 800m라는 수치는 항만과 인접 호안 시설 전체 범위로 보아야 하며, 서기 1세기 단일 부두 길이로 단정하지 않는다.',
     '막 1:21; 마 4:13', ['NUN1999', 'GALILI2018']),
    ('타브가·성 베드로 항구', 'Tabgha / St Peter harbour', 35.5508, 32.8737, '북서안', 'B', 'harbour',
     '로마기 사용 유력',
     '서로 다른 두 방파제로 보호된 정박 시설 가운데 하나다. 약 60m와 40m 방파제가 보고되며, 인근 온천수 때문에 겨울 어장이 형성되었다.',
     '막 1:16-20; 요 21:1-17', ['NUN1999', 'DELUCA2014']),
    ('긴네렛·게네사렛 정박지', 'Tel Kinneret / Gennesaret anchorage', 35.53952, 32.86995, '북서안', 'C', 'site',
     '자연 정박 후보·1세기 연대 미확정',
     '텔 동·남쪽 만은 자연 피항에 적합하지만 현대 개발로 해안 흔적이 크게 교란되었다. 항만 구조와 서기 1세기 사용을 확정해 표시해서는 안 된다.',
     '막 6:53', ['DELUCA2014']),
    ('긴노사르 배 발견지', 'Ginosar boat find / landing area', 35.52363, 32.84764, '서안', 'A', 'shore',
     '기원전 40년–서기 70년 선박',
     '1986년 갯벌에서 길이 약 8.2m의 어선이 발견되었다. 항구 구조의 직접 증거라기보다 예수 시대 호수 운항과 이 해안의 선박 활동을 입증하는 지점이다.',
     '막 6:53', ['RABAN1988']),
    ('막달라 하부 항구', 'Magdala lower harbour', 35.5169, 32.8247, '서안', 'A', 'harbour',
     '후기 헬레니즘–중기 로마기',
     '안벽·계선석·경사로·계단·플랫폼이 발굴되었다. 로마기 안벽은 수경성 모르타르를 썼고 네 개의 계선석이 확인되어, 서기 1세기 사용 근거가 가장 강한 항구다.',
     '막 8:10; 마 15:39', ['RABAN1988', 'DELUCA2014', 'SARTI2013']),
    ('디베랴 항구', 'Tiberias harbour', 35.5312, 32.7959, '서안', 'B', 'shore',
     '서기 19년 이후 로마기 유력',
     '헤롯 안티파스가 서기 19년경 세운 수도의 항만권이다. 항구 사용은 도시 성격과 문헌상 확실하지만, 현재 점은 공개된 항만 구조 좌표가 아닌 고대 도시 호안 대표점이다.',
     '요 6:23', ['NUN1999', 'GALILI2018']),
    ('함맛·엠마오 정박지', 'Hammat / Emmaus anchorage', 35.55065, 32.76638, '서안', 'B', 'site',
     '로마기',
     '디베랴 남쪽 온천 취락의 정박지다. 문헌의 엠마오/암마투스와 연결되지만, 점은 온천 유적 대표 좌표이므로 정확한 방파제 위치로 읽어서는 안 된다.',
     '', ['NUN1999']),
    ('벳 예라·필로테리아', 'Bet Yerah / Philoteria', 35.5739, 32.7059, '남서안', 'C', 'site',
     '헬레니즘기 취락·로마기 관계 불확실',
     '호수 남단의 텔과 필로테리아·세나브리스 명칭은 연구사에서 서로 복잡하게 연결된다. 항만 목록에는 포함되지만 서기 1세기 시설의 정확한 위치와 동일시가 확정되지 않았다.',
     '', ['DELUCA2014', 'GALILI2018']),
    ('하온·가다라 항구', 'Ha-on / Gadara harbour', 35.6238, 32.7286, '동안', 'B', 'shore',
     '헬레니즘–로마기 유력',
     '호수 동남안에서 조사된 대형 항만 시설로 가다라의 호수 출입항 후보다. 복음서의 귀신 축출 장소를 이곳으로 특정하는 것은 별도의 지리 가설이므로 항만 증거와 분리한다.',
     '마 8:28-34; 막 5:1-20', ['NUN1999']),
    ('수시타·히포스 항구', 'Susita / Hippos harbour', 35.6389, 32.7811, '동안', 'B', 'shore',
     '헬레니즘–로마기',
     '히포스 도시는 높은 언덕 위에 있지만 항구는 엔게브 일대 호안에 있었다. 기존처럼 산 위 도시 좌표에 닻을 찍지 않고 실제 출입 해안권을 표시한다.',
     '', ['NUN1999', 'GALILI2018']),
    ('엔 고프라 정박지', 'Ein Gofra anchorage', 35.6462, 32.8006, '동안', 'C', 'shore',
     '고대 항만·세부 연대 제한적',
     '유황 온천이 솟는 고프라 해안의 석축 정박 후보다. 해양고고학 목록에는 들지만 서기 1세기 사용을 직접 좁혀 주는 공개 층위 자료는 제한적이다.',
     '', ['NUN1999', 'GALILI2018']),
    ('쿠르시 항구', 'Kursi harbour', 35.6525, 32.8239, '동안', 'A', 'harbour',
     '헬레니즘–로마기',
     '반원형 방파제·보호 수역·안벽과 로마기 토기가 조사되었다. 갈릴리 호수에서 가장 상세히 도면화된 고대 항구 중 하나다.',
     '막 5:1-13; 막 8:1-10', ['RABAN1988', 'NUN1999']),
    ('크파르 아카브야', 'Kefar Aqavya / Kinar beach', 35.6505, 32.8558, '동북안', 'C', 'shore',
     '로마–비잔틴기 범위·1세기 미확정',
     '키나르 해변의 고대 취락·호안 시설이다. IAA 둘레길 조사에서 풍부한 유구가 기록되었으나 서기 1세기 정박지로 좁혀 확정할 자료는 부족하다.',
     '', ['IAA2011', 'GALILI2018']),
    ('아이쉬·벳새다 어업 해안', 'Aish / Bethsaida fishing shore', 35.6100, 32.8950, '북안', 'C', 'shore',
     '항만 후보·정확 위치 논쟁',
     '요단 삼각주 서쪽의 유구를 벳새다 어업 교외 항구로 보는 제안이다. 엣텔과 엘아라즈는 도시 후보이지 확인된 항구 자체가 아니므로 별도 닻 두 개로 표시하지 않는다.',
     '막 6:45; 요 1:44', ['NUN1999', 'DELUCA2014']),
]

GRADE = {
    'A': ('확인', '1세기 사용을 직접 지지하는 발굴·층위·유물'),
    'B': ('유력', '조사된 항만 구조와 헬레니즘·로마기 사용 근거'),
    'C': ('추정', '목록·지형·부분 조사에 근거하나 연대나 위치가 제한적'),
}


def main():
    features = []
    for ko, en, lon, lat, side, grade, basis, period, desc, refs, source_ids in HARBOURS:
        label, criterion = GRADE[grade]
        props = {
            'ko': ko, 'en': en, 'side': side, 'grade': grade,
            'confidence': label, 'criterion': criterion,
            'coordinate_basis': basis, 'period': period, 'desc': desc,
            'sources': ' · '.join(SOURCES[s] for s in source_ids),
        }
        if refs:
            props['refs'] = refs
        features.append({'type': 'Feature', 'properties': props,
                         'geometry': {'type': 'Point', 'coordinates': [lon, lat]}})

    collection = {
        'type': 'FeatureCollection',
        'attribution': 'Raban 1988 · Nun 1989/1999 · De Luca & Lena 2014 · Sarti et al. 2013 · Galili et al. 2018 · IAA 2011',
        'note': 'Nun의 16은 구조물/정박지 조사 수다. 중복 시설을 장소 단위로 묶고 1세기 확실성을 A/B/C로 구분한다.',
        'features': features,
    }
    OUT.write_text(json.dumps(collection, ensure_ascii=False, indent=1), encoding='utf-8')
    counts = {g: sum(f['properties']['grade'] == g for f in features) for g in GRADE}
    print(f'{len(features)}곳 · {counts}')


if __name__ == '__main__':
    main()
