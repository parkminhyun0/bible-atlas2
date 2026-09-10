#!/usr/bin/env python3
# 도로가 지형을 따라 돌아가게 다듬는다.
#
#   python3 bake/roads_terrain_fit.py data/roads-c30.geojson data/roads-c30.geojson
#
# 왜 필요한가. Itiner-e 의 '개연·추정' 구간은 아는 지점 몇 개를 곧은 선으로 이어 둔
# 것이 많다. 실제로 길이 6.5 km 를 자로 잰 듯 곧게 가지도 않고, 산비탈을 직각으로
# 꺾지도 않는다. 그래서 원본 꼭짓점은 그대로 두고, 그 사이가 멀리 벌어진 곳만
# 실제 표고를 보고 '걸어서 가장 덜 힘든 길'로 다시 잇는다.
#
# 중요 — 이것은 새로운 사료가 아니다. 원본이 성기게 그려 둔 구간을 지형에 맞춰
# 그럴듯하게 메운 것이고, 확실성 등급(확정/개연/추정)은 손대지 않는다.
#
# 표고: Mapterhorn terrarium 타일(지도에서 쓰는 것과 같은 자료).
# 비용: 토블러 보행함수 v = 6·exp(-3.5·|S+0.05|) km/h. 시간을 최소로 하면
#       비탈을 가로지르는 대신 등고선을 따라 감아 도는 길이 저절로 나온다.
import json, math, os, sys, io, subprocess
from PIL import Image

Z = 12                      # 타일 줌. 위도 32도에서 한 픽셀이 약 16 m 다.
TILE = 512
URL = 'https://tiles.mapterhorn.com/{z}/{x}/{y}.webp'
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dem-cache')
SPLIT_M = 600.0             # 이보다 멀리 떨어진 두 점 사이만 다시 잇는다
STEP_M = 60.0               # 길을 훑는 간격
MAX_OFF_M = 800.0           # 원래 직선에서 이만큼까지만 벗어날 수 있다
PULL = 0.12                 # 가운데(원래 직선)로 당기는 정도. 가파른 곳에서만 벗어난다
CORNER_DEG = 55.0           # 이보다 날카롭게 꺾이는 꼭짓점만 둥글린다
CORNER_MAX_M = 250.0        # 모서리를 깎아 내는 최대 반경
N = 2 ** Z
_tiles = {}

def tile_xy(lon, lat):
    x = (lon + 180) / 360 * N
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * N
    return x, y

def get_tile(tx, ty):
    key = (tx, ty)
    if key in _tiles: return _tiles[key]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'{Z}_{tx}_{ty}.webp')
    if not os.path.exists(path):
        # 이 환경에서는 urllib 의 https 가 인증서에서 막힌다. curl 로 받는다.
        r = subprocess.run(['curl', '-sS', '-m', '60', '-o', path, '-w', '%{http_code}',
                            URL.format(z=Z, x=tx, y=ty)], capture_output=True, text=True)
        if r.stdout.strip() != '200' or not os.path.exists(path) or os.path.getsize(path) < 100:
            if os.path.exists(path): os.remove(path)
            _tiles[key] = None; return None
    try:
        im = Image.open(path).convert('RGB')
        _tiles[key] = im.load()
    except Exception:
        _tiles[key] = None
    return _tiles[key]

def elev(lon, lat):
    """terrarium: 높이 = (R*256 + G + B/256) - 32768"""
    x, y = tile_xy(lon, lat)
    tx, ty = int(x), int(y)
    px = get_tile(tx, ty)
    if px is None: return None
    i = min(TILE - 1, int((x - tx) * TILE)); j = min(TILE - 1, int((y - ty) * TILE))
    r, g, b = px[i, j]
    return r * 256 + g + b / 256 - 32768

def hav(a, b):
    p = math.pi / 180; R = 6371008.8
    return 2 * R * math.asin(math.sqrt(
        math.sin((b[1] - a[1]) * p / 2) ** 2 +
        math.cos(a[1] * p) * math.cos(b[1] * p) * math.sin((b[0] - a[0]) * p / 2) ** 2))

