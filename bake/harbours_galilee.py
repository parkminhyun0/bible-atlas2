"""갈릴리 호수의 헬레니즘·로마기 항구와 정박지 후보.

Mendel Nun의 '16 harbours and anchorages'는 구조물 조사 수이지 서기 1세기에
동시에 운영된 16개 도시의 수가 아니다. 같은 해안에 복수 시설이 있고 일부는
Roman–Byzantine 범위로만 연대가 잡힌다. 그래서 장소와 증거 등급을 분리한다.

A verified: 1세기 사용을 직접 지지하는 발굴·층위·유물
B probable: 조사된 항만 구조 + 헬레니즘/로마기 사용이 유력
C tentative: 목록에 있으나 구조·연대·정확 좌표가 제한적

좌표 기준: harbour(항만 구조), shore(호안 대표점), site(배후 유적 대표점).

2026-09-13 Nun 1999 원문 대조
  BAS 모음집 『The Galilee Jesus Knew』(2008)에 실린 Mendel Nun, "Ports of Galilee:
  Modern drought reveals harbors from Jesus' time"(BAR 25:04, 1999) 전문을 읽고
  이 표를 한 줄씩 맞췄다. 세 가지가 드러났다.

  1. **인용이 넘쳤다.** 함맛·엠마오, 엔 고프라, 아이쉬·벳새다 세 곳은 이 논문에
     아예 나오지 않는데도 NUN1999 를 근거로 달고 있었다(원문 낱말 검색 0회).
     Nun 의 정박지 목록은 이 BAR 글이 아니라 그의 단행본에 있다 — 읽어 확인하지
     못한 책을 대신 적지 않고, 이 논문이 다루지 않는다는 사실을 그대로 적는다.
  2. **없는 수치를 적었다.** 타브가의 '약 60m와 40m 방파제'는 이 논문에 없다.
     Nun 은 "물이 낮을 때 방파제 흔적이 보인다"고만 쓴다. 수치를 뺀다.
  3. **좌표가 호안에서 멀었다.** OSM 의 호수 다각형으로 14곳의 호안선 거리를 재니
     쿠르시 682m, 디베랴 735m, 엔 고프라 462m, 크파르 아카브야 354m, 수시타 212m
     였다. 수시타 점은 엔게브 마을 노드(32.78111/35.63888)와 소수점까지 같았다 —
     항구가 아니라 마을을 찍고 있었다. Nun 은 항구가 "엔게브 키부츠 남쪽"에,
     디베랴 항구가 "현대 시가 남쪽·비잔틴 성벽 남쪽"에 있다고 못 박는다.
     문서화된 앵커에서 오늘의 호안선으로 옮겼다. harbour/shore 기준 점은 호안선
     120m 안에 있어야 한다는 규칙을 아래 CHECKS 로 못 박는다(site 기준은 예외 —
     텔은 원래 뭍에 있다).

  Nun 이 이 논문에서 실제로 준 치수는 nun1999 칸에 원문 단위 그대로 옮겨 적었다.
"""
import json
import math
import pathlib
import subprocess
import sys

OUT = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'harbours-galilee.geojson'

SOURCES = {
    'RABAN1988': 'Raban 1988, The boat from Migdal Nunia and the anchorages of the Sea of Galilee',
    'NUN1999': "Nun 1999, Ports of Galilee, Biblical Archaeology Review 25:04 "
               "(BAS, The Galilee Jesus Knew, 2008 재수록본으로 전문 대조)",
    'DELUCA2014': 'De Luca & Lena 2014, The Harbor of Magdala/Taricheae, BYZAS 19',
    'SARTI2013': 'Sarti et al. 2013, Magdala harbour sedimentation, Quaternary International 303',
    'GALILI2018': 'Galili et al. 2018, Five Decades of Marine Archaeology in Israel',
    'IAA2011': 'Israel Antiquities Authority 2011, The Kinneret Trail survey',
}

# 오늘의 호안선. 한 번 받아 두고 좌표 검사에 쓴다. Nun 은 로마기 최고 수위가 오늘보다
# 약 1m(3~4피트) 낮았고 얕은 물가가 최대 150피트(46m) 더 바깥에 있었다고 한다 —
# 그래서 옛 항만 시설은 오늘의 물가에 걸치거나 물속에 있다.
LAKE_CACHE = pathlib.Path(__file__).resolve().parent / '.cache-kinneret.json'
SHORE_MAX_M = 120          # harbour/shore 기준 점이 호안선에서 떨어져도 되는 한계

