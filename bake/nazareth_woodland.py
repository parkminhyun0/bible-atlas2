#!/usr/bin/env python3
# 나사렛 둘레의 실제 삼림·관목지 경계를 내려받아 정리한다.
#
#   python3 bake/nazareth_woodland.py data/nazareth-woodland.geojson
#
# 나무를 한 그루씩 실제 자리에 놓을 수는 없다. 그런 자료는 없다. 할 수 있는 것은
# '나무가 실제로 있는 자리(숲의 경계)'를 OSM 에서 가져와, 그 안에만 나무를 세우는
# 것이다. 그루의 위치는 화면에서 계산해 뿌린다(같은 씨앗이면 늘 같은 자리).
#
# 그리고 이 숲의 성격을 분명히 해 둔다 — 나사렛 둘레의 이름 붙은 숲(나사렛 비탈 숲,
# 세포리스 숲, 다볼산 숲, 발포어 숲)은 대부분 20세기에 심은 조림지다. 1세기의
# 풍경이 아니다.
import json, math, sys, os, subprocess

BOX = (32.67, 35.25, 32.75, 35.36)      # 남, 서, 북, 동
OVERPASS = 'https://overpass.kumi.systems/api/interpreter'
QUERY = """[out:json][timeout:180];
(
  way["natural"="wood"]({0},{1},{2},{3});
  way["landuse"="forest"]({0},{1},{2},{3});
  way["natural"="scrub"]({0},{1},{2},{3});
  way["landuse"="orchard"]({0},{1},{2},{3});
  relation["natural"="wood"]({0},{1},{2},{3});
  relation["landuse"="forest"]({0},{1},{2},{3});
);
out geom;""".format(*BOX)

# 이 지역 식생. 수고는 지중해성 식생의 일반적인 범위이며 개별 측정값이 아니다.
KINDS = {
  'forest': {'ko': '숲(조림지)', 'density': 380,          # 그루/ha
             'species': [('pine', '알레포 소나무', 0.62, (8, 15)),
                         ('cypress', '이탈리아 사이프러스', 0.10, (10, 18)),
                         ('oak', '참나무(케르메스·타보르)', 0.20, (4, 11)),
                         ('carob', '캐롭(쥐엄나무)', 0.08, (5, 9))]},
  'scrub':  {'ko': '관목지(마키·가리그)', 'density': 900,
             'species': [('shrub', '가시덤불·시스투스', 0.75, (0.4, 1.6)),
                         ('oak', '케르메스 참나무 덤불', 0.25, (1.5, 4))]},
  'orchard': {'ko': '과수원', 'density': 200,
             'species': [('olive', '올리브', 0.80, (3.5, 6.5)),
                         ('carob', '무화과·석류 등', 0.20, (3, 6))]},
}

def fetch():
    r = subprocess.run(['curl', '-sS', '-m', '300', '-X', 'POST', '--data-binary', QUERY, OVERPASS],
                       capture_output=True)
    return json.loads(r.stdout.decode('utf-8'))

def ring_area_ha(ring):
    R = 6371008.8; s = 0.0
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]
        s += math.radians(b[0] - a[0]) * (2 + math.sin(math.radians(a[1])) + math.sin(math.radians(b[1])))
    return abs(s * R * R / 2) / 10000

def perp(p, a, b):
    kx = 111320 * math.cos(math.radians(a[1])); ky = 110570
    ax, ay = a[0]*kx, a[1]*ky; bx, by = b[0]*kx, b[1]*ky; px, py = p[0]*kx, p[1]*ky
    dx, dy = bx-ax, by-ay
    if dx == 0 and dy == 0: return math.hypot(px-ax, py-ay)
    t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / (dx*dx + dy*dy)))
    return math.hypot(px - (ax+t*dx), py - (ay+t*dy))