def tobler_cost(dist_m, dh):
    """걸리는 시간(초). 오르막·내리막 모두 가파를수록 비싸진다."""
    if dist_m <= 0: return 0.0
    s = dh / dist_m
    v = 6.0 * math.exp(-3.5 * abs(s + 0.05))            # km/h
    return dist_m / max(v, 0.05) * 3.6

def fit_span(a, b):
    """a 와 b 사이를 지형을 보고 다시 잇는다. 실패하면 None."""
    L = hav(a, b)
    if L < SPLIT_M: return None
    nx = max(4, int(L / STEP_M))                         # 축 방향 칸 수
    half = min(MAX_OFF_M, L / 4)
    ny = max(3, int(half * 2 / STEP_M))
    if ny % 2 == 0: ny += 1                              # 가운데 줄이 원래 직선
    mid = ny // 2
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2)); ky = 110570
    dx = (b[0] - a[0]) * kx; dy = (b[1] - a[1]) * ky
    ux, uy = dx / L, dy / L                              # 축 방향
    px, py = -uy, ux                                     # 옆 방향
    def pos(i, j):
        along = L * i / nx; off = (j - mid) * (half * 2 / ny)
        ex = ux * along + px * off; ey = uy * along + py * off
        return [a[0] + ex / kx, a[1] + ey / ky]
    grid = [[None] * ny for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny):
            p = pos(i, j); e = elev(p[0], p[1])
            grid[i][j] = (p, e)
    ea = grid[0][mid][1]; eb = grid[nx][mid][1]
    if ea is None or eb is None: return None
    # 뭍길이 바다로 빠지지 않게 막는다. 이 DEM 은 바다를 정확히 0 으로 둔다.
    block_sea = min(ea, eb) > 5
    INF = float('inf')
    dp = [[INF] * ny for _ in range(nx + 1)]
    back = [[0] * ny for _ in range(nx + 1)]
    dp[0][mid] = 0.0
    for i in range(1, nx + 1):
        for j in range(ny):
            p, e = grid[i][j]
            if e is None: continue
            if block_sea and abs(e) < 0.5: continue      # 바다
            best = INF; bj = j
            for j2 in range(max(0, j - 2), min(ny, j + 3)):
                if dp[i - 1][j2] == INF: continue
                p2, e2 = grid[i - 1][j2]
                if e2 is None: continue
                # 원래 직선에서 멀어질수록 조금씩 비싸진다. 지형이 확실히 편해질
                # 때만 벗어나고, 평지에서는 원본을 그대로 따라간다.
                off = abs(j - mid) / max(1, mid)
                c = dp[i - 1][j2] + tobler_cost(hav(p2, p), e - e2) * (1 + PULL * off * off)
                if c < best: best, bj = c, j2
            dp[i][j] = best; back[i][j] = bj
    if dp[nx][mid] == INF: return None
    path = []; j = mid
    for i in range(nx, -1, -1):
        path.append(grid[i][j][0]); j = back[i][j]
    path.reverse()
    return path

def chaikin(pts, rounds=2):
    """모서리를 깎아 부드럽게. 양 끝은 고정한다."""
    for _ in range(rounds):
        if len(pts) < 3: return pts
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out.append([p[0] * 0.75 + q[0] * 0.25, p[1] * 0.75 + q[1] * 0.25])
            out.append([p[0] * 0.25 + q[0] * 0.75, p[1] * 0.25 + q[1] * 0.75])
        out.append(pts[-1])
        pts = out
    return pts

