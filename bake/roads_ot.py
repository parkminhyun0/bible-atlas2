#!/usr/bin/env python3
# 구약 시대 주요 도로를 만든다.
#
#   python3 bake/roads_ot.py data/roads-ot.geojson
#
# 신약(서기 30년경) 자료와 근거의 성격이 다르다는 점을 먼저 밝힌다.
#
#   신약 층: Itiner-e 라는 로마 도로 데이터셋의 실제 선형이 있다. 우리는 그 선을
#            서기 30년 기준으로 고르고 지형에 맞춰 다듬었을 뿐이다.
#   구약 층: 철기시대 도로의 선형을 담은 공개 데이터셋은 없다. 도로 유구도 거의
#            남지 않았다. 아는 것은 (1) 성경이 길 이름과 오간 경로를 말한다는 것,
#            (2) 그 길이 지나야 하는 고개·여울·샘이 지형상 정해져 있다는 것,
#            (3) 그 길목마다 성읍이 늘어서 있다는 것, (4) 후대 로마 도로가 같은
#            회랑을 다시 썼다는 것이다.
#
# 그래서 이 자료는 '성경이 말하는 양 끝과 경유지를 잇는, 지형상 가장 걷기 쉬운 길'
# 이다. 확실성은 아무리 높아도 '개연'이며 '확정'은 쓰지 않는다.
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roads_terrain_fit as T

Z = 11                      # 넓은 회랑을 다루므로 z11(약 32 m/px)로 충분하다
STEP_M = 200.0              # 길을 훑는 간격
MAX_OFF_M = 8000.0          # 두 성읍을 잇는 회랑의 반폭
PULL = 0.05                 # 직선으로 당기는 힘. 구약은 원본 선이 없으니 아주 약하게

def use_z(z):
    T.Z = z; T.N = 2 ** z; T._tiles.clear()

def hav(a, b): return T.hav(a, b)

# ---------- 성읍 좌표는 우리 지명 자료에서 가져온다 ----------
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def gazetteer():
    g = {}
    for f in ('ot-places', 'nt-places', 'peaks'):
        for ft in json.load(open(os.path.join(ROOT, 'data', f + '.geojson'), encoding='utf-8'))['features']:
            if ft['geometry']['type'] == 'Point':
                g.setdefault(ft['properties']['ko'], ft['geometry']['coordinates'])
    return g

# 우리 지명 자료에 없는 몇 곳. Pleiades 좌표를 근거로 적어 둔다(경유점일 뿐 지명 자료에 넣지 않는다).
EXTRA = {
    '가데스바네아': ([34.4183, 30.6533], 'Pleiades 746683 (Tell el-Qudeirat)'),
    '아라드':      ([35.1264, 31.2803], 'Pleiades 687826 (Tel Arad)'),
    '아스다롯':    ([36.0058, 32.8256], 'Pleiades 678000 (Tell Ashtarah)'),
    '에드레이':    ([36.1000, 32.6178], 'Pleiades 678123 (Derʿa)'),
    '아루나 고개':  ([35.0200, 32.5000], '와디 아라(나할 이론) — 해변길이 갈멜 산줄기를 넘는 고개'),
    '시스 고개':    ([35.3500, 31.4700], '대하 20:16 ‘시스 고개’ — 유대 광야에서 사해로 내려가는 비탈'),
    '아얄론 골짜기': ([34.9800, 31.8600], '수 10:12 — 벧호론 비탈길이 내려서는 골짜기'),
    '사해 남단':    ([35.4700, 30.9500], '아라바 길이 시작하는 사해 남쪽 끝(지형 지점)'),
}

