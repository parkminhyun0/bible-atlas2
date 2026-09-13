"""1세기(예수 당시) 예루살렘 — 성읍의 규모 · 헤롯 성전 자리 · 성문.

성벽 복원도가 아니다. **성읍이 얼마나 컸는지**를 지도 위에 보이려는 것이다.

세 가지를 낸다.
  1) 성읍 둘레와 그 안의 면 (넓이·둘레·남북·동서를 잰다)
  2) 헤롯 성전의 성전 산 대지 (다른 색으로 따로)
  3) 1세기 성문 (도면처럼 벽에 낸 구멍으로 그린다)

── 좌표를 어디서 가져왔나 ──
사용자가 준 개설도는 성벽이 **어디를 지나는지**(무엇이 안이고 무엇이 밖인지)를 정하는
데만 썼다. 그림을 못 네 곳으로 지리좌표에 맞춰 보니 기준점 잔차가 최대 111 m 였다 —
측량도가 아니라 개설도다. 그 왜곡을 옮길 이유가 없다.

꼭짓점은 되도록 **발굴된 유구**에 건다.
  · 성전 산 남벽 — 로빈슨 아치·훌다 이중문·훌다 삼중문·단일문 네 발굴 지점에 직선을
    회귀시켰다(잔차 0.9~6.4 m). 거기에 실측 치수(남 281·동 466·서 485 m)를 얹어 네
    모서리를 냈다.  [Baruch·Reich·Hagbi·Uziel, 『성전 산 남벽』, IAA 2022]
  · 남쪽 둘레 — 모즐리 스카프(개신교 묘지)에서 시온산 남쪽을 지나 실로암 못 **아래로**.
    Bliss 와 Dickie 가 1894~97년에 실제로 파서 따라간 선이다.
  · 동쪽 — 워런 수직갱·계단식 석조 구조물·오벨.   · 서쪽 — 다윗 탑·키슐레 발굴.

**실로암 못은 성 안이다.** 처음에 못을 경계선 위에 두었던 것은 틀렸다. 같은 보고서가
못 남쪽에서 성문을 파냈고("City Gate south of Pool of Siloam"), 본문은 "성벽선이 실로암
못을 성 안에 포함한다"고 못박는다. 테오도시우스(530년경)도 "실로암 못은 성벽 안에
있다"고 했고, 요세푸스는 성벽이 실로암 못 위쪽에서 꺾였다고 한다.

── 지형에 맞추기 ──
성벽은 골짜기 위 마루를 따라갔다. 그래서 발굴로 고정되지 않은 꼭짓점만 DEM(약 4 m/px)
으로 훑어 **사면이 꺾이는 자리**로 옮긴다. 다만 아무 데나 옮기지 않는다.
  · 어느 벽면을 어느 쪽으로 훑을지 벽면마다 지정한다(서쪽 사면은 서쪽으로, 동쪽은 동쪽).
  · **남단은 옮기지 않는다.** 그곳에서 성벽은 마루를 따르지 않고 못을 감싸려 내려갔다.
    실제로 마루로 끌어 보니 실로암 못이 다시 성 밖으로 밀려났다.
  · 옮긴 뒤 고고 검증(아래 CHECKS)을 다시 돌려, 통과하지 못하면 물러선다.

출력: data/jerusalem-c1.geojson
"""
import json, math, pathlib, pickle, subprocess, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'jerusalem-c1.geojson'
DEM_DIR = pathlib.Path('/tmp/jeru-dem')
Z = 15
KX = 111320 * math.cos(math.radians(31.776))
KY = 110540

# (경도, 위도, 무엇, 근거, 지형맞춤)  — 시계 방향.
#   지형맞춤: None = 옮기지 않음 / (방위각) = 그 방향으로 사면을 훑어 마루로 옮김
RING = [
    (35.22808, 31.77607, '다윗 탑 (헤롯기 탑 기초)',        '발굴',  None),
    (35.22799, 31.77516, '키슐레 발굴 (헤롯 궁전 기초)',     '발굴',  None),
    (35.22847, 31.77032, '모즐리 스카프 (개신교 묘지)',      '발굴',  None),
    (35.22960, 31.76991, '시온산 남쪽 발굴',                '발굴',  None),
    (35.23057, 31.77037, '티로포에온 골짜기를 건너는 구간',   '추정',  180),   # 남쪽 사면
    (35.23380, 31.76960, '실로암 못 남쪽 성문 부근',         '추정',  None),  # 못을 감싼다 — 고정
    (35.23560, 31.76980, '성읍 남단 (기드론·힌놈 합류부)',    '추정',  None),  # 고정
    (35.23641, 31.77310, '워런 수직갱',                    '발굴',  None),
    (35.23680, 31.77450, '기드론 위 능선',                  '추정',  90),    # 동쪽 사면
    (35.23656, 31.77570, '오벨',                          '발굴',  None),
    (35.23742, 31.77606, '성전 산 남동 모서리',             '발굴',  None),
    (35.23730, 31.78026, '성전 산 북동 모서리',             '발굴',  None),
    (35.23397, 31.78015, '성전 산 북서 (안토니아 요새)',     '발굴',  None),
    (35.23200, 31.77950, '제2성벽 북',                     '불확실', None),
    (35.23010, 31.77800, '제2성벽 북서',                   '불확실', None),
    (35.22870, 31.77780, '제2성벽 서',                     '불확실', None),
    (35.22880, 31.77650, '겐나트 문 부근',                  '불확실', None),
]

