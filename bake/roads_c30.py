#!/usr/bin/env python3
# 서기 30년경 주요 육상 교통로 데이터를 만든다.
#
#   python3 bake/roads_c30.py /path/to/itinere_roads.geojson
#
# 원자료는 Itiner-e (CC BY 4.0). 좌표는 EPSG:3395 라 WGS84 로 되돌린다.
# Itiner-e 의 시간 기준은 서기 150년경이므로 그대로 서기 30년 자료로 쓰지 않는다.
# 아래 ROADS 표에 노선을 하나하나 손으로 골라 넣고, 서기 30년에 그 길이 쓰였다고
# 볼 근거(c30Basis)를 함께 적는다. 근거가 모자라면 HOLD 로 남긴다.
import json, math, sys, io
from collections import defaultdict

A = 6378137.0; F = 1 / 298.257223563; E = math.sqrt(F * (2 - F))
def inv3395(x, y):
    lon = math.degrees(x / A)
    t = math.exp(-y / A); phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(8):
        es = E * math.sin(phi)
        phi = math.pi / 2 - 2 * math.atan(t * ((1 - es) / (1 + es)) ** (E / 2))
    return [round(lon, 5), round(math.degrees(phi), 5)]

def hav(a, b):                                   # km
    p = math.pi / 180; R = 6371.0088
    return 2 * R * math.asin(math.sqrt(
        math.sin((b[1] - a[1]) * p / 2) ** 2 +
        math.cos(a[1] * p) * math.cos(b[1] * p) * math.sin((b[0] - a[0]) * p / 2) ** 2))

CERT = {'Certain': 'confirmed', 'Conjectured': 'probable', 'Hypothetical': 'hypothetical'}

# 좌표 단순화(더글러스–포이커). Itiner-e 가 밝힌 자체 오차는 산지 50 m·평지 200 m 이므로,
# 25 m 로 줄여도 자료가 주장하는 정확도 안쪽이다. 모바일에서 점 수를 줄이는 것이 목적이다.
SIMPLIFY_M = 25.0
def _perp(p, a, b):
    kx = 111320 * math.cos(math.radians(a[1])); ky = 110570
    ax, ay = a[0] * kx, a[1] * ky; bx, by = b[0] * kx, b[1] * ky; px, py = p[0] * kx, p[1] * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0: return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
def simplify(pts, tol=SIMPLIFY_M):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, bi = -1, -1
        for k in range(i + 1, j):
            d = _perp(pts[k], pts[i], pts[j])
            if d > best: best, bi = d, k
        if best > tol:
            keep[bi] = True; stack.append((i, bi)); stack.append((bi, j))
    return [p for p, k in zip(pts, keep) if k]