# ko, en, lon, lat, side, grade, coordinate_basis, period, description, refs, sources, nun1999
HARBOURS = [
    ('가버나움 항구', 'Capernaum harbour', 35.5758, 32.8807, '북서안', 'B', 'shore',
     '헬레니즘–로마기 유력',
     '호안을 따라 762m(2,500피트) 길이의 포장 산책로가 뻗고, 폭 2.4m(8피트) 안벽이 그것을 받쳤다. '
     '거기서 약 30m(100피트)씩 내민 부두들이 있었는데 둘씩 짝지어 안으로 굽은 것, 곧은 것, 삼각형인 것이 '
     '섞여 있다. 마태가 맡았던 해상 세관이 이 항구에 있었다.',
     '막 1:21; 마 4:13', ['NUN1999', 'GALILI2018'],
     '상세 기술 — 산책로 2,500피트·안벽 폭 8피트·부두 약 100피트 돌출·쌍곡/직선/삼각 부두. '
     '산책로 높이 해수면 아래 687피트로, 오늘의 최고 수위(686피트)보다 낮다.'),
    ('타브가·성 베드로 항구', 'Tabgha / St Peter harbour', 35.55158, 32.87242, '북서안', 'B', 'harbour',
     '로마기 사용 유력',
     '가버나움 어부들이 겨울에 일하던 작은 항구다. 따뜻한 광천이 솟아 겨울·봄에 무슈트(베드로 고기)가 '
     '모였기 때문이다. 물이 낮을 때 방파제 흔적이 드러난다. 베드로 수위 교회가 선 바위가 '
     '예수께서 제자들을 부르신 자리로 전해진다.',
     '막 1:16-20; 요 21:1-17', ['NUN1999', 'DELUCA2014'],
     '간단 기술 — "물이 낮을 때 방파제 흔적이 보인다"가 전부다. **치수는 주지 않는다.** '
     '전에 적어 둔 60m·40m 방파제 수치는 이 논문에 없어 뺐다.'),
    ('긴네렛·게네사렛 정박지', 'Tel Kinneret / Gennesaret anchorage', 35.53952, 32.86995, '북서안', 'C', 'site',
     '자연 정박 후보·1세기 연대 미확정',
     '텔 동·남쪽 만은 자연 피항에 적합하지만 현대 개발로 해안 흔적이 크게 교란되었다. 항만 구조와 '
     '서기 1세기 사용을 확정해 표시해서는 안 된다.',
     '막 6:53', ['DELUCA2014'],
     '항구 도면 설명의 보기로 "Gennesar"가 한 번 나올 뿐, 이 정박지를 따로 다루지 않는다.'),
    ('긴노사르 배 발견지', 'Ginosar boat find / landing area', 35.52556, 32.84694, '서안', 'A', 'shore',
     '기원전 40년–서기 70년 선박',
     '1986년 갯벌에서 길이 약 8.2m의 어선이 발견되었다. 항구 구조의 직접 증거라기보다 예수 시대 호수 '
     '운항과 이 해안의 선박 활동을 입증하는 지점이다.',
     '막 6:53', ['RABAN1988'],
     '"막달라 북쪽 약 1마일 진흙에서 온전히 보존된 나무배가 나왔다"고 사진 설명에 적는다. '
     '배는 다루지만 이 지점의 항만 구조는 다루지 않는다.'),
    ('막달라 하부 항구', 'Magdala lower harbour', 35.5169, 32.8247, '서안', 'A', 'harbour',
     '후기 헬레니즘–중기 로마기',
     '안벽·계선석·경사로·계단·플랫폼이 발굴되었다. 로마기 안벽은 수경성 모르타르를 썼고 네 개의 '
     '계선석이 확인되어, 서기 1세기 사용 근거가 가장 강한 항구다. 히브리 이름 미그달 누니야(물고기 탑), '
     '그리스 이름 타리케아(물고기를 절이는 곳)가 이 항구의 성격을 그대로 말한다.',
     '막 8:10; 마 15:39', ['RABAN1988', 'DELUCA2014', 'SARTI2013'],
     '상세 기술 — 산책로가 호안과 나란히 아랍 마을 미그달 폐허 아래에서 북으로 약 300피트(91m) 이어지고, '
     '그 안쪽에 보호된 정박 수역이 있다. 요세푸스는 막달라에 배와 조선공, 목재가 많았다고 적는다.'),
    ('디베랴 항구', 'Tiberias harbour', 35.54598, 32.77606, '서안', 'B', 'shore',
     '서기 19년 이후 로마기 유력',
     '헤롯 안티파스가 서기 19년경 세운 수도의 항만권이다. Nun 은 1989–91년 가뭄에 드러난 호안에서 '
     '돌닻과 계선석, 그물추 수백 개를 찾아 이 구역을 항구로 확정했다. 다만 방파제는 실마리만 잡혔을 뿐 '
     '발굴되지 않아 도면을 완성할 수 없다.',
     '요 6:23', ['NUN1999', 'GALILI2018'],
     '상세 기술 — 항구는 **현대 시가 남쪽**, 5세기 비잔틴 방어벽 남쪽의 교란되지 않은 약 500피트 구간에 '
     '있다. 기둥 여섯 줄이 약 80피트에 걸쳐 있으나 이는 아랍기(8~9세기) 재사용 건물이다. '
     '전에 찍어 둔 점은 현대 시가 한복판이라 이 기술과 어긋났다.'),
    ('함맛·엠마오 정박지', 'Hammat / Emmaus anchorage', 35.55065, 32.76638, '서안', 'C', 'site',
     '로마기·근거 제한적',
     '디베랴 남쪽 온천 취락의 정박지로 알려져 있다. 점은 온천 유적 대표 좌표이므로 정확한 방파제 위치로 '
     '읽어서는 안 된다.',
     '', ['GALILI2018'],
     '**언급 없음** — 이 논문은 함맛도 엠마오도 다루지 않는다(원문 검색 0회). '
     '전에는 이 논문을 근거로 달았으나 뒷받침하지 않아 뺐고, 등급도 B 에서 C 로 내렸다.'),
    ('벳 예라·필로테리아', 'Bet Yerah / Philoteria', 35.5739, 32.7059, '남서안', 'C', 'site',
     '헬레니즘기 취락·로마기 관계 불확실',
     '호수 남단의 텔과 필로테리아·세나브리스 명칭은 연구사에서 서로 복잡하게 연결된다. 항만 목록에는 '
     '포함되지만 서기 1세기 시설의 정확한 위치와 동일시가 확정되지 않았다.',
     '', ['DELUCA2014', 'GALILI2018'],
     '**언급 없음** — 다만 요단강 옛 출구가 오늘의 키네레트 마을 부근이었고 약 1,000년 전 남쪽으로 '
     '옮겨 가며 수위가 올랐다는 설명이 이 일대를 지난다.'),
    ('하온·가다라 항구', 'Ha-on / Gadara harbour', 35.61867, 32.72448, '동안', 'B', 'shore',
     '헬레니즘–로마기 유력',
     '가다라의 호수 출입항이다. 호수를 두른 항구 가운데 가장 크고 화려했다. 가다라 주화는 250년 동안 '
     '군선을 새겼고, 2세기 주화가 기념하는 해전 경기(나우마키아)가 이 넓은 항내에서 열렸을 것으로 본다. '
     '복음서의 귀신 축출 장소를 이곳으로 특정하는 것은 별도의 지리 가설이므로 항만 증거와 분리한다.',
     '마 8:28-34; 막 5:1-20', ['NUN1999'],
     '상세 기술 — 텔 삼라(오늘의 하온 휴양촌). 중앙 방파제 800피트·기저 폭 15피트, 산책로 650피트, '
     '항내 폭 150피트·넓이 3에이커, 산책로와 방파제를 합해 1,600피트. 산책로 한가운데 탑 자리와 '
     '항만 관리 건물로 보이는 큰 구조의 잔해가 있다.'),
    ('수시타·히포스 항구', 'Susita / Hippos harbour', 35.63914, 32.77029, '동안', 'B', 'shore',
     '헬레니즘–로마기',
     '히포스(수시타)는 호수 위 300m 언덕의 요새 도시였고, 항구와 15에이커짜리 해안 교외는 그 아래 '
     '호안에 있었다. 탈무드는 수시타 일대를 디베랴의 곳간이라 부른다. 미드라시는 노아의 방주가 '
     '"디베랴에서 수시타로 가듯" 쉽게 떠갔다고 적는데, 이 구절이 Nun 에게 하부 도시와 항구를 찾게 한 실마리였다.',
     '', ['NUN1999', 'GALILI2018'],
     '상세 기술 — 항구는 **엔게브 키부츠 남쪽**이다. 주 방파제 약 400피트·기저 폭 20피트로 북쪽을 두르다 '
     '남으로 꺾여 호안과 나란해지고, 남쪽에 짧은 방파제가 하나 더 있다. 항내는 약 1에이커, '
     '방파제에서 작은 부두가 뻗어 붐비는 항내에 들어가지 않고도 타고 내릴 수 있었다. '
     '전에 찍어 둔 점은 엔게브 마을 노드와 소수점까지 같았다.'),
    ('엔 고프라 정박지', 'Ein Gofra anchorage', 35.64170, 32.80231, '동안', 'C', 'shore',
     '고대 항만·세부 연대 제한적',
     '유황 온천이 솟는 고프라 해안의 석축 정박 후보다. 해양고고학 목록에는 들지만 서기 1세기 사용을 '
     '직접 좁혀 주는 공개 층위 자료는 제한적이다.',
     '', ['GALILI2018'],
     '**언급 없음** — 이 논문은 이 지점을 다루지 않는다(원문 검색 0회). '
     '전에는 이 논문을 근거로 달았으나 뒷받침하지 않아 뺐다.'),
    ('쿠르시 항구', 'Kursi harbour', 35.64433, 32.82639, '동안', 'A', 'harbour',
     '헬레니즘–로마기',
     '1970년 교회·수도원 발굴 때 라반(Avner Raban)의 수중 조사로 방파제가 확인된, 갈릴리에서 가장 먼저 '
     '찾아낸 고대 항구다. 어시장 부두 위에 활어를 담아 두던 얕은 수조가 있었고, 회반죽을 바른 안쪽에는 '
     '호수가 아니라 개울에서 끌어온 물을 채웠다. 부근에서 납 그물추가 백 개 넘게 나왔다.',
     '막 5:1-13; 막 8:1-10', ['RABAN1988', 'NUN1999'],
     '상세 기술 — 방파제 500피트가 호안에서 살짝 꺾여 나가며 폭 80피트·길이 330피트(약 0.5에이커)의 '
     '좁은 수역을 감싼다. 활어 수조 10×11피트를 바닥에서 3피트 올려 지었고, 어시장 부두는 25×16피트다. '
     '북쪽에 모자이크 바닥이 남은 관리 건물이 있다. 호수 수위가 낮을 때 한 해의 대부분 드러나는 '
     '유일한 항구여서, 옛 탐사자들이 보고도 알아보지 못했다.'),
    ('크파르 아카브야', 'Kefar Aqavya / Kinar beach', 35.64697, 32.85463, '동북안', 'C', 'shore',
     '로마–비잔틴기 범위·1세기 미확정',
     '키나르 해변의 고대 취락·호안 시설이다. IAA 둘레길 조사에서 풍부한 유구가 기록되었으나 서기 1세기 '
     '정박지로 좁혀 확정할 자료는 부족하다.',
     '', ['IAA2011', 'GALILI2018'],
     '**언급 없음** — 이 논문은 이 지점을 다루지 않는다.'),
    ('아이쉬·벳새다 어업 해안', 'Aish / Bethsaida fishing shore', 35.6100, 32.8950, '북안', 'C', 'shore',
     '항만 후보·정확 위치 논쟁',
     '요단 삼각주 서쪽의 유구를 벳새다 어업 교외 항구로 보는 제안이다. 엣텔과 엘아라즈는 도시 후보이지 '
     '확인된 항구 자체가 아니므로 별도 닻 두 개로 표시하지 않는다.',
     '막 6:45; 요 1:44', ['DELUCA2014'],
     '**언급 없음** — 이 논문에는 벳새다가 한 번도 나오지 않는다(원문 검색 0회). '
     '전에는 이 논문을 근거로 달았으나 뒷받침하지 않아 뺐다.'),
]


