"""오늘의 도로를 1세기 지도 위에 얹기 위한 자료를 만든다.

이 지도의 배경은 서기 30년경이지만, 도로만은 **오늘 실제로 깔린 길**이다.
옛 길을 추정해 그린 것이 아니다. 성지를 찾는 사람이 '지금 어느 길로 가면
그 자리에 닿는가'를 읽을 수 있게 하려는 것이다.

**도형은 줄이지 않는다.** 처음에는 Douglas–Peucker 로 33만 점을 1.4만 점까지
줄였는데(고속 60 m · 간선 90 m · 주요 130 m), 그러면 완만한 곡선이 긴 직선으로
떨어지고 남은 꼭짓점이 뾰족하게 꺾인다. 허용오차 안이라도 눈에는 보인다.
그래서 OSM 이 가진 점을 하나도 버리지 않는다.

대신 좌표를 **인코딩된 폴리라인**으로 담는다. 33만 점을 [경도,위도] 배열로
쓰면 6.4 MB 지만, 앞 점과의 차이를 밑수 32 로 적으면 1.4 MB 다(점당 4.3바이트).
차이값은 대개 작아서 — 도로 위 이웃한 점은 10~50 m 떨어져 있다 — 한두 글자로
적힌다. 정밀도는 소수 6자리(약 0.11 m)로, 가장 크게 확대해도 계단이 지지 않는다.

줌에 따른 간략화는 MapLibre 의 geojson 소스가 타일마다 알아서 한다. 우리가 미리
줄일 이유가 없다 — 미리 줄이면 확대했을 때 되돌릴 방법이 없다.

입력:  Overpass API (https 는 이 환경에서 urllib 이 막혀 curl 로 받는다)
출력:  data/roads-modern.json   (GeoJSON 이 아니다. 읽는 쪽에서 펼친다)
"""
import json, math, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT  = ROOT / 'data' / 'roads-modern.json'

# 성경 지리권을 덮는 상자. 남쪽은 네게브·아라바, 북쪽은 다마스쿠스·시돈까지.
BBOX = (29.3, 33.8, 34.0, 37.0)          # 남, 서, 북, 동
CLASSES = ('motorway', 'trunk', 'primary')
PRECISION = 6                            # 소수 6자리 ≈ 0.11 m

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

    도형은 바뀌지 않는다 — 이어 붙이기만 한다. 줄 수가 줄면 파일의 껍데기가 줄고,
    MapLibre 가 타일마다 다루는 조각 수도 준다.

    좌표를 소수 6자리로 끊어 열쇠를 만든다. OSM 은 같은 교차점을 공유하므로
    좌표가 정확히 일치한다 — 근사 매칭은 필요 없고, 하면 엉뚱한 길이 붙는다.
    갈림길(후보가 둘 이상)에서는 잇지 않는다. 아무 쪽이나 붙이면 길이 꼬인다.
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
        for _ in range(2):                    # 양 끝으로 번갈아 뻗는다
            while True:
                cands = [(j, side) for j, side in ends.get(key(line[-1]), []) if not used[j]]
                if len(cands) != 1:
                    break
                j, side = cands[0]
                used[j] = True
                nxt = segments[j] if side == 'head' else segments[j][::-1]
                line.extend(nxt[1:])
            line.reverse()
        out.append(line)
    return out


def encode(line, prec=PRECISION):
    """인코딩된 폴리라인. 경도·위도 순으로, 앞 점과의 차이를 밑수 32 로 적는다."""
    f = 10 ** prec
    out = []
    px = py = 0
    for x, y in line:
        ix, iy = round(x * f), round(y * f)
        for d in (ix - px, iy - py):
            v = ~(d << 1) if d < 0 else (d << 1)
            while v >= 0x20:
                out.append(chr((0x20 | (v & 0x1f)) + 63))
                v >>= 5
            out.append(chr(v + 63))
        px, py = ix, iy
    return ''.join(out)


def length_km(line):
    t = 0.0
    for (x1, y1), (x2, y2) in zip(line, line[1:]):
        lat0 = math.radians((y1 + y2) / 2)
        t += math.hypot((x2 - x1) * 111.320 * math.cos(lat0), (y2 - y1) * 110.540)
    return t


def main():
    data = fetch()
    groups = {}
    raw_pts = 0
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

    # 같은 등급·같은 노선번호는 한 묶음으로 낸다. 조각마다 껍데기를 붙이면 그것만으로
    # 파일의 절반을 먹는다.
    bundles, kept_pts, total_km, nlines = {}, 0, 0.0, 0
    for (cls, gid), segs in groups.items():
        ref = '' if gid.startswith('w') and gid[1:].isdigit() else gid
        for line in chain(segs):
            if len(line) < 2:
                continue
            kept_pts += len(line)
            total_km += length_km(line)
            nlines += 1
            bundles.setdefault((cls, ref), []).append(encode(line))

    feats = []
    for (cls, ref), enc in sorted(bundles.items()):
        f = {'cls': cls, 'enc': enc}
        if ref:
            f['ref'] = ref
        feats.append(f)

    doc = {'format': 'roads-encoded-polyline', 'precision': PRECISION,
           'attribution': '© OpenStreetMap contributors (ODbL)',
           'note': '오늘의 도로다. 1세기 노선이 아니다. 도형은 OSM 원본 그대로, 줄이지 않았다.',
           'features': feats}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    n = {}
    for f in feats:
        n[f['cls']] = n.get(f['cls'], 0) + 1
    print('조각 %d개 → 이어서 %d줄 → 노선 %d개로 묶음' % (len(data.get('elements', [])), nlines, len(feats)))
    print('점 %d개 → %d개 (버린 것 없음)' % (raw_pts, kept_pts))
    print('등급별 노선', n, '· 총 연장 %.0f km' % total_km)
    print('%s  %.2f MB (점당 %.1f 바이트)'
          % (OUT, OUT.stat().st_size / 1e6, OUT.stat().st_size / kept_pts))


if __name__ == '__main__':
    main()