# ---------- 노선 ----------
# certainty 는 아래 규칙으로 정한다(evidence 에도 적는다).
#   probable     — 양 끝과 경유지가 성경에 분명하고, 지형상 통로가 사실상 하나이며,
#                  후대 로마 도로가 같은 회랑을 다시 쓴 것이 확인되는 노선
#   hypothetical — 그 밖의 노선
#   confirmed    — 쓰지 않는다. 철기시대 도로 유구가 확인된 구간을 확보하지 못했다.
ROADS = [
 {'id': 'ot-coastal', 'nameKo': '해변길 (블레셋 사람의 땅의 길)', 'nameEn': 'Way of the Sea / Way of the Philistines',
  'routeType': 'trunk', 'region': '해안 평야·이스르엘',
  'via': ['가사', '아스글론', '아스돗(아소도)', '욥바', '돌', '아루나 고개', '므깃도', '벧산(스구도볼리)', '하솔', '다메섹'],
  'periodKo': '청동기~철기 (출애굽~왕국 시대 내내)',
  'attestation': ['출 13:17', '사 9:1', '왕하 23:29'],
  'basisKo': '출애굽 때 하나님이 이 길로 인도하지 않으셨다는 기록(출 13:17)에서 이미 이름이 나온다. '
             '애굽과 메소포타미아를 잇는 국제 간선로였고, 갈멜 산줄기를 넘는 아루나 고개와 그 어귀의 므깃도가 '
             '이 길의 목이라 열왕기·역대기의 전투가 거기서 벌어진다.',
  'noteKo': '뒷날 로마가 같은 회랑을 다시 포장했고, 그것을 후대에 ‘Via Maris’라 불렀다. '
            '1세기 공식 도로명이 아니듯 구약 시대 이름도 아니다.'},

 {'id': 'ot-kings-highway', 'nameKo': '왕의 대로', 'nameEn': "King's Highway",
  'routeType': 'trunk', 'region': '요단 동편 고원',
  'via': ['엘랏(엘롯)', '데만', '보스라', '아로엘', '디본', '메드바', '헤스본', '랍바(빌라델비아)', '길르앗', '아스다롯', '다메섹'],
  'periodKo': '청동기~철기 (광야 시대부터)',
  'attestation': ['민 20:17', '민 21:22', '신 2:27'],
  'basisKo': '이스라엘이 에돔 왕과 아모리 왕 시혼에게 “왕의 대로로만 가고 좌우로 치우치지 않겠다”고 청한 그 길이다'
             '(민 20:17; 21:22). 요단 동편 고원의 등줄기를 남북으로 달리며, 아르논 골짜기를 건너는 목이 정해져 있다.',
  'noteKo': '트라야누스가 서기 111~114년에 놓은 Via Nova Traiana 가 이 회랑을 상당 부분 다시 썼다. '
            '그러나 로마 도로의 포장 선형과 구약 시대의 길을 같은 선으로 단정하지는 않는다.'},

 {'id': 'ot-ridge', 'nameKo': '중앙 산지 능선길 (족장의 길)', 'nameEn': 'Central Ridge Route',
  'routeType': 'pilgrimage', 'region': '유다·에브라임 산지',
  'via': ['브엘세바', '헤브론', '베들레헴', '예루살렘', '벧엘', '실로', '세겜', '도단', '이스르엘'],
  'periodKo': '청동기~철기 (족장 시대부터)',
  'attestation': ['창 12:6-9', '창 35:1-7', '삿 21:19', '삼상 1:3'],
  'basisKo': '아브람이 세겜에서 벧엘로, 다시 남방으로 옮겨 간 길이 이 능선이다(창 12:6-9). '
             '분수령을 따르므로 골짜기를 건너지 않아도 되고, 실로·벧엘·세겜 같은 성소가 이 길목에 늘어서 있다.',
  'noteKo': '남북으로 이어지는 이 능선이 유다와 에브라임 산지의 등뼈다. 절기마다 이 길로 올라갔다.'},

 {'id': 'ot-jericho-ai', 'nameKo': '여리고–아이–벧엘 오르막', 'nameEn': 'Jericho–Ai–Bethel ascent',
  'routeType': 'regional', 'region': '유대 광야',
  'via': ['여리고', '아이', '벧엘'],
  'periodKo': '철기 (정복 시대)',
  'attestation': ['수 7:2', '수 8:1-29', '수 10:1-15'],
  'basisKo': '여리고를 친 뒤 아이로 올라간 길이다(수 7-8장). 요단 계곡(-260 m)에서 산지(900 m)로 오르는 '
             '비탈이라 통로가 사실상 하나뿐이다.',
  'noteKo': '여리고에서 산지로 ‘올라간다’는 표현이 그대로 지형이다.'},

 {'id': 'ot-beth-horon', 'nameKo': '벧호론 비탈길', 'nameEn': 'Ascent/Descent of Beth-horon',
  'routeType': 'regional', 'region': '유다 산지 서쪽 비탈',
  'via': ['기브온', '벧호론', '아얄론 골짜기', '에그론'],
  'periodKo': '철기 (정복~왕국 시대)',
  'attestation': ['수 10:10-11', '삼상 13:18', '대하 8:5'],
  'basisKo': '여호수아가 아모리 다섯 왕을 쫓아 내려간 “벧호론에 올라가는 비탈길”이다(수 10:10-11). '
             '산지에서 해안 평야로 내려서는 몇 안 되는 통로라 마카베오 시대까지 전투가 반복된다.',
  'noteKo': '위 벧호론과 아래 벧호론이 이 비탈의 위아래 마을이다.'},

 {'id': 'ot-jezreel', 'nameKo': '이스르엘 평야 횡단로', 'nameEn': 'Jezreel Valley route',
  'routeType': 'regional', 'region': '이스르엘 평야',
  'via': ['므깃도', '다아낙', '이스르엘', '벧산(스구도볼리)'],
  'periodKo': '청동기~철기',
  'attestation': ['삿 5:19', '삼상 31:1-13', '왕하 9:27'],
  'basisKo': '드보라의 노래가 “다아낙 성 곁 므깃도 물 가에서” 싸웠다고 하고(삿 5:19), 사울이 길보아에서 '
             '죽은 뒤 시신이 벧산 성벽에 달렸다(삼상 31). 평야를 동서로 가르는 이 길이 그 무대다.',
  'noteKo': '해변길이 아루나 고개를 넘어 이 평야로 내려서서 요단 계곡으로 이어진다.'},

 {'id': 'ot-jabbok', 'nameKo': '세겜–숙곳–얍복 길 (야곱의 길)', 'nameEn': 'Shechem–Succoth–Jabbok route',
  'routeType': 'regional', 'region': '요단 계곡·길르앗',
  'via': ['세겜', '숙곳(요단)', '얍복강', '마하나임'],
  'periodKo': '청동기 (족장 시대)',
  'attestation': ['창 32:22-31', '창 33:17-18'],
  'basisKo': '야곱이 얍복 나루를 건너 씨름하고, 숙곳에 집을 짓고, 세겜에 이른 그 경로다(창 32-33). '
             '얍복강이 요단으로 드는 여울목이 건널 자리를 정한다.',
  'noteKo': '요단 동편에서 세겜으로 들어오는 길목이다.'},

 {'id': 'ot-salt', 'nameKo': '소금길 (헤브론–엔게디)', 'nameEn': 'Salt route (Hebron–En Gedi)',
  'routeType': 'trade', 'region': '유대 광야',
  'via': ['헤브론', '시스 고개', '엔게디'],
  'periodKo': '철기 (왕국 시대)',
  'attestation': ['대하 20:16', '수 15:62', '삼상 24:1'],
  'basisKo': '여호사밧 때 적군이 “시스 고개로 올라오리라” 한 그 비탈이다(대하 20:16). '
             '사해의 소금과 역청을 산지로 실어 올리던 길이며, 다윗이 사울을 피한 엔게디가 그 끝이다.',
  'noteKo': '유대 광야를 가로질러 사해까지 1,000 m 넘게 떨어진다.'},

 {'id': 'ot-negev', 'nameKo': '네게브 종단로 (아다림 길)', 'nameEn': 'Negev route / Way of Atharim',
  'routeType': 'trunk', 'region': '네게브',
  'via': ['가데스바네아', '아라드', '브엘세바'],
  'periodKo': '철기 (광야~왕국 시대)',
  'attestation': ['민 21:1', '민 13:26', '민 33:36-37'],
  'basisKo': '아랏 왕이 “이스라엘이 아다림 길로 온다”는 말을 듣고 싸우러 나온 그 길이다(민 21:1). '
             '가데스바네아에서 네게브를 건너 브엘세바로 드는 통로다.',
  'noteKo': '아다림 길의 정확한 선형은 논쟁이 있다. 여기서는 양 끝과 아랏을 잇는 지형상 통로로 그린다.'},

 {'id': 'ot-arabah', 'nameKo': '아라바 길', 'nameEn': 'Way of the Arabah',
  'routeType': 'trade', 'region': '아라바',
  'via': ['사해 남단', '에시온게벨'],
  'periodKo': '철기 (왕국 시대)',
  'attestation': ['신 2:8', '왕상 9:26', '왕상 22:48'],
  'basisKo': '“엘랏과 에시온게벨 곁으로 지나 아라바 길을 떠나”(신 2:8). 솔로몬이 에시온게벨에 배를 지은 '
             '그 항구로 내려가는 길이며, 아라바 지구대 바닥을 따라간다.',
  'noteKo': '사해 남단에서 홍해까지 이어지는 지구대 바닥길이다.'},

 {'id': 'ot-bashan', 'nameKo': '바산 길', 'nameEn': 'Way of Bashan',
  'routeType': 'regional', 'region': '바산',
  'via': ['아스다롯', '에드레이'],
  'periodKo': '철기 (정복 시대)',
  'attestation': ['민 21:33', '신 3:1-3'],
  'basisKo': '“그들이 돌이켜 바산 길로 올라가매 바산 왕 옥이 에드레이에서 맞아 싸우려고”(민 21:33). '
             '아스다롯과 에드레이는 옥의 두 도읍이다(수 12:4).',
  'noteKo': '짧지만 성경이 이름을 붙여 부르는 길이라 넣었다.'},
]