GRADE = {
    'A': ('확인', '1세기 사용을 직접 지지하는 발굴·층위·유물'),
    'B': ('유력', '조사된 항만 구조와 헬레니즘·로마기 사용 근거'),
    'C': ('추정', '목록·지형·부분 조사에 근거하나 연대나 위치가 제한적'),
}


def lake_rings():
    """오늘의 호수 다각형. 한 번 받아 캐시에 둔다."""
    if not LAKE_CACHE.exists():
        q = ('[out:json][timeout:180];'
             'relation["natural"="water"]["name:en"="Sea of Galilee"];'
             'out geom;')
        r = subprocess.run(['curl', '-s', '--max-time', '240',
                            '--data-urlencode', 'data=' + q,
                            'https://overpass-api.de/api/interpreter'],
                           capture_output=True, text=True)
        if not r.stdout.strip().startswith('{'):
            sys.exit('호수 다각형을 받지 못했다')
        LAKE_CACHE.write_text(r.stdout, encoding='utf-8')
    d = json.loads(LAKE_CACHE.read_text(encoding='utf-8'))
    rel = next(e for e in d['elements'] if e['type'] == 'relation')
    return [[(g['lon'], g['lat']) for g in m['geometry']]
            for m in rel['members'] if m.get('geometry') and m.get('role') != 'inner']