# 헤롯 성전의 성전 산 대지. 남벽 회귀 + 실측 치수로 낸 네 모서리.
TEMPLE = [(35.23446, 31.77581), (35.23742, 31.77606), (35.23730, 31.78026), (35.23397, 31.78015)]

# ── 성전 산은 한 번에 이 크기가 아니었다 ──
# 세 시대를 함께 그려 크기를 견주게 한다. 근거의 성격이 시대마다 다르므로 그것도 적는다.
#
# 치수는 이 프로젝트의 성전 연구 묶음(Temple in Jerusalem/temple_spec.json · 02_치수표.md)을
# 따른다. 그 묶음이 세운 기준:
#   · 규빗 0.525 m (리트마이어의 왕실 규빗). 앞서 0.45·0.5 를 섞어 쓴 것은 틀렸다.
#   · 옛 성전 산 정방형 500×500 규빗 = 262.5 m  [Middot 2:1 · 리트마이어 실측 861 ft, 등급 A]
#   · 그 정방형은 헤롯 외벽에 대해 4.2° 틀어져 있다 — 정방형 축은 거의 정동서로 달린다
#   · 헤롯 서벽과 정방형 서변 사이 약 25 m
#   · 헤롯 외벽 서 485 · 동 470 · 북 315 · 남 280 m  [Warren/Ritmeyer 실측]
#
#  헤롯 (서기 1세기)  — 발굴. 남벽 네 지점 회귀 + 위 실측 치수. 약 14 ha
#  스룹바벨~하스몬    — 문헌 + 발굴 앵커. 500규빗 정방형을 동벽 이음매에 건다.
#  솔로몬 (제1성전)   — 경내 크기는 남아 있지 않다. 성경이 건물 치수를 정확히 말하므로
#                      (왕상 6:2-3) 솔로몬만은 경내가 아니라 '건물'을 그린다. 자리는
#                      바위 돔 아래 반석을 지성소로 보는 리트마이어 안을 따른다.
CUBIT = 0.525                     # 왕실 규빗. 연구 묶음의 기준값 하나로 통일한다.
SQUARE_CUBITS = 500               # Middot 2:1
SQUARE_SKEW_DEG = -4.2            # 헤롯 외벽 기준. 음수라야 정방형 축이 정동서에 가깝다.
SQUARE_WEST_OFFSET_SPEC = 25.0    # 헤롯 서벽과 정방형 서변 사이 (명세값, 검산에 쓴다)
HEROD_WALLS = {'south': 280.0, 'east': 470.0, 'north': 315.0, 'west': 485.0}

# ── 베데스다 못 ──
# 요 5:2 "예루살렘에 있는 양문 곁에 히브리 말로 베데스다라 하는 못이 있는데 거기 행각
# 다섯이 있고". 성 안나 교회 곁의 쌍못이다. 북쪽 못이 먼저(기원전 700년대 댐으로 샘을
# 저수지로 바꾼 것), 남쪽 못은 하스몬기 증축. 둘 사이의 둑이 다섯째 행각 자리로 읽힌다.
# 1888년 K. Schick 이 드러냈고 비잔틴 교회가 그 위에 섰다.
#
# 다른 이름의 '쌍못'과 헷갈리지 않아야 한다. Warren·Wilson 의 『Recovery of Jerusalem』이
# 말하는 "성전 산 북서 모서리의 쌍못"(길이 165 ft · 폭 48 ft)은 안토니아 곁의 스트루티온
# 못으로, 여기가 아니다. 에우세비우스 시대의 전승지를 논하는 대목이다.
#
# 폴리곤은 OSM 의 발굴 구역(Wikidata Q831297). 오늘 파내어 보이는 만큼이고, 옛 복합은
# 뒷날의 교회와 수도원 부지 아래로 더 뻗는다 — 팝업에 그렇게 적는다.
BETHESDA_RING = [[35.23565, 31.78124], [35.23559, 31.78127], [35.23558, 31.7813], [35.23556, 31.78138], [35.23555, 31.7814], [35.23558, 31.78146], [35.23558, 31.7815], [35.2356, 31.7815], [35.23564, 31.78151], [35.23564, 31.78152], [35.23564, 31.78156], [35.23564, 31.78159], [35.23565, 31.7816], [35.23568, 31.78161], [35.23592, 31.78165], [35.23593, 31.78166], [35.23593, 31.78167], [35.23592, 31.78169], [35.23599, 31.7817], [35.23603, 31.78171], [35.23606, 31.78169], [35.23608, 31.78168], [35.23611, 31.78169], [35.23614, 31.78168], [35.23619, 31.78167], [35.23628, 31.78167], [35.23634, 31.78168], [35.23643, 31.78149], [35.23574, 31.78127], [35.23565, 31.78124]]
BETHESDA_CENTER = [35.23597, 31.78151]