# ── 서기 30년에 쓰였다고 볼 수 있는 노선만 고른다 ───────────────────────────────
# itinere: Itiner-e 의 Name 값. 그 이름의 구간을 모두 가져온다.
ROADS = [
 { 'id': 'coastal-trunk', 'nameKo': '지중해 연안 간선로', 'nameEn': 'Mediterranean coastal trunk road',
   'routeType': 'trunk', 'region': 'Coast',
   'itinere': ['Gaza-Raphia', 'Ascalon-Gaza', 'Azotos-Ascalon', 'Iamnia-Azotus', 'Ioppe-Iamnia',
               'Caesarea Maritima-Ioppe', 'Caesarea Maritima-Ptolemais', 'Ptolemais-Tyre'],
   'via': ['가사', '아스글론', '아소도', '얌니아', '욥바', '가이사랴', '돌레마이', '두로'],
   'relatedVerses': ['행 8:26', '행 9:32-43', '행 21:7-8'],
   'c30Basis': '이집트–레반트를 잇는 해안 통로는 청동기 이래 쓰였고, 잇는 도시가 모두 서기 30년에 존재한다. '
               'Itiner-e 는 이 구간에 연대를 지정하지 않았다.',
   'noteKo': '이집트에서 가사·욥바·가이사랴를 지나 두로로 이어지는 해안길이다. 전통적으로 ‘해변길(Via Maris)’이라 '
             '불리지만 그것은 후대의 별칭이며 1세기 공식 도로명이 아니다.' },

 { 'id': 'ridge-route', 'nameKo': '중앙 산지 능선로', 'nameEn': 'Central hill-country ridge route',
   'routeType': 'pilgrimage', 'region': 'Judaea/Samaria',
   'itinere': ['Jerusalem-Hebron', 'Ziph-Bethlehem', 'Gophna-Jerusalem', 'Neapolis-Jerusalem',
               'Neapolis-Sebaste', 'Sebaste-Ginae'],
   'via': ['헤브론', '베들레헴', '예루살렘', '벧엘', '실로', '세겜', '사마리아'],
   'relatedVerses': ['요 4:3-6', '눅 2:4', '삿 21:19'],
   'c30Basis': '유대 산지의 분수령을 따르는 길로 철기시대부터 이어졌다. 갈릴리 사람들이 절기에 사마리아를 '
               '지나 예루살렘으로 올라갔다는 기록(요세푸스 유대고대사 20.118; 요 4:3-6)이 1세기 통행을 뒷받침한다.',
   'noteKo': '산지 분수령을 따라 남북으로 잇는 길이다. Itiner-e 의 구간명은 후대 지명(네아폴리스·세바스테)을 쓰지만 '
             '길 자체는 세겜·사마리아를 지나던 그 노선이다.' },

 { 'id': 'jerusalem-jericho', 'nameKo': '예루살렘–여리고 길', 'nameEn': 'Jerusalem–Jericho road',
   'routeType': 'trunk', 'region': 'Judaea',
   'itinere': ['Jerusalem-Jericho'],
   'via': ['예루살렘', '여리고'],
   'relatedVerses': ['눅 10:30-35', '눅 19:1', '막 10:46'],
   'c30Basis': '유대 광야를 가로질러 예루살렘과 여리고를 잇는 길. 헤롯의 여리고 궁과 예루살렘을 오가는 '
               '주요 통로였고, 복음서가 이 길의 내리막과 위험을 그대로 전한다.',
   'noteKo': '예루살렘(약 750 m)에서 여리고(약 -260 m)까지 27 km 남짓에 1,000 m 넘게 내려간다. '
             '‘예루살렘에서 여리고로 내려가다’(눅 10:30)라는 표현이 그대로 지형이다.' },

 { 'id': 'joppa-jerusalem', 'nameKo': '욥바·룻다–예루살렘 연결로', 'nameEn': 'Joppa/Lydda–Jerusalem road',
   'routeType': 'trunk', 'region': 'Judaea',
   'itinere': ['Diospolis-Ioppe', 'Diospolis-Jerusalem', 'Diospolis-Abu Ghosh', 'Abu Ghosh-Gabaon',
               'Emmaus-Jerusalem', 'Emmaus-Beth Horon Road', 'Antipatris-Diospolis'],
   'via': ['욥바', '룻다', '엠마오', '기브온', '벧호론', '예루살렘'],
   'relatedVerses': ['눅 24:13-33', '행 9:32-38', '행 23:31-33'],
   'c30Basis': '항구 욥바와 예루살렘을 잇는 길목이다. 룻다(디오스폴리스는 서기 199년의 개칭)·엠마오·벧호론은 '
               '모두 서기 30년에 있던 곳이며, 벧호론 오르막은 마카베오 시대부터 알려진 통로다.',
   'noteKo': '해안에서 유대 산지로 올라가는 여러 갈래가 있다. 엠마오 길(눅 24:13)과 벧호론 오르막이 대표적이다.' },

 { 'id': 'jordan-valley', 'nameKo': '요단 계곡길', 'nameEn': 'Jordan Valley road',
   'routeType': 'trunk', 'region': 'Jordan Valley',
   'itinere': ['Scythopolis-Archelais', 'Archelais-Jericho', 'Jericho-Livias', 'Tiberias-Scythopolis'],
   'via': ['벧산(스구도볼리)', '여리고'],
   'relatedVerses': ['막 10:1', '요 1:28', '눅 9:52-53'],
   'c30Basis': '아르켈라이스는 아켈라오(기원전 4년~서기 6년)가 세운 곳이라 서기 30년에 존재한다. '
               '사마리아를 피해 요단 계곡으로 도는 길은 갈릴리–예루살렘 왕래의 대안 노선이었다.',
   'noteKo': '갈릴리에서 예루살렘으로 갈 때 사마리아를 지나지 않으려면 이 계곡길로 돌았다(눅 9:52-53 배경).' },

 { 'id': 'galilee-cross', 'nameKo': '갈릴리 횡단로', 'nameEn': 'Galilee cross route',
   'routeType': 'regional', 'region': 'Galilee',
   'itinere': ['Ptolemais-Sepphoris', 'Sepphoris-Tiberias', 'Ptolemais-Sea of Galilee'],
   'via': ['돌레마이', '세포리스', '디베랴'],
   'relatedVerses': ['마 4:23', '요 2:1-11'],
   'c30Basis': '세포리스는 안티파스의 첫 도읍, 디베랴는 서기 19/20년 건설로 둘 다 서기 30년에 존재한다. '
               '두 도시를 잇는 길이 갈릴리 내륙을 가로지른다.',
   'noteKo': '항구 돌레마이에서 갈릴리 내륙을 거쳐 갈릴리 호수로 나가는 길이다. 가나·나사렛이 이 길목 가까이에 있다.' },

 { 'id': 'galilee-damascus', 'nameKo': '갈릴리–다메섹 연결로', 'nameEn': 'Galilee–Damascus road',
   'routeType': 'trunk', 'region': 'Upper Galilee/Gaulanitis',
   'itinere': ['Tyre-Sea of Galilee', 'Cadasa-Sea of Galilee', 'Tyre-Caesarea Paneas',
               'Caesarea Paneas-Damascus'],
   'via': ['두로', '가이사랴 빌립보', '다메섹'],
   'relatedVerses': ['마 16:13', '막 8:27', '행 9:1-8'],
   'c30Basis': '파네아스(가이사랴 빌립보)는 빌립이 기원전 2년에 다시 세워 서기 30년에 존재한다. '
               '훌라 계곡을 지나 다메섹으로 가는 통로는 오래된 국제 노선이다.',
   'noteKo': '갈릴리 북쪽에서 훌라 계곡을 지나 다메섹으로 이어진다. Itiner-e 가 서기 130년으로 연대를 적은 '
             '율리아스–파네아스 구간은 이 층에서 뺐다.' },

 { 'id': 'decapolis', 'nameKo': '데가볼리·요단 동편 연결로', 'nameEn': 'Decapolis / Transjordan link',
   'routeType': 'regional', 'region': 'Decapolis/Peraea',
   'itinere': ['Scythopolis-Pella', 'Pella-Gerasa', 'Gerasa-Philadelphia', 'Scythopolis-Gadara',
               'Tiberias-Gadara', 'Scythopolis-Hippos', 'Hippos-Julias', 'Pella-Amathous',
               'Ammathous-Philadelphia'],
   'via': ['벧산(스구도볼리)', '가다라', '히포스', '거라사', '빌라델비아'],
   'relatedVerses': ['막 5:20', '막 7:31', '마 4:25'],
   'c30Basis': '데가볼리 도시들은 모두 서기 30년에 존재한다. 가다라·히포·펠라·게라사·필라델피아를 잇는 '
               '길은 폼페이우스 이후의 도시망을 따른다. 카피톨리아스(서기 97/98년 건설)를 지나는 구간은 뺐다.',
   'noteKo': '갈릴리 호수 동남쪽 데가볼리 도시들을 잇는 길이다. ‘데가볼리에서 큰 무리가 따랐다’(마 4:25)의 배경.' },

 { 'id': 'peraea-philadelphia', 'nameKo': '베레아–필라델피아 연결로', 'nameEn': 'Peraea–Philadelphia road',
   'routeType': 'regional', 'region': 'Peraea',
   'itinere': ['Livias-Esbus', 'Philadelphia-Esbus'],
   'via': ['헤스본', '빌라델비아'],
   'relatedVerses': ['막 10:1'],
   'c30Basis': '요세푸스는 베레아가 “필라델피아에서 요단까지” 뻗었다고 적는다(유대 전쟁사 3.47). '
               '리비아스는 안티파스가 서기 13년경 세워 서기 30년에 존재한다.',
   'noteKo': '요단 동편 베레아에서 헤스본을 지나 필라델피아(오늘의 암만)로 오르는 길이다.' },

 { 'id': 'incense-gaza', 'nameKo': '나바테아 향료길 (페트라–가사)', 'nameEn': 'Nabataean incense road (Petra–Gaza)',
   'routeType': 'trade', 'region': 'Negev/Nabataea',
   'itinere': ['Moyet Awad-Petra', 'Oboda-Moyet Awad', 'Elusa-Oboda', 'Gaza-Elusa'],
   'via': ['가사'],
   'relatedVerses': [],
   'c30Basis': '아라비아의 향료를 페트라에서 지중해 항구 가사로 실어 내던 나바테아 대상로다. 오보다·엘루사 같은 '
               '길목 도시가 기원전 1세기~서기 1세기에 쓰였다. 트라야누스가 서기 111~114년에 놓은 Via Nova Traiana '
               '와는 다른 길이다.',
   'noteKo': '유일하게 서기 30년 이전부터 확실히 쓰인 나바테아 교역로다. 요단 동편을 남북으로 잇는 Via Nova '
             'Traiana 는 서기 111~114년 도로여서 이 층에 넣지 않았다.' },
]

