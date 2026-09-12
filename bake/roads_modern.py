"""오늘의 도로를 1세기 지도 위에 얹기 위한 자료를 만든다.

이 지도의 배경은 서기 30년경이지만, 도로만은 **오늘 실제로 깔린 길**이다.
옛 길을 추정해 그린 것이 아니다. 성지를 찾는 사람이 '지금 어느 길로 가면
그 자리에 닿는가'를 읽을 수 있게 하려는 것이다.

원본은 OSM 의 motorway·trunk·primary 다(ODbL). 이 상자 안에 22,015개 way,
33만 점이 들어 있어 그대로는 못 쓴다. 세 단계로 줄인다.

1. 잇기   — OSM 의 way 는 교차로·태그 변화마다 토막나 있다. 같은 등급·같은
            노선번호끼리 끝점을 맞춰 한 줄로 잇는다. 조각 수가 크게 준다.
2. 단순화 — Douglas–Peucker. 고속도로는 원래 곡률이 완만해 100 m 로 줄여도
            z13 에서 눈에 띄지 않는다. 등급별로 다르게 준다.
3. 자리수 — 좌표를 소수 5자리(약 1 m)로 끊는다. 그 아래는 파일만 불린다.

입력:  Overpass API (https 는 이 환경에서 urllib 이 막혀 curl 로 받는다)
출력:  data/roads-modern.geojson
"""
import json, math, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT  = ROOT / 'data' / 'roads-modern.geojson'

# 성경 지리권을 덮는 상자. 남쪽은 네게브·아라바, 북쪽은 다마스쿠스·시돈까지.
BBOX = (29.3, 33.8, 34.0, 37.0)          # 남, 서, 북, 동
CLASSES = ('motorway', 'trunk', 'primary')

# 등급별 단순화 허용오차(m). 고속도로일수록 곡률이 완만해 더 줄여도 된다…가 아니라
# 반대다. 고속도로는 넓은 곡선반경으로 길게 휘므로 촘촘한 점이 실제로 모양을 만든다.
# 지방도는 굽이가 많아 보이지만 그 굽이가 지도 축척에서는 거의 안 보인다.
TOL = {'motorway': 60.0, 'trunk': 90.0, 'primary': 130.0}

OVERPASS = 'https://overpass-api.de/api/interpreter'