def shore_distance_m(rings, x, y):
    """점에서 호안선까지의 최단거리(미터). 선분까지의 수직거리로 잰다."""
    sx = 111320.0 * math.cos(math.radians(y))
    sy = 110540.0
    best = float('inf')
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            ax, ay = (x1 - x) * sx, (y1 - y) * sy
            bx, by = (x2 - x) * sx, (y2 - y) * sy
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def main():
    features = []
    for (ko, en, lon, lat, side, grade, basis, period, desc,
         refs, source_ids, nun) in HARBOURS:
        label, criterion = GRADE[grade]
        props = {
            'ko': ko, 'en': en, 'side': side, 'grade': grade,
            'confidence': label, 'criterion': criterion,
            'coordinate_basis': basis, 'period': period, 'desc': desc,
            'sources': ' · '.join(SOURCES[s] for s in source_ids),
            'nun1999': nun,
        }
        if refs:
            props['refs'] = refs
        features.append({'type': 'Feature', 'properties': props,
                         'geometry': {'type': 'Point', 'coordinates': [lon, lat]}})

    # 좌표 검사. harbour/shore 를 기준으로 삼았다면 오늘의 호안선 가까이 있어야 한다.
    # site 기준은 텔·취락이라 뭍에 있는 것이 맞으므로 재기만 하고 넘어간다.
    rings = lake_rings()
    print('호안선 꼭짓점 %d개' % sum(len(r) for r in rings))
    bad = []
    for f in features:
        lon, lat = f['geometry']['coordinates']
        d = shore_distance_m(rings, lon, lat)
        f['properties']['shore_distance_m'] = round(d)
        basis = f['properties']['coordinate_basis']
        mark = ' '
        if basis in ('harbour', 'shore') and d > SHORE_MAX_M:
            bad.append('%s %dm' % (f['properties']['ko'], round(d)))
            mark = '!'
        print('  %s %-22s %-8s %5dm' % (mark, f['properties']['ko'], basis, round(d)))
    if bad:
        sys.exit('harbour/shore 기준인데 호안선에서 %dm 넘게 떨어진 점: %s'
                 % (SHORE_MAX_M, ' | '.join(bad)))

    collection = {
        'type': 'FeatureCollection',
        'attribution': 'Raban 1988 · Nun 1989/1999 · De Luca & Lena 2014 · Sarti et al. 2013 · Galili et al. 2018 · IAA 2011',
        'note': ('Nun 1999 는 호수에 "적어도 15곳"(도면 설명)에서 "적어도 16곳"(본문)의 인공 항구가 '
                 '있었다고 적는다. 같은 글 안에서 수가 갈리므로 어느 한쪽을 확정해 옮기지 않는다. '
                 '여기 담은 14곳은 장소 단위로 묶은 것이고, 1세기 확실성은 A/B/C 로 나눈다. '
                 '로마기 최고 수위는 오늘보다 약 1m 낮았고 얕은 물가가 최대 46m 더 바깥이었다 — '
                 '그래서 옛 항만 시설은 오늘의 물가에 걸치거나 물속에 있다.'),
        'evidence_model': {g: GRADE[g][1] for g in GRADE},
        'features': features,
    }
    OUT.write_text(json.dumps(collection, ensure_ascii=False, indent=1), encoding='utf-8')
    counts = {g: sum(f['properties']['grade'] == g for f in features) for g in GRADE}
    nun_silent = sum('언급 없음' in f['properties']['nun1999'] for f in features)
    print('%d곳 · %s · Nun 1999 가 다루지 않는 곳 %d' % (len(features), counts, nun_silent))


if __name__ == '__main__':
    main()