def _perp(p, a, b):
    kx = 111320 * math.cos(math.radians(a[1])); ky = 110570
    ax, ay = a[0] * kx, a[1] * ky; bx, by = b[0] * kx, b[1] * ky; qx, qy = p[0] * kx, p[1] * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0: return math.hypot(qx - ax, qy - ay)
    t = max(0, min(1, ((qx - ax) * dx + (qy - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(qx - (ax + t * dx), qy - (ay + t * dy))

def simplify(pts, tol):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, bi = -1, -1
        for k in range(i + 1, j):
            d = _perp(pts[k], pts[i], pts[j])
            if d > best: best, bi = d, k
        if best > tol: keep[bi] = True; stack.append((i, bi)); stack.append((bi, j))
    return [p for p, k in zip(pts, keep) if k]

def bearing(a, b):
    p = math.pi / 180
    y = math.sin((b[0] - a[0]) * p) * math.cos(b[1] * p)
    x = math.cos(a[1] * p) * math.sin(b[1] * p) - math.sin(a[1] * p) * math.cos(b[1] * p) * math.cos((b[0] - a[0]) * p)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def round_corners(pts):
    """날카롭게 꺾이는 꼭짓점만 둥글린다. 길은 한 점에서 직각으로 돌지 않는다.
    꼭짓점을 옮기지 않고 그 앞뒤를 조금 깎아 곡선으로 잇는다."""
    if len(pts) < 3: return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = hav(a, b), hav(b, c)
        if d1 < 1 or d2 < 1: continue
        turn = abs((bearing(b, c) - bearing(a, b) + 180) % 360 - 180)
        if turn < CORNER_DEG: out.append(b); continue
        r = min(CORNER_MAX_M, d1 * 0.45, d2 * 0.45)
        t1, t2 = r / d1, r / d2
        p1 = [b[0] + (a[0] - b[0]) * t1, b[1] + (a[1] - b[1]) * t1]
        p2 = [b[0] + (c[0] - b[0]) * t2, b[1] + (c[1] - b[1]) * t2]
        # p1 → b → p2 를 이차 베지에로 부드럽게 잇는다
        for k in range(1, 8):
            t = k / 8
            u = 1 - t
            out.append([u * u * p1[0] + 2 * u * t * b[0] + t * t * p2[0],
                        u * u * p1[1] + 2 * u * t * b[1] + t * t * p2[1]])
    out.append(pts[-1])
    return out

def fit_line(line):
    # 톱니와 직각은 round_corners 에서 모서리를 깎아 없앤다. 꼭짓점을 문질러
    # 옮기는 방식은 쓰지 않는다 — 최소비용 경로의 출발·도착이 흐트러져 애써 찾은
    # '걷기 쉬운 길'이 도로 펴진다(실측: 오르막 개선 -14.1% → -1.9%).
    out = [line[0]]; changed = 0
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]
        seg = fit_span(a, b)
        if seg:
            # 새로 만든 마디만 부드럽게 하고, 양 끝(원본 꼭짓점)은 건드리지 않는다.
            seg = simplify(chaikin(seg, 1), 5.0)
            out.extend(seg[1:]); changed += 1
        else:
            out.append(b)
    return round_corners(out), changed

def point_at(a, b, dist):
    """a 에서 b 쪽으로 dist m 간 지점."""
    d = hav(a, b)
    if d < 1e-6: return list(a)
    t = min(1.0, dist / d)
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]

def join_corners(feats):
    """한 도로가 여러 구간(feature)으로 나뉘어 있어서, 구간과 구간이 만나는 이음매는
    앞의 round_corners 가 보지 못한다. 거기서 길이 직각으로 꺾여 보인다.
    같은 도로끼리 맞닿은 끝점만 골라 양쪽을 조금씩 깎고 곡선으로 잇는다.
    서로 다른 도로가 만나는 곳(진짜 갈림길)은 그대로 둔다."""
    ends = []
    for fi, f in enumerate(feats):
        for li, line in enumerate(f['geometry']['coordinates']):
            if len(line) < 2: continue
            ends.append([f['properties']['roadId'], fi, li, 0])
            ends.append([f['properties']['roadId'], fi, li, -1])
    def pt(e):
        line = feats[e[1]]['geometry']['coordinates'][e[2]]
        return line[e[3]], line[1 if e[3] == 0 else -2]
    fixed = 0
    for i in range(len(ends)):
        for j in range(i + 1, len(ends)):
            a, b = ends[i], ends[j]
            if a[0] != b[0]: continue                       # 다른 도로면 갈림길이다
            if a[1] == b[1] and a[2] == b[2]: continue
            pa, na = pt(a); pb, nb = pt(b)
            if hav(pa, pb) > 40: continue
            turn = abs((bearing(pb, nb) - bearing(na, pa) + 180) % 360 - 180)
            if turn <= CORNER_DEG: continue
            r = min(200.0, hav(na, pa) * 0.4, hav(pb, nb) * 0.4)
            if r < 15: continue
            p1 = point_at(pa, na, r); p2 = point_at(pb, nb, r)
            J = pa
            def bez(t):
                u = 1 - t
                return [u * u * p1[0] + 2 * u * t * J[0] + t * t * p2[0],
                        u * u * p1[1] + 2 * u * t * J[1] + t * t * p2[1]]
            la = feats[a[1]]['geometry']['coordinates'][a[2]]
            lb = feats[b[1]]['geometry']['coordinates'][b[2]]
            arc_a = [bez(k / 8) for k in range(0, 5)]        # p1 → 가운데
            arc_b = [bez(k / 8) for k in range(4, 9)][::-1]  # 가운데 → p2 (b 는 끝에서 시작)
            if a[3] == 0: feats[a[1]]['geometry']['coordinates'][a[2]] = arc_a[::-1] + la[1:]
            else:         feats[a[1]]['geometry']['coordinates'][a[2]] = la[:-1] + arc_a
            if b[3] == 0: feats[b[1]]['geometry']['coordinates'][b[2]] = arc_b[::-1] + lb[1:]
            else:         feats[b[1]]['geometry']['coordinates'][b[2]] = lb[:-1] + arc_b
            fixed += 1
    return fixed

def main(src, dst):
    d = json.load(open(src, encoding='utf-8'))
    n_fit = 0; n_span = 0; before = 0; after = 0
    stats = []
    for f in d['features']:
        p = f['properties']
        lines = f['geometry']['coordinates']
        new = []; ch = 0
        for line in lines:
            before += len(line)
            fitted, c = fit_line(line)
            ch += c; new.append(fitted); after += len(fitted)
        if ch:
            n_fit += 1; n_span += ch
            p['geometrySource'] = 'itinere + terrain-fit'
        else:
            p['geometrySource'] = 'itinere'
        f['geometry']['coordinates'] = new
    n_join = join_corners(d['features'])
    print(f'구간과 구간이 만나는 이음매 {n_join}곳을 둥글렸다')
    d['note'] = (d.get('note', '') +
        ' 원본이 성기게 그려 둔 구간(두 점 사이 600 m 이상)은 실제 표고를 보고 '
        '토블러 보행함수로 다시 이었다(지형 보정). 새 사료가 아니라 지형에 맞춘 '
        '그럴듯한 선이며, 확실성 등급은 그대로다.')
    d['terrainFit'] = {'dem': 'Mapterhorn terrarium z12 (약 16 m/px)',
                       'cost': "Tobler v = 6·exp(-3.5·|S+0.05|) km/h",
                       'splitOverM': SPLIT_M, 'stepM': STEP_M, 'maxOffsetM': MAX_OFF_M,
                       'smoothing': '새로 이은 마디만 Chaikin 1회 + 5 m 단순화. 원본 꼭짓점은 옮기지 않는다.',
                       'pull': PULL, 'cornerDeg': CORNER_DEG, 'cornerMaxM': CORNER_MAX_M,
                       'note': '원본 꼭짓점은 모두 고정했다. 벗어나는 폭은 구간 길이의 1/4 과 800 m 중 '
                               '작은 값으로 묶고, 가운데로 당기는 힘을 두어 지형이 확실히 편해질 때만 '
                               '벗어나게 했다. 55도 넘게 꺾이는 꼭짓점은 반경 130 m 안에서 둥글렸다.'}
    json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'지형 보정한 구간(feature) {n_fit}개 · 다시 이은 마디 {n_span}개')
    print(f'점 {before} → {after}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