def simplify(pts, tol=8.0):
    if len(pts) < 4: return pts
    keep = [False]*len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    while stack:
        i, j = stack.pop()
        best, bi = -1, -1
        for k in range(i+1, j):
            d = perp(pts[k], pts[i], pts[j])
            if d > best: best, bi = d, k
        if best > tol: keep[bi] = True; stack.append((i, bi)); stack.append((bi, j))
    out = [p for p, k in zip(pts, keep) if k]
    return out if len(out) >= 4 else pts

def rings_from(el):
    out = []
    if el['type'] == 'way' and el.get('geometry'):
        r = [[round(p['lon'], 6), round(p['lat'], 6)] for p in el['geometry']]
        if r[0] != r[-1]: r.append(r[0])
        if len(r) >= 4: out.append(r)
    elif el['type'] == 'relation':
        for m in el.get('members', []):
            if m.get('role') == 'outer' and m.get('geometry'):
                r = [[round(p['lon'], 6), round(p['lat'], 6)] for p in m['geometry']]
                if r[0] != r[-1]: r.append(r[0])
                if len(r) >= 4: out.append(r)
    return out

def main(dst):
    d = fetch()
    feats = []; tot = {}
    for el in d['elements']:
        t = el.get('tags', {})
        kind = t.get('natural') or t.get('landuse')
        if kind == 'wood': kind = 'forest'
        if kind not in KINDS: continue
        for ring in rings_from(el):
            ha = ring_area_ha(ring)
            if ha < 0.15: continue                     # 아주 작은 조각은 뺀다
            ring = simplify(ring)
            tot[kind] = tot.get(kind, 0) + ha
            feats.append({'type': 'Feature',
                'properties': {'kind': kind, 'kindKo': KINDS[kind]['ko'],
                               'areaHa': round(ha, 2), 'osmId': f"{el['type']}/{el['id']}",
                               'name': t.get('name'), 'nameEn': t.get('name:en')},
                'geometry': {'type': 'Polygon', 'coordinates': [ring]}})
    out = {'type': 'FeatureCollection', 'name': 'nazareth-woodland',
      'note': '나사렛 둘레의 실제 삼림·관목지·과수원 경계다. 나무 한 그루 한 그루의 자리는 아니다. '
              '그루 위치는 이 경계 안에서 화면이 계산해 뿌린다(같은 씨앗이면 늘 같은 자리).',
      'caution': '여기 이름 붙은 숲(나사렛 비탈 숲·세포리스 숲·다볼산 숲·발포어 숲 등)은 대부분 '
                 '20세기에 심은 조림지다. 1세기 나사렛의 풍경이 아니다. 그 시절 이 비탈은 '
                 '계단식 올리브밭과 포도원, 참나무·테레빈 성긴 숲, 방목지가 섞인 땅이었다.',
      'attribution': '© OpenStreetMap contributors (ODbL). Overpass 로 내려받아 8 m 단순화했다.',
      'box': {'south': BOX[0], 'west': BOX[1], 'north': BOX[2], 'east': BOX[3]},
      'kinds': {k: {'ko': v['ko'], 'densityPerHa': v['density'],
                    'species': [{'id': s[0], 'ko': s[1], 'share': s[2], 'heightM': list(s[3])} for s in v['species']]}
                for k, v in KINDS.items()},
      'heightNote': '수고는 지중해성 식생의 일반적인 범위이며 개별 나무를 잰 값이 아니다.',
      'features': feats}
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    pts = sum(len(f['geometry']['coordinates'][0]) for f in feats)
    print(f'폴리곤 {len(feats)}개 · 점 {pts}개 · {os.path.getsize(dst)//1024} KB')
    for k, v in sorted(tot.items(), key=lambda x: -x[1]):
        est = int(v * KINDS[k]['density'])
        print(f'  {KINDS[k]["ko"]:18} {v:7.0f} ha · 밀도 {KINDS[k]["density"]}/ha → 약 {est:,}그루')

if __name__ == '__main__':
    main(sys.argv[1])
