"""1세기(예수 당시) 예루살렘 성읍의 규모.

성벽을 복원해 그리는 것이 아니라, **성읍이 얼마나 컸는지**를 지도 위에 보이려는
것이다. 그래서 둘레선 하나와 그 안의 면을 내고, 넓이·둘레·남북·동서를 잰다.

꼭짓점은 되도록 **발굴된 유구**에 건다. 사용자가 준 개설도(예루살렘 도시 경계.png)는
성벽이 어디를 지나는지 — 어디가 안이고 어디가 밖인지 — 를 정하는 데 썼고, 좌표는
그림에서 긁지 않았다. 그림을 못 네 곳으로 지리좌표에 맞춰 보니 기준점 잔차가 최대
111 m 였다. 측량도가 아니라 개설도이기 때문이다. 그 왜곡을 그대로 옮길 이유가 없다.

근거로 쓴 것:
  · 성전 산 남벽 — 로빈슨 아치·훌다 이중문·훌다 삼중문·단일문 네 발굴 지점에 직선을
    회귀시켰다(잔차 0.9~6.4 m). 거기에 실측 치수(남 281 m·동 466 m·서 485 m)를 얹어
    네 모서리를 냈다.  [Baruch·Reich·Hagbi·Uziel, 『성전 산 남벽』, IAA 2022]
  · 남쪽 둘레 — 모즐리 스카프(개신교 묘지)에서 시온산 남쪽을 지나 실로암 못까지.
    Bliss 와 Dickie 가 1894~97년에 실제로 파서 따라간 선이다.
    [Bliss & Dickie, 『Excavations at Jerusalem 1894-1897』]
  · 동쪽 둘레 — 다윗 성 능선의 워런 수직갱·계단식 석조 구조물·오벨.
  · 서쪽 둘레 — 다윗 탑(헤롯기 탑 기초)과 키슐레 발굴.

제2성벽(북쪽)만은 발굴로 확정된 선이 없다. 학설이 갈린다. 여기서는 고고 증거가 주는
두 조건만 지켰다 — 골고다(성묘 교회)는 성 **밖**, 히스기야 못은 성 **안**. 그래서 그
네 꼭짓점은 '불확실'로 표시하고 지도에서도 점선으로 그린다.

출력: data/jerusalem-c1.geojson
"""
import json, math, pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'jerusalem-c1.geojson'

# (경도, 위도, 무엇, 근거등급)  — 시계 방향
RING = [
    (35.22808, 31.77607, '다윗 탑 (헤롯기 탑 기초)',        '발굴'),
    (35.22799, 31.77516, '키슐레 발굴 (헤롯 궁전 기초)',     '발굴'),
    (35.22847, 31.77032, '모즐리 스카프 (개신교 묘지)',      '발굴'),
    (35.22960, 31.76991, '시온산 남쪽 발굴',                '발굴'),
    (35.23057, 31.77037, '티로포에온 골짜기를 건너는 구간',   '추정'),
    (35.23512, 31.77040, '실로암 못',                      '발굴'),
    (35.23641, 31.77310, '워런 수직갱',                    '발굴'),
    (35.23680, 31.77450, '기드론 위 능선',                  '추정'),
    (35.23656, 31.77570, '오벨',                          '발굴'),
    (35.23742, 31.77606, '성전 산 남동 모서리',             '발굴'),
    (35.23730, 31.78026, '성전 산 북동 모서리',             '발굴'),
    (35.23397, 31.78015, '성전 산 북서 (안토니아 요새)',     '발굴'),
    (35.23200, 31.77950, '제2성벽 북',                     '불확실'),
    (35.23010, 31.77800, '제2성벽 북서',                   '불확실'),
    (35.22870, 31.77780, '제2성벽 서',                     '불확실'),
    (35.22880, 31.77650, '겐나트 문 부근',                  '불확실'),
]

