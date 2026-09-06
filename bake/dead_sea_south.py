"""사해 남부 분지를 하나의 매끈한 수역으로 만든다.

OSM 은 이 일대의 칼륨 증발지를 보통 호수(class=lake)로 태깅해 보내고, 그래서
지도에는 자로 그은 듯한 직사각형과 그 사이의 제방이 그대로 드러난다. 1930년에
시작된 공장 시설이 성경 지도에서 고대의 자연 호수처럼 읽히는 셈이다.

증발지 폴리곤들을 격자에 찍고 → 팽창·수축(모폴로지 닫힘)으로 제방 틈을 메운 뒤
→ 경계를 따라가 하나의 매끈한 외곽선을 뽑는다. 물을 지우지 않는 이유는, 고대의
남부 분지가 리산 반도 남쪽의 얕은 석호였고 그 넓이가 지금 증발지와 얼추 비슷하기
때문이다. 없애면 오히려 성경 시대와 멀어진다.

입력:  querySourceFeatures 로 받아 둔 물 폴리곤 목록(JSON)
출력:  data/dead-sea-south.geojson
"""
import json, math, pathlib, sys
import numpy as np

# 남부 분지(리산 반도 남쪽)만 다룬다. 북쪽 본 호수와 서쪽 아라바의 작은 못은 건드리지 않는다.
BOX = (35.33, 30.92, 35.58, 31.34)      # lon0, lat0, lon1, lat1
CELL = 0.0004                            # 약 40 m
CLOSE = 9                                # 팽창·수축 반경(셀). 제방 폭보다 넉넉해야 메워진다.


def rings(geom):
    if geom['type'] == 'Polygon':
        return geom['coordinates']
    if geom['type'] == 'MultiPolygon':
        return [r for poly in geom['coordinates'] for r in poly]
    return []


def rasterize(polys, nx, ny):
    """스캔라인 채우기. 외곽 고리와 구멍을 짝수·홀수 규칙으로 함께 처리한다."""
    grid = np.zeros((ny, nx), dtype=bool)
    edges = []
    for ring in polys:
        for i in range(len(ring) - 1):
            (x1, y1), (x2, y2) = ring[i][:2], ring[i + 1][:2]
            if y1 != y2:
                edges.append((x1, y1, x2, y2))
    if not edges:
        return grid
    e = np.array(edges)
    for j in range(ny):
        y = BOX[1] + (j + 0.5) * CELL
        hit = ((e[:, 1] > y) != (e[:, 3] > y))
        if not hit.any():
            continue
        s = e[hit]
        xs = s[:, 0] + (y - s[:, 1]) * (s[:, 2] - s[:, 0]) / (s[:, 3] - s[:, 1])
        xs = np.sort(xs)
        for a, b in zip(xs[0::2], xs[1::2]):
            i0 = max(0, int((a - BOX[0]) / CELL))
            i1 = min(nx, int(math.ceil((b - BOX[0]) / CELL)))
            if i1 > i0:
                grid[j, i0:i1] = True
    return grid


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def morph(grid, se, dilate):
    """순수 numpy 팽창/수축. 구조요소의 True 위치마다 격자를 밀어 겹친다."""
    r = se.shape[0] // 2
    pad = np.pad(grid if dilate else ~grid, r, constant_values=False)
    out = np.zeros_like(pad)
    for dy in range(se.shape[0]):
        for dx in range(se.shape[1]):
            if se[dy, dx]:
                out |= np.roll(np.roll(pad, dy - r, axis=0), dx - r, axis=1)
    out = out[r:-r, r:-r]
    return out if dilate else ~out


def components(grid, min_cells=200):
    """이어진 덩어리를 나눈다. 증발지는 서안·동안 무리가 수로로 갈라져 있어서
    가장 큰 덩어리 하나만 따면 한쪽이 통째로 빠진다."""
    ny, nx = grid.shape
    seen = np.zeros_like(grid)
    out = []
    for j0 in range(ny):
        for i0 in np.flatnonzero(grid[j0] & ~seen[j0]):
            stack, cells = [(int(i0), j0)], []
            seen[j0, i0] = True
            while stack:
                i, j = stack.pop()
                cells.append((i, j))
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = i + di, j + dj
                    if 0 <= a < nx and 0 <= b < ny and grid[b, a] and not seen[b, a]:
                        seen[b, a] = True
                        stack.append((a, b))
            if len(cells) >= min_cells:
                m = np.zeros_like(grid)
                idx = np.array(cells)
                m[idx[:, 1], idx[:, 0]] = True
                out.append((len(cells), m))
    return sorted(out, key=lambda c: -c[0])


def trace(grid):
    """무어 이웃 추적으로 덩어리의 바깥 경계를 딴다."""
    ny, nx = grid.shape
    start = None
    for j in range(ny):
        row = np.flatnonzero(grid[j])
        if row.size:
            start = (int(row[0]), j)
            break
    if start is None:
        return []
    nbr = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    def on(i, j):
        return 0 <= i < nx and 0 <= j < ny and grid[j, i]
    path, cur, d = [start], start, 6
    for _ in range(4 * nx * ny):
        found = False
        for k in range(8):
            dd = (d + 6 + k) % 8
            ni, nj = cur[0] + nbr[dd][0], cur[1] + nbr[dd][1]
            if on(ni, nj):
                cur, d, found = (ni, nj), dd, True
                path.append(cur)
                break
        if not found or (len(path) > 3 and cur == start):
            break
    return path


def smooth(pts, passes=6):
    for _ in range(passes):
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            out.append([(pts[i - 1][k] + 2 * pts[i][k] + pts[i + 1][k]) / 4 for k in (0, 1)])
        out.append(pts[-1])
        pts = out
    return pts


def main(src):
    feats = json.load(open(src, encoding='utf-8'))
    polys = []
    for f in feats:
        for ring in rings(f['g']):
            xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
            if (max(xs) < BOX[0] or min(xs) > BOX[2] or max(ys) < BOX[1] or min(ys) > BOX[3]):
                continue
            polys.append(ring if ring[0] == ring[-1] else ring + [ring[0]])
    nx = int((BOX[2] - BOX[0]) / CELL)
    ny = int((BOX[3] - BOX[1]) / CELL)
    grid = rasterize(polys, nx, ny)
    print(f'폴리곤 {len(polys)}개 · 격자 {nx}×{ny} · 물 셀 {int(grid.sum()):,}')
    se = disk(CLOSE)
    closed = morph(morph(grid, se, True), se, False)
    print(f'제방을 메운 뒤 물 셀 {int(closed.sum()):,} (+{int(closed.sum()-grid.sum()):,})')
    polys_out = []
    for n, comp in components(closed):
        path = trace(comp)
        if len(path) < 30:
            continue
        ring = smooth([[BOX[0] + (i + 0.5) * CELL, BOX[1] + (j + 0.5) * CELL]
                       for i, j in path[::3]])
        ring = [[round(x, 5), round(y, 5)] for x, y in ring]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        polys_out.append([ring])
        print(f'  덩어리 {n:,} 셀 → 외곽선 {len(ring)}점')
    out = {'type': 'FeatureCollection', 'features': [{
        'type': 'Feature', 'id': 'ds-south',
        'properties': {'ko': '사해 남부 분지',
                       'note': '오늘날은 칼륨·브롬 증발지. 제방선을 지우고 하나의 수역으로 그린다.'},
        'geometry': {'type': 'MultiPolygon', 'coordinates': polys_out}}]}
    p = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'dead-sea-south.geojson'
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'수역 {len(polys_out)}개 → {p.name}')


if __name__ == '__main__':
    main(sys.argv[1])