# 서기 30년 이후에 놓인 길. 기본 화면에서는 숨기고, 사용자가 켤 때만 회색 점선으로 보인다.
LATER = [
 ('via-nova-traiana', 'Via Nova Traiana (서기 111~114년)', 111,
  ['Characmoba-Thornia', 'Thornia-Negla', 'Petra-Zodocatha', 'Dibon-Aeropolis', 'Negla-Petra',
   'Zodocatha-Auara', 'Aeropolis-Characmoba', 'Aeropolis-Betthorus']),
 ('later-hula', '율리아스–파네아스 도로 (서기 130년)', 130, ['Julias-Caesarea Paneas']),
 ('later-jer-eleuth', '예루살렘–엘레우테로폴리스 도로 (서기 130년)', 130, ['Jerusalem-Eleutheropolis']),
 ('later-golan', '갈릴리 호수 동편 도로 (서기 162년)', 162, ['Sea of Galilee-Neue', 'Dionysias-Phaena']),
 ('later-gerasa-bostra', '게라사–보스트라 도로 (서기 162년)', 162, ['Gerasa-Bostra']),
 ('later-caesarea-legio', '가이사랴–레기오 도로 (서기 70년 이후)', 70, ['Caesarea Maritima-Legio']),
]

def build(src):
    by_name = defaultdict(list)
    with io.open(src, encoding='utf-8') as f:
        for line in f:
            line = line.strip().rstrip(',')
            if not line.startswith('{ "type": "Feature"'): continue
            try: ft = json.loads(line)
            except Exception: continue
            n = ft['properties'].get('Name')
            if n: by_name[n].append(ft)

    feats = []; summary = []; missing = []
    def emit(spec_id, props_base, names, later=None):
        n_seg = 0; km = 0.0; certs = []
        for nm in names:
            if nm not in by_name: missing.append((spec_id, nm)); continue
            for ft in by_name[nm]:
                g = ft['geometry']
                parts = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
                ll = [[inv3395(c[0], c[1]) for c in p] for p in parts]
                ll = [simplify(p) for p in ll]
                ll = [p for p in ll if len(p) >= 2]
                if not ll: continue
                for p in ll:
                    km += sum(hav(p[i], p[i + 1]) for i in range(len(p) - 1))
                cert = CERT.get(ft['properties'].get('Segment_s'), 'hypothetical')
                certs.append(cert)
                props = dict(props_base)
                props['id'] = f"{spec_id}#{n_seg}"
                props['certainty'] = cert
                props['segmentName'] = nm
                props['segmentSource'] = ft['properties'].get('Bibliograp') or ''
                feats.append({'type': 'Feature', 'properties': props,
                              'geometry': {'type': 'MultiLineString', 'coordinates': ll}})
                n_seg += 1
        return n_seg, km, certs

    for r in ROADS:
        base = {'roadId': r['id'], 'nameKo': r['nameKo'], 'nameEn': r['nameEn'],
                'routeType': r['routeType'], 'activeC30': True, 'region': r['region'],
                'periodStart': None, 'periodEnd': None,
                'via': r['via'], 'relatedPlaces': r['via'], 'relatedVerses': r['relatedVerses'],
                'sourceIds': ['itinere-2024', 'pleiades', 'josephus'],
                'noteKo': r['noteKo'], 'c30Basis': r['c30Basis'],
                'license': 'Itiner-e (Brughmans, de Soto, Pažout, Bjerregaard Vahlstrup 2024) CC BY 4.0'}
        n, km, certs = emit(r['id'], base, r['itinere'])
        # 길 전체를 한 등급으로 뭉뚱그리지 않는다. 구간 구성을 그대로 적어 팝업에서 보여준다.
        mix = {c: certs.count(c) for c in ('confirmed', 'probable', 'hypothetical') if certs.count(c)}
        days = (round(km / 35), round(km / 25))
        for ft in feats:
            if ft['properties']['roadId'] == r['id']:
                ft['properties']['lengthKm'] = round(km)
                ft['properties']['certaintyMix'] = mix
                ft['properties']['walkDays'] = list(days)
        summary.append({'id': r['id'], 'nameKo': r['nameKo'], 'routeType': r['routeType'],
                        'segments': n, 'lengthKm': round(km), 'certaintyMix': mix, 'walkDays': days})

    for rid, name, start, names in LATER:
        base = {'roadId': rid, 'nameKo': name, 'nameEn': name, 'routeType': 'later',
                'activeC30': False, 'region': 'later', 'periodStart': start, 'periodEnd': None,
                'via': [], 'relatedPlaces': [], 'relatedVerses': [],
                'sourceIds': ['itinere-2024'], 'noteKo': '서기 30년 이후에 놓인 길이라 기준 화면에서는 숨긴다.',
                'c30Basis': '', 'license': 'Itiner-e CC BY 4.0'}
        n, km, certs = emit(rid, base, names)
        for ft in feats:
            if ft['properties']['roadId'] == rid:
                ft['properties']['lengthKm'] = round(km)
                ft['properties']['certaintyMix'] = {c: certs.count(c) for c in set(certs)}
                ft['properties']['walkDays'] = [round(km / 35), round(km / 25)]
        summary.append({'id': rid, 'nameKo': name, 'routeType': 'later', 'segments': n,
                        'lengthKm': round(km), 'periodStart': start})
    return feats, summary, missing

if __name__ == '__main__':
    feats, summary, missing = build(sys.argv[1])
    out = {'type': 'FeatureCollection', 'name': 'roads-c30',
           'note': '서기 30년경 주요 육상 교통로 · 문헌·고고학·지형에 근거한 교육용 재구성이다. '
                   '“서기 30년의 정확한 도로망”이 아니다.',
           'attribution': 'Roads: Itiner-e — Brughmans, T., de Soto, P., Pažout, A., '
                          'Bjerregaard Vahlstrup, P. (2024), CC BY 4.0. 좌표계를 EPSG:3395 에서 '
                          'WGS84 로 바꾸고, 서기 30년 기준으로 노선을 골라 속성을 새로 붙였다.',
           'features': feats}
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False)
    print(json.dumps({'roads': summary, 'missingNames': missing}, ensure_ascii=False, indent=1))