SEAM = (35.23758, 31.77635)          # 동벽 이음매 (발굴)
ROCK = (35.23542, 31.77802)          # 바위 돔 아래 반석 (에스사흐라)
FIRST_TEMPLE_MASONRY = (35.23752, 31.77683)   # 동벽의 제1성전기 석조 (발굴)
HERODIAN_NORTH_EXT = (35.23719, 31.77959)     # 동벽의 헤롯기 북쪽 확장부 (발굴)

# 1세기 성문. bearing 은 그 문이 뚫린 벽의 방위각(도면 기호를 벽과 나란히 눕히려고 쓴다).
# wall: 이 문이 뚫린 벽. 성전 산의 문과 성읍의 문은 다른 벽에 난 문이다 —
# 구별해 주지 않으면 성전 산 문들이 '성읍 경계 안에 떠 있는' 것처럼 보인다.
GATES = [
    ('훌다 이중문',   35.23588, 31.77584,  84, '발굴', '성전 산 남벽. 순례자가 정결례를 마치고 올라온 주 출입구다.', '성전 산'),
    ('훌다 삼중문',   35.23658, 31.77595,  84, '발굴', '성전 산 남벽의 동쪽 문.', '성전 산'),
    ('로빈슨 아치',   35.23459, 31.77582, 354, '발굴', '성전 산 남서 모서리에 걸린 계단. 아래 저잣거리에서 왕의 주랑으로 올라갔다.', '성전 산'),
    ('바클레이 문',   35.23451, 31.77638, 354, '발굴', '성전 산 서벽의 헤롯기 문. 지금은 무그라비 문 아래에 묻혀 있다.', '성전 산'),
    ('윌슨 아치',     35.23432, 31.77707, 354, '발굴', '윗성에서 성전 산으로 건너오던 다리.', '성전 산'),
    ('워런 문',       35.23430, 31.77790, 354, '추정', '성전 산 서벽 북쪽의 헤롯기 문. 지금은 막혀 있다.', '성전 산'),
    ('실로암 문',     35.23380, 31.76960,  95, '발굴', 'Bliss 와 Dickie 가 실로암 못 남쪽에서 파낸 성문.', '성읍'),
    ('에센 문',       35.22890, 31.77010, 175, '발굴', '시온산 남서쪽. 요세푸스가 이름을 남긴 문이고 발굴로 확인되었다.', '성읍'),
    ('겐나트 문',     35.22880, 31.77650,  95, '불확실', '요세푸스가 제2성벽이 여기서 갈라졌다고 한 문. 자리는 확정되지 않았다.', '성읍'),
]

# 경계가 맞는지 재는 시금석. 여유 거리까지 본다 — 아슬아슬하게 걸치면 맞다고 할 수 없다.
CHECKS = [
    ('성묘 교회 (골고다)', 35.22972, 31.77833, '밖', 20),
    ('베데스다 못',        35.23599, 31.78147, '밖', 20),
    ('다메섹 문',          35.23018, 31.78182, '밖', 20),
    ('기혼 샘',            35.23683, 31.77323, '밖', 10),
    ('실로암 못',          35.23512, 31.77040, '안', 30),
    ('계단식 석조 구조물',  35.23590, 31.77377, '안', 20),
    ('브로드 월',          35.23165, 31.77594, '안', 20),
    ('히스기야 못',        35.22902, 31.77718, '안', 20),
    ('로빈슨 아치',        35.23459, 31.77582, '안', 5),
    ('기바티 주차장 발굴',  35.23510, 31.77444, '안', 20),
    ('다윗 성',            35.23572, 31.77242, '안', 20),
    ('윌슨 아치',          35.23432, 31.77707, '안', 20),
    ('헤롯 극장터',        35.23370, 31.77236, '안', 20),
]


# ---------- 지형 ----------
def tile_xy(lon, lat):
    r = math.radians(lat)
    return (int((lon + 180) / 360 * 2 ** Z),
            int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** Z))


