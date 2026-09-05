#!/usr/bin/env python3
"""
사건 동선 생성기 — 지형 최소비용경로
=====================================
직선이 아니라 사람이 실제로 걸었을 길을 그린다. 청동기에는 포장도로가 없었으므로
'지형이 허락하는 최소 노력 경로'가 가장 방어 가능한 재구성이다. 고고학에서 쓰는
최소비용경로(LCP) 분석과 같은 방법이다.

  비용   Tobler 도보 함수. v = 6·exp(-3.5·|S + 0.05|) km/h  (S = 경사)
  DEM    AWS terrarium 타일. 구간 길이에 따라 줌을 고른다
  바다    지도 가장자리에서 홍수채움으로 찾아 통행 불가로 둔다

  python bake/routes.py --out data/genesis-routes.geojson
"""
import argparse, heapq, json, math, pathlib, sys
import numpy as np
from PIL import Image
import requests

TILE = 256
DEM_URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
CACHE = pathlib.Path('bake/dem-cache')
S = requests.Session()

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    lat = max(min(lat, 85.05112878), -85.05112878)
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def tile_to_lonlat(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat

def fetch_tile(z, x, y):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f'{z}_{x}_{y}.png'
    if not f.exists():
        r = S.get(DEM_URL.format(z=z, x=x, y=y), timeout=60)
        if r.status_code != 200:
            return None
        f.write_bytes(r.content)
    try:
        return np.asarray(Image.open(f).convert('RGB'), dtype=np.float64)
    except Exception:
        f.unlink(missing_ok=True)
        return None

def dem_for_box(w, s, e, n, z):
    """상자를 덮는 DEM 격자와 좌표 변환에 필요한 원점을 돌려준다."""
    x0, y0 = lonlat_to_tile(w, n, z)
    x1, y1 = lonlat_to_tile(e, s, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    grid = np.zeros(((ty1 - ty0 + 1) * TILE, (tx1 - tx0 + 1) * TILE), np.float32)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            a = fetch_tile(z, tx, ty)
            if a is None:
                continue
            elev = a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768
            grid[(ty - ty0) * TILE:(ty - ty0 + 1) * TILE,
                 (tx - tx0) * TILE:(tx - tx0 + 1) * TILE] = elev
    return grid, tx0 * TILE, ty0 * TILE

# 바다 판정은 구간 상자 안에서 하면 안 된다. 상자 가장자리가 요단 지구대를 자르면
# 해수면 아래 육지(-200~-430m)가 통째로 바다로 잡힌다. 실제로 그래서 여러 구간이
# '경로 없음'으로 떨어졌다. 지역 전체를 한 번 훑어 바깥 바다와 이어진 물만 바다로 본다.
_SEA = None
def global_sea(z=6, box=(24.0, 16.0, 58.0, 46.0)):
    """지역 전체의 바다 마스크를 한 번만 만든다. 바깥 경계에서 홍수채움하므로
    사해·갈릴리·카스피 같은 내륙 분지는 육지로 남는다."""
    global _SEA
    if _SEA is not None: return _SEA
    w, s, e, n = box
    elev, ox, oy = dem_for_box(w, s, e, n, z)
    h, wd = elev.shape
    water = elev <= 0
    seen = np.zeros_like(water)
    stack = [(i, j) for i in range(h) for j in (0, wd - 1) if water[i, j]]
    stack += [(i, j) for j in range(wd) for i in (0, h - 1) if water[i, j]]
    while stack:
        i, j = stack.pop()
        if seen[i, j] or not water[i, j]: continue
        seen[i, j] = True
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            a, b = i + di, j + dj
            if 0 <= a < h and 0 <= b < wd and water[a, b] and not seen[a, b]:
                stack.append((a, b))
    _SEA = (seen, ox, oy, z)
    print(f'  바다 마스크: z{z} {h}x{wd} · 바다 {seen.mean()*100:.0f}%')
    return _SEA

def sea_at(lons, lats):
    """경위도 배열을 지역 바다 마스크에 조회한다."""
    seen, ox, oy, z = global_sea()
    h, w = seen.shape
    n = 2 ** z
    xs = ((lons + 180.0) / 360.0 * n * TILE - ox).astype(np.int64)
    la = np.clip(lats, -85.0, 85.0)
    ys = ((1 - np.log(np.tan(np.radians(la)) + 1 / np.cos(np.radians(la))) / np.pi) / 2 * n * TILE - oy).astype(np.int64)
    ok = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    out = np.zeros(lons.shape, bool)
    out[ok] = seen[ys[ok], xs[ok]]
    return out

def least_cost_path(elev, blocked, start, goal, mpp):
    """Tobler 도보 함수를 비용으로 쓰는 8방향 다익스트라."""
    h, w = elev.shape
    INF = np.inf
    dist = np.full(h * w, INF)
    prev = np.full(h * w, -1, np.int64)
    si, sj = start; gi, gj = goal
    s = si * w + sj; g = gi * w + gj
    dist[s] = 0.0
    pq = [(0.0, s)]
    NB = [(-1,0,1.0),(1,0,1.0),(0,-1,1.0),(0,1,1.0),
          (-1,-1,1.4142),(-1,1,1.4142),(1,-1,1.4142),(1,1,1.4142)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        if u == g: break
        ui, uj = divmod(u, w)
        eu = elev[ui, uj]
        for di, dj, k in NB:
            vi, vj = ui + di, uj + dj
            if vi < 0 or vi >= h or vj < 0 or vj >= w: continue
            if blocked[vi, vj]: continue
            run = k * mpp
            slope = (elev[vi, vj] - eu) / run
            speed = 6.0 * math.exp(-3.5 * abs(slope + 0.05))     # km/h
            if speed < 0.15: speed = 0.15
            nd = d + (run / 1000.0) / speed                       # 시간(h)
            v = vi * w + vj
            if nd < dist[v]:
                dist[v] = nd; prev[v] = u
                heapq.heappush(pq, (nd, v))
    if not np.isfinite(dist[g]): return None, None
    path, u = [], g
    while u != -1:
        path.append(divmod(u, w)); u = prev[u]
    return path[::-1], dist[g]

def simplify(pts, tol):
    """Douglas-Peucker. 경로 점이 수천 개가 되므로 형태를 지키며 줄인다."""
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy) or 1e-12
    worst, wi = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / n
        if d > worst: worst, wi = d, i
    if worst <= tol: return [a, b]
    return simplify(pts[:wi + 1], tol)[:-1] + simplify(pts[wi:], tol)

def zoom_for(km):
    if km > 600: return 6
    if km > 200: return 7
    if km > 60:  return 8
    return 9

def haversine(a, b):
    R = 6371.0
    (lo1, la1), (lo2, la2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(x))

def leg(a, b, verbose=True):
    """두 지점 사이 지형 최소비용경로를 [(lon,lat), ...] 로 돌려준다."""
    km = haversine(a, b)
    z = zoom_for(km)
    pad = max(0.45, km / 111.0 * 0.35)
    w = min(a[0], b[0]) - pad; e = max(a[0], b[0]) + pad
    s = min(a[1], b[1]) - pad; n = max(a[1], b[1]) + pad
    elev, ox, oy = dem_for_box(w, s, e, n, z)
    def to_px(p):
        x, y = lonlat_to_tile(p[0], p[1], z)
        return int(round(y * TILE - oy)), int(round(x * TILE - ox))
    h, wd = elev.shape
    si, sj = to_px(a); gi, gj = to_px(b)
    si = max(0, min(h-1, si)); gi = max(0, min(h-1, gi))
    sj = max(0, min(wd-1, sj)); gj = max(0, min(wd-1, gj))
    # 격자 각 칸의 경위도를 구해 지역 바다 마스크에 조회한다
    ii, jj = np.meshgrid(np.arange(h), np.arange(wd), indexing='ij')
    nn = 2 ** z
    lon_g = (jj + ox) / TILE / nn * 360.0 - 180.0
    lat_g = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (ii + oy) / TILE / nn))))
    blocked = sea_at(lon_g, lat_g)
    blocked[si, sj] = blocked[gi, gj] = False       # 항구는 물가에 있다
    lat_mid = (s + n) / 2
    mpp = 40075016.686 * math.cos(math.radians(lat_mid)) / (TILE * 2 ** z)
    path, hours = least_cost_path(elev, blocked, (si, sj), (gi, gj), mpp)
    if path is None:
        if verbose: print(f'      경로 없음 — 직선으로 대체 ({km:.0f} km)')
        return [a, b], km, None
    pts = []
    for (i, j) in path:
        lon, lat = tile_to_lonlat((j + ox) / TILE, (i + oy) / TILE, z)
        pts.append((round(lon, 4), round(lat, 4)))
    pts = simplify(pts, 0.008)
    dist = sum(haversine(pts[i], pts[i+1]) for i in range(len(pts)-1))
    if verbose:
        print(f'      z{z} 격자 {h}x{wd} · 점 {len(pts)} · {dist:.0f} km · 도보 {hours:.0f}시간')
    return pts, dist, hours