def route(a, b):
    """두 지점을 잇는, 걸어서 가장 덜 힘든 길. 원본 선이 없으므로 회랑을 넓게 연다."""
    L = hav(a, b)
    nx = max(6, int(L / STEP_M))
    half = min(MAX_OFF_M, L / 4)
    ny = max(5, int(half * 2 / STEP_M))
    if ny % 2 == 0: ny += 1
    mid = ny // 2
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2)); ky = 110570
    dx = (b[0] - a[0]) * kx; dy = (b[1] - a[1]) * ky
    ux, uy = dx / L, dy / L; px, py = -uy, ux
    def pos(i, j):
        along = L * i / nx; off = (j - mid) * (half * 2 / ny)
        ex = ux * along + px * off; ey = uy * along + py * off
        return [a[0] + ex / kx, a[1] + ey / ky]
    grid = [[None] * ny for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny):
            p = pos(i, j); grid[i][j] = (p, T.elev(p[0], p[1]))
    ea, eb = grid[0][mid][1], grid[nx][mid][1]
    if ea is None or eb is None: return None
    block_sea = min(ea, eb) > 5
    INF = float('inf')
    dp = [[INF] * ny for _ in range(nx + 1)]; back = [[0] * ny for _ in range(nx + 1)]
    dp[0][mid] = 0.0
    for i in range(1, nx + 1):
        for j in range(ny):
            p, e = grid[i][j]
            if e is None: continue
            if block_sea and abs(e) < 0.5: continue
            best = INF; bj = j
            for j2 in range(max(0, j - 2), min(ny, j + 3)):
                if dp[i - 1][j2] == INF: continue
                p2, e2 = grid[i - 1][j2]
                if e2 is None: continue
                off = abs(j - mid) / max(1, mid)
                c = dp[i - 1][j2] + T.tobler_cost(hav(p2, p), e - e2) * (1 + PULL * off * off)
                if c < best: best, bj = c, j2
            dp[i][j] = best; back[i][j] = bj
    if dp[nx][mid] == INF: return None
    path = []; j = mid
    for i in range(nx, -1, -1):
        path.append(grid[i][j][0]); j = back[i][j]
    path.reverse()
    return path