# 경계가 맞는지 재는 시금석. 안에 있어야 할 것과 밖에 있어야 할 것.
CHECKS = [
    ('성묘 교회 (골고다)', 35.22972, 31.77833, '밖'),
    ('베데스다 못',        35.23599, 31.78147, '밖'),
    ('다메섹 문',          35.23018, 31.78182, '밖'),
    ('기혼 샘',            35.23683, 31.77323, '밖'),
    ('계단식 석조 구조물',  35.23590, 31.77377, '안'),
    ('브로드 월',          35.23165, 31.77594, '안'),
    ('히스기야 못',        35.22902, 31.77718, '안'),
    ('로빈슨 아치',        35.23459, 31.77582, '안'),
    ('기바티 주차장 발굴',  35.23510, 31.77444, '안'),
    ('다윗 성',            35.23572, 31.77242, '안'),
    ('윌슨 아치',          35.23432, 31.77707, '안'),
    ('헤롯 극장터',        35.23370, 31.77236, '안'),
]


def dist_m(a, b):
    la = math.radians((a[1] + b[1]) / 2)
    return math.hypot((b[0] - a[0]) * 111320 * math.cos(la), (b[1] - a[1]) * 110540)


def area_ha(ring):
    lat0 = sum(p[1] for p in ring) / len(ring)
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110540
    pts = [(p[0] * kx, p[1] * ky) for p in ring]
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 / 10000


def inside(pt, ring):
    x, y = pt
    c = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            c = not c
    return c


def main():
    ring = [(p[0], p[1]) for p in RING]

    # 시금석부터. 여기서 틀리면 넓이를 재 봐야 소용없다.
    bad = []
    for name, lo, la, want in CHECKS:
        got = '안' if inside((lo, la), ring) else '밖'
        if got != want:
            bad.append('%s: %s (기대 %s)' % (name, got, want))
    if bad:
        raise SystemExit('경계 검증 실패 — ' + ' / '.join(bad))
    print('경계 검증 %d/%d 통과' % (len(CHECKS), len(CHECKS)))

    ha = area_ha(ring)
    per = sum(dist_m(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
    lats = [p[1] for p in ring]
    lons = [p[0] for p in ring]
    la0 = sum(lats) / len(lats)
    ns = (max(lats) - min(lats)) * 110540
    ew = (max(lons) - min(lons)) * 111320 * math.cos(math.radians(la0))

    feats = [{
        'type': 'Feature',
        'properties': {
            'kind': 'extent', 'ko': '예수 당시 예루살렘 성읍',
            'ha': round(ha, 1), 'km2': round(ha / 100, 3),
            'perimeter_km': round(per / 1000, 2),
            'ns_m': round(ns), 'ew_m': round(ew),
            'dug': sum(1 for p in RING if p[3] == '발굴'),
            'guess': sum(1 for p in RING if p[3] == '추정'),
            'unsure': sum(1 for p in RING if p[3] == '불확실'),
        },
        'geometry': {'type': 'Polygon', 'coordinates': [[list(p) for p in ring] + [list(ring[0])]]},
    }]

    # 꼭짓점마다 무엇에 걸었는지 따로 낸다. 지도에서 눌러 볼 수 있게.
    for lo, la, what, cert in RING:
        feats.append({'type': 'Feature',
                      'properties': {'kind': 'anchor', 'ko': what, 'cert': cert},
                      'geometry': {'type': 'Point', 'coordinates': [lo, la]}})

    # 제2성벽 구간만 따로 — 점선으로 그린다.
    unsure = [[p[0], p[1]] for p in RING if p[3] == '불확실']
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'unsure', 'ko': '제2성벽 (확정된 발굴선 없음)'},
                  'geometry': {'type': 'LineString',
                               'coordinates': [[RING[11][0], RING[11][1]]] + unsure +
                                              [[RING[0][0], RING[0][1]]]}})

    fc = {'type': 'FeatureCollection',
          'attribution': '좌표: 발굴 유구 위치 (OpenStreetMap ODbL) · 치수: 성전 산 남벽 실측',
          'note': '예수 당시 성읍의 규모. 성벽 복원도가 아니다.',
          'features': feats}
    OUT.write_text(json.dumps(fc, ensure_ascii=False, indent=1), encoding='utf-8')

    print('넓이 %.1f ha (%.3f km²) · 둘레 %.2f km · 남북 %.0f m · 동서 %.0f m'
          % (ha, ha / 100, per / 1000, ns, ew))
    print('꼭짓점 %d (발굴 %d · 추정 %d · 불확실 %d)'
          % (len(RING), feats[0]['properties']['dug'],
             feats[0]['properties']['guess'], feats[0]['properties']['unsure']))
    print('%s  %.1f KB' % (OUT, OUT.stat().st_size / 1024))


if __name__ == '__main__':
    main()