def load_dem():
    """AWS terrarium 타일(약 4 m/px). 이 환경은 urllib https 가 막혀 curl 로 받는다."""
    from PIL import Image
    DEM_DIR.mkdir(parents=True, exist_ok=True)
    x0, y1 = tile_xy(35.2180, 31.7620)
    x1, y0 = tile_xy(35.2470, 31.7880)
    W = (x1 - x0 + 1) * 256
    H = (y1 - y0 + 1) * 256
    grid = [[0.0] * W for _ in range(H)]
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            f = DEM_DIR / ('%d_%d_%d.png' % (Z, tx, ty))
            if not f.exists() or f.stat().st_size < 1000:
                u = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png' % (Z, tx, ty)
                subprocess.run(['curl', '-s', '--max-time', '90', u, '-o', str(f)])
            im = Image.open(f).convert('RGB')
            px = im.load()
            ox, oy = (tx - x0) * 256, (ty - y0) * 256
            for j in range(256):
                row = grid[oy + j]
                for i in range(256):
                    r, g, b = px[i, j]
                    row[ox + i] = (r * 256 + g + b / 256) - 32768
    return {'grid': grid, 'W': W, 'H': H, 'ox': x0 * 256, 'oy': y0 * 256}


def elev(dem, lon, lat):
    n = 2 ** Z * 256
    r = math.radians(lat)
    x = (lon + 180) / 360 * n - dem['ox']
    y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n - dem['oy']
    xi, yi = int(x), int(y)
    if not (0 <= xi < dem['W'] - 1 and 0 <= yi < dem['H'] - 1):
        return None
    fx, fy = x - xi, y - yi
    g = dem['grid']
    a, b, c, d = g[yi][xi], g[yi][xi + 1], g[yi + 1][xi], g[yi + 1][xi + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def crest_offset(dem, lon, lat, bearing, rng=90, step=4):
    """주어진 방위로 ±rng m 훑어 사면이 꺾이는 자리(마루)까지의 거리를 낸다."""
    nx = math.sin(math.radians(bearing))
    ny = math.cos(math.radians(bearing))
    ts, es = [], []
    t = -rng
    while t <= rng:
        e = elev(dem, lon + nx * t / KX, lat + ny * t / KY)
        if e is None:
            return None, nx, ny
        ts.append(t); es.append(e); t += step
    best = bi = None
    for i in range(2, len(es) - 2):
        d2 = es[i - 2] - 2 * es[i] + es[i + 2]
        if best is None or d2 < best:
            best, bi = d2, i
    return ts[bi], nx, ny


# ---------- 기하 ----------
def inside(pt, ring):
    x, y = pt
    c = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            c = not c
    return c


def dist_to_ring(pt, ring):
    x, y = pt
    best = 1e18
    n = len(ring)
    for i in range(n):
        ax, ay = ring[i][0], ring[i][1]
        bx, by = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        px, py = (x - ax) * KX, (y - ay) * KY
        vx, vy = (bx - ax) * KX, (by - ay) * KY
        L = vx * vx + vy * vy
        t = 0 if L == 0 else max(0, min(1, (px * vx + py * vy) / L))
        best = min(best, math.hypot(px - t * vx, py - t * vy))
    return best


def check(ring):
    bad = []
    for name, lo, la, want, margin in CHECKS:
        got = '안' if inside((lo, la), ring) else '밖'
        d = dist_to_ring((lo, la), ring)
        if got != want:
            bad.append('%s: %s (기대 %s)' % (name, got, want))
        elif d < margin:
            bad.append('%s: %s 이지만 경계에서 %.0f m 뿐 (최소 %d m)' % (name, got, d, margin))
    return bad


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


def perim_m(ring):
    t = 0.0
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        la = math.radians((a[1] + b[1]) / 2)
        t += math.hypot((b[0] - a[0]) * 111320 * math.cos(la), (b[1] - a[1]) * 110540)
    return t


def temple_frame():
    """성전 산의 지역 좌표계. 남벽을 x축(u), 그 수직을 y축(n)으로 삼는다.

    TEMPLE 네 모서리에서 바로 뽑는다 — 남벽 발굴 네 지점에 회귀시켜 만든 것이므로
    그 방향이 곧 성전 산의 방향이다.
    """
    sw, se = TEMPLE[0], TEMPLE[1]
    ux = (se[0] - sw[0]) * KX
    uy = (se[1] - sw[1]) * KY
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    return (ux, uy), (-uy, ux)          # u(동쪽), n(북쪽)


def offset(pt, u, n, du, dn):
    """지역 좌표계에서 du(동) · dn(북) 미터만큼 옮긴 경위도."""
    return [round(pt[0] + (u[0] * du + n[0] * dn) / KX, 5),
            round(pt[1] + (u[1] * du + n[1] * dn) / KY, 5)]


def build_temples():
    """500규빗 정방형과 솔로몬 성전 건물을 만든다.

    정방형은 헤롯 외벽과 나란하지 않다. 연구 묶음이 4.2° 스큐를 적는데, 음수 쪽으로
    돌려야 정방형 축이 거의 정동서가 된다(헤롯 남벽은 정동에서 북으로 5.6° 기울어 있다).
    양수 쪽으로 돌리면 정방형이 헤롯 대지 밖으로 나가 버린다 — 실제로 그렇게 나왔다.
    """
    u, n = temple_frame()
    side = SQUARE_CUBITS * CUBIT

    a = math.radians(SQUARE_SKEW_DEG)
    ca, sa = math.cos(a), math.sin(a)
    au = (u[0] * ca - u[1] * sa, u[1] * ca + u[0] * sa)     # 정방형의 동
    an = (-au[1], au[0])                                     # 정방형의 북

    # 남동 모서리 = 이음매를 헤롯 동벽 위로 내린 점.
    hse = TEMPLE[1]
    dn = ((SEAM[0] - hse[0]) * KX * n[0] + (SEAM[1] - hse[1]) * KY * n[1])
    se_m = ((hse[0] - TEMPLE[0][0]) * KX + n[0] * dn, (hse[1] - TEMPLE[0][1]) * KY + n[1] * dn)

    def to_ll(mx, my):
        return [round(TEMPLE[0][0] + mx / KX, 5), round(TEMPLE[0][1] + my / KY, 5)]

    pts = [se_m,
           (se_m[0] + side * an[0], se_m[1] + side * an[1]),                      # 북동
           (se_m[0] + side * an[0] - side * au[0], se_m[1] + side * an[1] - side * au[1]),  # 북서
           (se_m[0] - side * au[0], se_m[1] - side * au[1])]                      # 남서
    pre = [to_ll(*q) for q in pts]

    # 솔로몬 성전 건물. 왕상 6:2 본체 60×20 규빗, 6:3 현관 깊이 10 규빗 → 70×20.
    # 축은 헤롯 외벽이 아니라 '정방형'을 따른다 — 성전은 그 경내의 건물이다.
    rock_m = ((ROCK[0] - TEMPLE[0][0]) * KX, (ROCK[1] - TEMPLE[0][1]) * KY)
    half_w = 10 * CUBIT
    west, east = -10 * CUBIT, 60 * CUBIT
    sol = [to_ll(rock_m[0] + au[0] * west + an[0] * -half_w, rock_m[1] + au[1] * west + an[1] * -half_w),
           to_ll(rock_m[0] + au[0] * east + an[0] * -half_w, rock_m[1] + au[1] * east + an[1] * -half_w),
           to_ll(rock_m[0] + au[0] * east + an[0] *  half_w, rock_m[1] + au[1] * east + an[1] *  half_w),
           to_ll(rock_m[0] + au[0] * west + an[0] *  half_w, rock_m[1] + au[1] * west + an[1] *  half_w)]

    # 헤롯 성소 '건물'. 솔로몬 건물과 견주려고 같이 낸다 — 크기를 물으신 뜻이
    # 건물끼리 견주는 것이기 때문이다. 연구 묶음 02_치수표: 정면 100×100 규빗,
    # 동서 총장 100 규빗 (Middot 4:6-7 · War 5.207, 등급 A).
    # 솔로몬과 같은 기준으로 건다 — 지성소가 서쪽 끝이고 그 한가운데가 반석이다.
    # 반석에 '한가운데'를 맞추면 지성소가 반석에서 50규빗 서쪽으로 밀려난다.
    hw = 50 * CUBIT                       # 정면 폭 100규빗의 절반
    hwest, heast = -10 * CUBIT, 90 * CUBIT
    her = [to_ll(rock_m[0] + au[0] * hwest + an[0] * -hw, rock_m[1] + au[1] * hwest + an[1] * -hw),
           to_ll(rock_m[0] + au[0] * heast + an[0] * -hw, rock_m[1] + au[1] * heast + an[1] * -hw),
           to_ll(rock_m[0] + au[0] * heast + an[0] *  hw, rock_m[1] + au[1] * heast + an[1] *  hw),
           to_ll(rock_m[0] + au[0] * hwest + an[0] *  hw, rock_m[1] + au[1] * hwest + an[1] *  hw)]

    # 검산에 쓸 값: 정방형 서변이 헤롯 서벽에서 얼마나 떨어졌나
    def seg_dist(px, py, ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - ax - t * vx, py - ay - t * vy)
    sw_m = (0.0, 0.0)
    nw_m = ((TEMPLE[3][0] - TEMPLE[0][0]) * KX, (TEMPLE[3][1] - TEMPLE[0][1]) * KY)
    west_off = min(seg_dist(pts[3][0], pts[3][1], sw_m[0], sw_m[1], nw_m[0], nw_m[1]),
                   seg_dist(pts[2][0], pts[2][1], sw_m[0], sw_m[1], nw_m[0], nw_m[1]))
    return pre, sol, her, side, (70 * CUBIT, 20 * CUBIT), (100 * CUBIT, 100 * CUBIT), west_off, dn


def main():
    dem = load_dem()
    print('DEM 준비 — 바위 돔 %.0f m · 실로암 못 %.0f m · 시온산 %.0f m'
          % (elev(dem, 35.23542, 31.77802), elev(dem, 35.23512, 31.77040), elev(dem, 35.22866, 31.77162)))

    ring = [[p[0], p[1], p[2], p[3]] for p in RING]
    bad = check(ring)
    if bad:
        raise SystemExit('지형 맞춤 전부터 검증 실패 — ' + ' / '.join(bad))

    print('\n지형 맞춤:')
    for i, (lo, la, name, cert, fit) in enumerate(RING):
        if fit is None:
            continue
        t, nx, ny = crest_offset(dem, lo, la, fit)
        if t is None:
            print('  %-24s DEM 없음' % name)
            continue
        moved = False
        for k in range(10, -1, -1):           # 마루에서 시작해 원위치까지 물러난다
            tt = t * k / 10
            cand = [lo + nx * tt / KX, la + ny * tt / KY, name, cert]
            trial = [r[:] for r in ring]
            trial[i] = cand
            if not check(trial):
                ring[i] = [round(cand[0], 5), round(cand[1], 5), name, cert]
                print('  %-24s %+5.0f m · 고도 %.0f m%s'
                      % (name, tt, elev(dem, cand[0], cand[1]),
                         '' if abs(tt - t) < 1 else ' (고고 검증에 막혀 물러섬)'))
                moved = True
                break
        if not moved:
            print('  %-24s 옮기지 못함 (고고 검증)' % name)

    bad = check(ring)
    if bad:
        raise SystemExit('지형 맞춤 뒤 검증 실패 — ' + ' / '.join(bad))
    print('\n고고 검증 %d/%d 통과 (여유 거리 포함)' % (len(CHECKS), len(CHECKS)))

    ha = area_ha(ring)
    per = perim_m(ring)
    lats = [p[1] for p in ring]
    lons = [p[0] for p in ring]
    la0 = sum(lats) / len(lats)
    ns = (max(lats) - min(lats)) * 110540
    ew = (max(lons) - min(lons)) * 111320 * math.cos(math.radians(la0))
    tha = area_ha([[p[0], p[1]] for p in TEMPLE])

    feats = [{
        'type': 'Feature',
        'properties': {'kind': 'extent', 'ko': '예수 당시 예루살렘 성읍',
                       'ha': round(ha, 1), 'km2': round(ha / 100, 3),
                       'perimeter_km': round(per / 1000, 2),
                       'ns_m': round(ns), 'ew_m': round(ew),
                       'temple_ha': round(tha, 1),
                       'temple_pct': round(100 * tha / ha, 1),
                       'dug': sum(1 for p in RING if p[3] == '발굴'),
                       'guess': sum(1 for p in RING if p[3] == '추정'),
                       'unsure': sum(1 for p in RING if p[3] == '불확실')},
        'geometry': {'type': 'Polygon',
                     'coordinates': [[[p[0], p[1]] for p in ring] + [[ring[0][0], ring[0][1]]]]},
    }, {
        'type': 'Feature',
        'properties': {'kind': 'temple', 'ko': '헤롯 성전 (성전 산 대지)',
                       'ha': round(tha, 1),
                       's_m': round(math.hypot((TEMPLE[1][0]-TEMPLE[0][0])*KX, (TEMPLE[1][1]-TEMPLE[0][1])*KY)),
                       'e_m': round(math.hypot((TEMPLE[2][0]-TEMPLE[1][0])*KX, (TEMPLE[2][1]-TEMPLE[1][1])*KY)),
                       'n_m': round(math.hypot((TEMPLE[3][0]-TEMPLE[2][0])*KX, (TEMPLE[3][1]-TEMPLE[2][1])*KY)),
                       'w_m': round(math.hypot((TEMPLE[0][0]-TEMPLE[3][0])*KX, (TEMPLE[0][1]-TEMPLE[3][1])*KY))},
        'geometry': {'type': 'Polygon', 'coordinates': [TEMPLE + [TEMPLE[0]]]},
    }]

    # ── 성전 산의 세 시대 ──
    pre, sol, her, pre_side, sol_size, her_size, west_off, seam_dn = build_temples()
    pre_ha = area_ha([[q[0], q[1]] for q in pre])
    sol_ha = area_ha([[q[0], q[1]] for q in sol])

    # 검산. 발굴 지점들이 이 복원과 어긋나지 않아야 한다.
    if not inside((FIRST_TEMPLE_MASONRY[0], FIRST_TEMPLE_MASONRY[1]), [[q[0], q[1]] for q in pre]) \
       and dist_to_ring((FIRST_TEMPLE_MASONRY[0], FIRST_TEMPLE_MASONRY[1]), [[q[0], q[1]] for q in pre]) > 25:
        raise SystemExit('제1성전기 석조가 500규빗 네모의 동벽에서 25 m 넘게 떨어졌다')
    if inside((HERODIAN_NORTH_EXT[0], HERODIAN_NORTH_EXT[1]), [[q[0], q[1]] for q in pre]):
        raise SystemExit('헤롯기 북쪽 확장부가 500규빗 네모 안에 들어갔다 — 확장이 아니게 된다')
    for nm2, q in zip(['남동', '북동', '북서', '남서'], pre):
        if not inside((q[0], q[1]), [[t[0], t[1]] for t in TEMPLE]):
            raise SystemExit('500규빗 네모의 %s 모서리가 헤롯 대지 밖이다' % nm2)
    if abs(west_off - SQUARE_WEST_OFFSET_SPEC) > 12:
        raise SystemExit('정방형 서변~헤롯 서벽 %.0f m — 명세 %.0f m 와 12 m 넘게 어긋난다'
                         % (west_off, SQUARE_WEST_OFFSET_SPEC))
    print('  정방형 서변~헤롯 서벽 %.0f m (명세 %.0f m) · 이음매는 남동에서 북으로 %.0f m'
          % (west_off, SQUARE_WEST_OFFSET_SPEC, seam_dn))
    print('성전 시대 검산 통과 — 제1성전기 석조가 동벽에 붙고, 헤롯기 북쪽 확장부는 네모 밖이다')

    feats.append({'type': 'Feature',
                  'properties': {'kind': 'temple2', 'ko': '스룹바벨~하스몬기 성전 산',
                                 'ha': round(pre_ha, 1), 'side_m': round(pre_side),
                                 'cubit': CUBIT, 'skew': SQUARE_SKEW_DEG,
                                 'west_off_m': round(west_off),
                                 'cert': '문헌 + 발굴 앵커'},
                  'geometry': {'type': 'Polygon', 'coordinates': [pre + [pre[0]]]}})
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'sanctuary', 'ko': '헤롯 성소 (건물)',
                                 'len_m': round(her_size[0], 1), 'wid_m': round(her_size[1], 1),
                                 'cubit': CUBIT, 'cert': '문헌 치수 + 추정 위치',
                                 'vs_solomon': round((her_size[0] * her_size[1]) /
                                                     (sol_size[0] * sol_size[1]), 1)},
                  'geometry': {'type': 'Polygon', 'coordinates': [her + [her[0]]]}})
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'temple1', 'ko': '솔로몬 성전 (건물)',
                                 'ha': round(sol_ha, 3),
                                 'len_m': round(sol_size[0], 1), 'wid_m': round(sol_size[1], 1),
                                 'cubit': CUBIT, 'cert': '성경 치수 + 추정 위치'},
                  'geometry': {'type': 'Polygon', 'coordinates': [sol + [sol[0]]]}})

    for lo, la, name, cert, _ in RING:
        i = [r[2] for r in ring].index(name)
        feats.append({'type': 'Feature',
                      'properties': {'kind': 'anchor', 'ko': name, 'cert': cert},
                      'geometry': {'type': 'Point', 'coordinates': [ring[i][0], ring[i][1]]}})

    for name, lo, la, brg, cert, desc, wall in GATES:
        feats.append({'type': 'Feature',
                      'properties': {'kind': 'gate', 'ko': name, 'cert': cert,
                                     'bearing': brg, 'desc': desc, 'wall': wall},
                      'geometry': {'type': 'Point', 'coordinates': [lo, la]}})

    # 면에 라벨을 붙이면 그 면이 걸친 타일마다 한 번씩 찍혀 글자가 겹친다(실제로 세 번씩
    # 나왔다). 라벨은 면의 한가운데에 점 하나를 따로 내어 거기에 붙인다.
    def centroid(poly):
        xs = [q[0] for q in poly[:-1]] if poly[0] == poly[-1] else [q[0] for q in poly]
        ys = [q[1] for q in poly[:-1]] if poly[0] == poly[-1] else [q[1] for q in poly]
        return [round(sum(xs) / len(xs), 5), round(sum(ys) / len(ys), 5)]
    for kind, poly in [('temple', TEMPLE), ('temple2', pre), ('temple1', sol), ('sanctuary', her)]:
        feats.append({'type': 'Feature',
                      'properties': {'kind': kind, 'label_only': True},
                      'geometry': {'type': 'Point', 'coordinates': centroid(list(poly))}})

    # ── 베데스다 못 ──
    bring = [list(q) for q in BETHESDA_RING]
    if bring[0] != bring[-1]:
        bring.append(list(bring[0]))
    b_ha = area_ha([[q[0], q[1]] for q in bring])
    bxs = [q[0] for q in bring]
    bys = [q[1] for q in bring]
    b_ew = (max(bxs) - min(bxs)) * KX
    b_ns = (max(bys) - min(bys)) * KY
    # 성읍 안인가 밖인가. 요한복음은 '양문 곁'이라 하고, 제2성벽 밖 베제타 지구다.
    b_in = sum(1 for q in bring[:-1] if inside((q[0], q[1]), ring))
    b_gap = dist_to_ring((BETHESDA_CENTER[0], BETHESDA_CENTER[1]), ring)
    if b_in:
        raise SystemExit('베데스다 못 꼭짓점 %d 개가 성읍 안으로 들어왔다 — 제2성벽 밖이어야 한다' % b_in)
    print('베데스다 못  %.0f×%.0f m · %.2f ha · 성읍 **밖** · 경계에서 %.0f m'
          % (b_ew, b_ns, b_ha, b_gap))
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'pool', 'ko': '베데스다 못',
                                 'ha': round(b_ha, 2), 'ew_m': round(b_ew), 'ns_m': round(b_ns),
                                 'outside_m': round(b_gap), 'cert': '발굴 구역 (OSM · Wikidata Q831297)'},
                  'geometry': {'type': 'Polygon', 'coordinates': [bring]}})
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'pool', 'label_only': True},
                  'geometry': {'type': 'Point', 'coordinates': list(BETHESDA_CENTER)}})

    unsure = [[p[0], p[1]] for p in ring if p[3] == '불확실']
    i12 = [r[2] for r in ring].index('성전 산 북서 (안토니아 요새)')
    feats.append({'type': 'Feature',
                  'properties': {'kind': 'unsure', 'ko': '제2성벽 (확정된 발굴선 없음)'},
                  'geometry': {'type': 'LineString',
                               'coordinates': [[ring[i12][0], ring[i12][1]]] + unsure +
                                              [[ring[0][0], ring[0][1]]]}})

    fc = {'type': 'FeatureCollection',
          'attribution': '좌표: 발굴 유구 (OpenStreetMap ODbL) · 치수: 성전 산 남벽 실측 · 지형: AWS Terrain Tiles',
          'note': '예수 당시 성읍의 규모. 성벽 복원도가 아니다.',
          'features': feats}
    OUT.write_text(json.dumps(fc, ensure_ascii=False, indent=1), encoding='utf-8')

    print('\n성읍  넓이 %.1f ha (%.3f km²) · 둘레 %.2f km · 남북 %.0f m · 동서 %.0f m'
          % (ha, ha / 100, per / 1000, ns, ew))
    print('성전  %.1f ha (성읍의 %.1f%%) · 남 %d · 동 %d · 북 %d · 서 %d m'
          % (tha, 100 * tha / ha, feats[1]['properties']['s_m'], feats[1]['properties']['e_m'],
             feats[1]['properties']['n_m'], feats[1]['properties']['w_m']))
    print('성전  스룹바벨~하스몬 %.1f ha (%d규빗=%.1f m 네모, 스큐 %.1f°) · 솔로몬 건물 %.2f×%.2f m'
          % (pre_ha, SQUARE_CUBITS, pre_side, SQUARE_SKEW_DEG, sol_size[0], sol_size[1]))
    print('      헤롯 %.1f ha 는 그 %.1f 배다' % (tha, tha / pre_ha))
    print('건물  솔로몬 %.2f×%.2f m · 헤롯 성소 %.1f×%.1f m (바닥 넓이로 %.1f 배)'
          % (sol_size[0], sol_size[1], her_size[0], her_size[1],
             (her_size[0] * her_size[1]) / (sol_size[0] * sol_size[1])))
    print('성문  %d개 (발굴 %d · 추정 %d · 불확실 %d)'
          % (len(GATES), sum(1 for g in GATES if g[4] == '발굴'),
             sum(1 for g in GATES if g[4] == '추정'), sum(1 for g in GATES if g[4] == '불확실')))
    print('%s  %.1f KB' % (OUT, OUT.stat().st_size / 1024))


if __name__ == '__main__':
    main()