def roman_overlap(line, roman, tol_m=3000.0):
    """이 노선이 로마 도로(신약 층)와 같은 회랑을 얼마나 함께 쓰는가.
    후대에 같은 길을 다시 썼다는 것은 그 회랑이 오래된 통로였다는 방증이다."""
    near = 0; tot = 0
    for i in range(len(line) - 1):
        d = hav(line[i], line[i + 1]); tot += d
        p = line[i]
        for rl in roman:
            if any(hav(p, q) < tol_m for q in rl): near += d; break
    return round(near / tot * 100) if tot else 0

def main(dst):
    use_z(Z)
    G = gazetteer()
    # 신약 층(서기 30년)과 후대 로마 도로를 따로 모은다. 왕의 대로처럼 서기 30년
    # 층에는 없고 후대 로마 도로(Via Nova Traiana)가 같은 회랑을 쓴 노선이 있다.
    roman, roman_later = [], []
    rp = os.path.join(ROOT, 'data', 'roads-c30.geojson')
    if os.path.exists(rp):
        for f in json.load(open(rp, encoding='utf-8'))['features']:
            (roman if f['properties'].get('activeC30') else roman_later).extend(f['geometry']['coordinates'])
    feats = []; summary = []
    for r in ROADS:
        pts = []
        for name in r['via']:
            if name in G: pts.append(G[name])
            elif name in EXTRA: pts.append(EXTRA[name][0])
            else: raise SystemExit('좌표를 못 찾음: ' + name)
        segs = []
        for i in range(len(pts) - 1):
            seg = route(pts[i], pts[i + 1])
            if seg is None:
                print(f"  ! {r['id']} {r['via'][i]}~{r['via'][i+1]} 경로를 못 찾음(표고 없음)"); continue
            seg = T.simplify(seg, 25.0)
            segs.append(T.round_corners(seg))
        if not segs: continue
        km = sum(hav(s[i], s[i + 1]) for s in segs for i in range(len(s) - 1)) / 1000
        flat = [p for s in segs for p in s]
        ov = roman_overlap(flat, roman)
        ov_later = roman_overlap(flat, roman_later)
        cert = 'probable' if max(ov, ov_later) >= 40 else 'hypothetical'
        props = {'id': r['id'], 'roadId': r['id'], 'nameKo': r['nameKo'], 'nameEn': r['nameEn'],
                 'routeType': r['routeType'], 'testament': 'ot', 'activeC30': False,
                 'region': r['region'], 'periodKo': r['periodKo'],
                 'via': r['via'], 'relatedPlaces': r['via'], 'relatedVerses': r['attestation'],
                 'certainty': cert, 'lengthKm': round(km),
                 'walkDays': [round(km / 35), round(km / 25)],
                 'romanOverlapPct': ov, 'laterRomanOverlapPct': ov_later,
                 'sourceIds': ['bible-text', 'ot-places', 'mapterhorn-dem', 'itinere-2024'],
                 'noteKo': r['noteKo'], 'basisKo': r['basisKo'],
                 'geometrySource': 'termini + terrain least-cost path',
                 'license': '경로는 이 프로젝트가 계산한 값. 표고 Mapterhorn, 대조에 Itiner-e (CC BY 4.0).'}
        feats.append({'type': 'Feature', 'properties': props,
                      'geometry': {'type': 'MultiLineString',
                                   'coordinates': [T.round_coords(T.dedupe(T.drop_spikes(s))) for s in segs]}})
        summary.append({'id': r['id'], 'nameKo': r['nameKo'], 'km': round(km), 'certainty': cert,
                        'romanOverlapPct': ov, 'laterRomanOverlapPct': ov_later, 'segments': len(segs)})
    out = {'type': 'FeatureCollection', 'name': 'roads-ot',
           'note': '구약 시대 주요 도로 · 성경이 말하는 양 끝과 경유지를 잇는, 지형상 가장 걷기 쉬운 길이다. '
                   '철기시대 도로 유구의 선형이 아니라 교육용 재구성이며, 확실성은 아무리 높아도 ‘개연’이다.',
           'attribution': '표고 Mapterhorn terrarium · 지명 이 프로젝트의 구약·신약 지명 자료 · '
                          '노선 대조에 Itiner-e (CC BY 4.0)',
           'method': {'router': "토블러 보행함수 최소비용 경로", 'dem': f'Mapterhorn terrarium z{Z}',
                      'stepM': STEP_M, 'corridorHalfM': MAX_OFF_M, 'pull': PULL,
                      'certaintyRule': "후대 로마 도로(서기 30년 층 또는 그 이후 층)와 3 km 안에서 40% 이상 "
                                        "같은 회랑을 쓰면 '개연', 그 밖은 '추정'. '확정'은 쓰지 않는다. "
                                        "로마가 같은 길을 다시 썼다는 것은 그 회랑이 오래된 통로였다는 방증이다."},
           'features': feats}
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print('노선', len(feats), '· 총', round(sum(s['km'] for s in summary)), 'km')

if __name__ == '__main__':
    main(sys.argv[1])