def fetch():
    q = ('[out:json][timeout:600];\n'
         'way["highway"~"^(%s)$"](%s,%s,%s,%s);\n'
         'out geom;' % ('|'.join(CLASSES), *BBOX))
    print('Overpass 에서 받는 중… (수십 MB, 몇 분 걸린다)')
    r = subprocess.run(['curl', '-s', '--max-time', '900', '-X', 'POST',
                        '-d', q, OVERPASS], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit('Overpass 응답을 받지 못했다: %s' % r.stderr[:400])
    return json.loads(r.stdout)


def clean_ref(tags):
    """노선번호. 여러 개면 첫 번째만. 'IL 90' 같은 접두는 떼고 숫자만 남긴다."""
    ref = (tags.get('ref') or '').split(';')[0].strip()
    if not ref:
        return ''
    ref = ref.replace('–', '-')
    parts = ref.split()
    return parts[-1] if len(parts) > 1 and parts[-1][:1].isdigit() else ref


def chain(segments):
    """끝점이 맞는 조각들을 한 줄로 잇는다.

    좌표를 소수 6자리로 끊어 열쇠를 만든다. OSM 은 같은 교차점을 공유하므로
    좌표가 정확히 일치한다 — 근사 매칭은 필요 없고, 하면 엉뚱한 길이 붙는다.
    """
    key = lambda p: (round(p[0], 6), round(p[1], 6))
    ends = {}
    for i, s in enumerate(segments):
        ends.setdefault(key(s[0]), []).append((i, 'head'))
        ends.setdefault(key(s[-1]), []).append((i, 'tail'))

    used = [False] * len(segments)
    out = []
    for i in range(len(segments)):
        if used[i]:
            continue
        used[i] = True
        line = list(segments[i])
        # 양 끝으로 번갈아 뻗는다.
        for _ in range(2):
            while True:
                cands = [(j, side) for j, side in ends.get(key(line[-1]), []) if not used[j]]
                if len(cands) != 1:          # 갈림길이면 잇지 않는다. 아무 쪽이나 붙이면 길이 꼬인다.
                    break
                j, side = cands[0]
                used[j] = True
                nxt = segments[j] if side == 'head' else segments[j][::-1]
                line.extend(nxt[1:])
            line.reverse()
        out.append(line)
    return out


def dp(line, tol_m):
    """Douglas–Peucker. 위경도를 그 위도의 미터로 환산해 잰다."""
    if len(line) < 3:
        return line
    lat0 = math.radians(sum(p[1] for p in line) / len(line))
    mx, my = 111320.0 * math.cos(lat0), 110540.0

    def seg_dist(p, a, b):
        px, py = (p[0] - a[0]) * mx, (p[1] - a[1]) * my
        bx, by = (b[0] - a[0]) * mx, (b[1] - a[1]) * my
        L = bx * bx + by * by
        if L == 0:
            return math.hypot(px, py)
        t = max(0.0, min(1.0, (px * bx + py * by) / L))
        return math.hypot(px - t * bx, py - t * by)

    keep = [False] * len(line)
    keep[0] = keep[-1] = True
    stack = [(0, len(line) - 1)]
    while stack:
        a, b = stack.pop()
        worst, wi = -1.0, -1
        for i in range(a + 1, b):
            d = seg_dist(line[i], line[a], line[b])
            if d > worst:
                worst, wi = d, i
        if worst > tol_m:
            keep[wi] = True
            stack.append((a, wi))
            stack.append((wi, b))
    return [p for p, k in zip(line, keep) if k]


def length_km(line):
    t = 0.0
    for (x1, y1), (x2, y2) in zip(line, line[1:]):
        lat0 = math.radians((y1 + y2) / 2)
        t += math.hypot((x2 - x1) * 111.320 * math.cos(lat0), (y2 - y1) * 110.540)
    return t


def main():
    data = fetch()
    raw_pts = 0
    groups = {}
    for e in data.get('elements', []):
        geom = e.get('geometry')
        if not geom or len(geom) < 2:
            continue
        tags = e.get('tags', {})
        cls = tags.get('highway')
        if cls not in CLASSES:
            continue
        line = [[p['lon'], p['lat']] for p in geom]
        raw_pts += len(line)
        # 노선번호가 없으면 way id 로 따로 둔다. 번호 없는 길끼리 이으면 안 된다.
        ref = clean_ref(tags)
        groups.setdefault((cls, ref or 'w%d' % e['id']), []).append(line)

    # 같은 등급·같은 노선번호는 한 피처(MultiLineString)로 묶는다. 조각마다 Feature 를
    # 만들면 properties·geometry 껍데기만 110 바이트씩 붙어 파일의 절반을 먹는다.
    bundles, kept_pts = {}, 0
    for (cls, gid), segs in groups.items():
        ref = '' if gid.startswith('w') and gid[1:].isdigit() else gid
        for line in chain(segs):
            line = dp(line, TOL[cls])
            if len(line) < 2:
                continue
            km = length_km(line)
            # 아주 짧은 토막은 버린다. 잇지 못한 램프·연결로라 지도에서 점처럼 보인다.
            if km < (0.8 if cls == 'primary' else 0.4):
                continue
            line = [[round(x, 5), round(y, 5)] for x, y in line]
            kept_pts += len(line)
            bundles.setdefault((cls, ref), []).append(line)

    feats = []
    for (cls, ref), lines in sorted(bundles.items()):
        props = {'cls': cls}
        if ref:
            props['ref'] = ref
        feats.append({'type': 'Feature', 'properties': props,
                      'geometry': {'type': 'MultiLineString', 'coordinates': lines}})

    fc = {'type': 'FeatureCollection',
          'attribution': '© OpenStreetMap contributors (ODbL)',
          'note': '오늘의 도로다. 1세기 노선이 아니다.',
          'features': feats}
    OUT.write_text(json.dumps(fc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    n, lines_by = {}, {}
    for f in feats:
        c = f['properties']['cls']
        n[c] = n.get(c, 0) + 1
        lines_by[c] = lines_by.get(c, 0) + len(f['geometry']['coordinates'])
    print('조각 %d개 → 이어서 %d줄 → 노선 %d개로 묶음'
          % (len(data.get('elements', [])), sum(lines_by.values()), len(feats)))
    print('점 %d개 → %d개 (%.1f%%)' % (raw_pts, kept_pts, 100.0 * kept_pts / raw_pts))
    print('등급별 노선', n, '· 줄', lines_by)
    print('%s  %.0f KB' % (OUT, OUT.stat().st_size / 1024))


if __name__ == '__main__':
    main()
