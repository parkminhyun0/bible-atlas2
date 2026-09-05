"""세계 지도용 주요 산맥·강 라벨 데이터를 만든다.

원본은 Natural Earth (public domain):
  - ne_10m_geography_regions_polys.geojson  → Range/mtn 폴리곤
  - ne_50m_rivers_lake_centerlines.geojson  → 강 중심선

산맥은 폴리곤이라 그대로는 곡선 라벨을 붙일 수 없다. 주성분축을 따라 잘라
구간마다 무게중심을 잡으면, 히말라야의 호나 안데스의 굽이를 따라가는 등줄기
선이 나온다. 이 선은 그리지 않고 라벨 경로로만 쓴다.

사용법:  python3 bake/world_labels.py <ne_regions.geojson> <ne_rivers.geojson>
"""
import json, math, sys, pathlib

# ── 산맥: 쓸 것과 한국어 이름 ──────────────────────────────────────────
# Natural Earth 의 NAME_KO 는 '코스트 마운틴스'처럼 음역이 섞여 있어 손으로 고친다.
RANGES = {
  'ALPS': '알프스산맥', 'ANDES': '안데스산맥', 'CAUCASUS MTS.': '캅카스산맥',
  'GREAT DIVIDING RANGE': '그레이트디바이딩산맥', 'HIMALAYAS': '히말라야산맥',
  'ROCKY MOUNTAINS': '로키산맥', 'TIAN SHAN': '톈산산맥', 'URAL MOUNTAINS': '우랄산맥',
  'Transantarctic Mountains': '남극횡단산맥',
  'ALASKA RANGE': '알래스카산맥', 'ALTAY MOUNTAINS': '알타이산맥',
  'APPALACHIAN MTS.': '애팔래치아산맥', 'ATLAS MOUNTAINS': '아틀라스산맥',
  'BROOKS RANGE': '브룩스산맥', 'CASCADE RANGE': '캐스케이드산맥',
  'CHAÎNE ANNAMITIQUE': '안남산맥', 'COAST MOUNTAINS': '코스트산맥',
  'ETHIOPIAN HIGHLANDS': '에티오피아고원', 'GREATER KHINGAN RANGE': '대싱안링산맥',
  'HINDU KUSH': '힌두쿠시산맥', 'KARAKORAM RA.': '카라코람산맥',
  'KUNLUN MOUNTAINS': '쿤룬산맥', 'PAMIRS': '파미르고원',
  'STANOVOY RANGE': '스타노보이산맥', 'ZAGROS MOUNTAINS': '자그로스산맥',
  'AHAGGAR MTS.': '아하가르산맥', 'APPENNINI': '아펜니노산맥',
  'CARPATHIAN MOUNTAINS': '카르파티아산맥', 'COAST RANGES': '코스트레인지',
  'DRAKENSBERG': '드라켄즈버그산맥', 'EASTERN GHATS': '동고츠산맥',
  'EASTERN SAYAN MTS.': '사얀산맥', 'ELBURZ MTS.': '엘부르즈산맥',
  'HEJAZ MTS.': '헤자즈산맥', 'KJØLEN MOUNTAINS': '스칸디나비아산맥',
  'MACKENZIE MTS.': '매켄지산맥', 'PYRENEES': '피레네산맥',
  'QUILIAN MOUNTAINS': '치롄산맥', 'SIERRA MADRE OCCIDENTAL': '서시에라마드레산맥',
  'SIERRA MADRE ORIENTAL': '동시에라마드레산맥', 'SIERRA NEVADA': '시에라네바다산맥',
  'SIKHOTE-ALIN’ RANGE': '시호테알린산맥', 'SOUTHERN ALPS': '서던알프스산맥',
  'TIBESTI MTS.': '티베스티산맥', 'WESTERN GHATS': '서고츠산맥',
  'VERKHOYANSK RANGE': '베르호얀스크산맥', 'CHERSKIY RANGE': '체르스키산맥',
  'Dinaric Alps': '디나르알프스산맥', 'Balkan Mts.': '발칸산맥',
  'Taurus Mts.': '토로스산맥', 'PONTIC MOUNTAINS': '폰투스산맥',
  'Lebanon Mts.': '레바논산맥', 'Anti Atlas': '안티아틀라스산맥',
  'CHUGACH MTS.': '추가치산맥',
  'GUIANA HIGHLANDS': '기아나고지', 'Serra do Mar': '세하두마르산맥', 'Serra Geral': '세하제라우산맥',
  'AÏR MTS.': '아이르산맥', 'ASIR MTS.': '아시르산맥',
  'ALTUN MTS.': '알툰산맥', 'MITUMBA MTS.': '미툼바산맥',
  'CRYSTAL MOUNTAINS': '크리스털산맥', 'Lesser Khingan Range': '샤오싱안링산맥',
  'Nan Ling Mts.': '난링산맥', 'Dabie Mts.': '다볘산맥',
  'ATLAS SAHARIEN': '사하라아틀라스산맥', 'HAUT ATLAS': '오트아틀라스산맥',
  'Siwalik Hills': '시왈리크구릉',
}

# ── 강: 한국어 이름 → Natural Earth 의 구간 이름들 ────────────────────
# 한 강이 구간마다 다른 현지 이름으로 쪼개져 있어(창장 = Tuotuo·Tongtian·Jinsha·
# Chang Jiang·Yangtze) 이름으로 묶어 하나의 선으로 만든다.
RIVERS = {
  '나일강': ['Nile', 'Bahr el Jebel', 'Albert Nile', 'Victoria Nile', 'El Bahr el Abyad', 'Damietta Branch', 'Rosetta Branch'],
  '청나일강': ['El Bahr el Azraq', 'Abay'],
  '콩고강': ['Congo', 'Lualaba'], '우방기강': ['Ubangi', 'Uele'], '카사이강': ['Kasai'],
  '니제르강': ['Niger'], '베누에강': ['Benue'], '잠베지강': ['Zambezi'],
  '오렌지강': ['Orange'], '바알강': ['Vaal'], '림포포강': ['Limpopo'],
  '세네갈강': ['Sénégal'], '볼타강': ['Volta'], '차리강': ['Chari'],
  '오카방고강': ['Okavango', 'Cubango'], '주바강': ['Jubba'],
  '유프라테스강': ['Euphrates', 'Al Furat', 'Firat'], '티그리스강': ['Tigris'],
  '샤트알아랍': ['Shatt al Arab'], '요단강': ['Jordan'],
  '인더스강': ['Indus'], '갠지스강': ['Ganges'], '브라마푸트라강': ['Brahmaputra', 'Yarlung', 'Dihang', 'Maquan'],
  '야무나강': ['Yamuna'], '나르마다강': ['Narmada'], '크리슈나강': ['Krishna'],
  '메콩강': ['Mekong', 'Lancang'], '살윈강': ['Salween', 'Nu'],
  '이라와디강': ['Ayeyarwady', 'Irrawaddy Delta', 'Nmai'],
  '창장(양쯔강)': ['Chang Jiang', 'Yangtze', 'Jinsha', 'Tongtian', 'Tuotuo'],
  '황허': ['Huang', 'Za'], '시장강': ['Xi'], '쑹화강': ['Songhua'],
  '아무르강': ['Amur', 'Heilong Jiang', 'Argun’', 'Hailar'],
  '셀렝가강': ['Selenge (Selenga)', 'Ideriyn'],
  '레나강': ['Lena'], '예니세이강': ['Yenisey', 'Verkhniy Yenisey', 'Malyy Yenisey'],
  '앙가라강': ['Angara'], '오브강': ['Ob'], '이르티시강': ['Irtysh', 'Ertis', 'Ertix'],
  '콜리마강': ['Kolyma'], '인디기르카강': ['Indigirka'], '페초라강': ['Pechora'],
  '북드비나강': ['Severnaya Dvina'],
  '시르다리야강': ['Syr Darya'], '아무다리야강': ['Amu  Darya'],
  '볼가강': ['Volga'], '우랄강': ['Ural'], '돈강': ['Don'], '드네프르강': ['Dnipro'],
  '도나우강(다뉴브)': ['Danube', 'Donau'], '라인강': ['Rhine', 'Rhein'],
  '엘베강': ['Elbe'], '오데르강': ['Oder'], '비스와강': ['Vistula'],
  '센강': ['Seine'], '루아르강': ['Loire'], '론강': ['Rhône'], '에브로강': ['Ebro'], '포강': ['Po'],
  '미시시피강': ['Mississippi'], '미주리강': ['Missouri'], '오하이오강': ['Ohio'],
  '아칸소강': ['Arkansas'], '콜로라도강': ['Colorado'], '리오그란데강': ['Rio Grande'],
  '컬럼비아강': ['Columbia'], '스네이크강': ['Snake'], '유콘강': ['Yukon'],
  '매켄지강': ['Mackenzie', 'Slave', 'Peace'], '프레이저강': ['Fraser'],
  '서스캐처원강': ['Saskatchewan', 'North Saskatchewan', 'South Saskatchewan'],
  '넬슨강': ['Nelson'], '세인트로렌스강': ['St. Lawrence'],
  '아마존강': ['Amazonas'], '마데이라강': ['Madeira', 'Mamoré', 'Guaporé'],
  '우카얄리강': ['Ucayali'], '네그루강': ['Negro'], '싱구강': ['Xingu'],
  '타파조스강': ['Tapajós'], '토칸칭스강': ['Tocantins'],
  '오리노코강': ['Orinoco'], '막달레나강': ['Magdalena'],
  '파라나강': ['Paraná'], '우루과이강': ['Uruguay'], '필코마요강': ['Pilcomayo'],
  '머리강': ['Murray'], '달링강': ['Darling', 'Barwon'],
}


def simplify(pts, tol):
    """더글러스–포이커. 세계 시점에서 강의 잔굽이는 픽셀 아래로 사라지는데,
    글자를 선 위에 놓을 때는 그 굽이가 각도 제한에 걸려 라벨이 통째로 버려진다."""
    if len(pts) < 3:
        return pts
    stack, keep = [(0, len(pts) - 1)], {0, len(pts) - 1}
    while stack:
        a, b = stack.pop()
        x1, y1 = pts[a]; x2, y2 = pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        far, fd = None, tol
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
            if d > fd:
                far, fd = i, d
        if far is not None:
            keep.add(far)
            stack += [(a, far), (far, b)]
    return [pts[i] for i in sorted(keep)]


def join(parts, eps=0.05):
    """끝점이 맞닿은 조각을 이어 붙인다. Natural Earth 의 강은 지류·구간마다
    잘려 있어, 그대로 두면 조각이 짧아 이름이 들어갈 자리가 안 나온다."""
    parts = [list(p) for p in parts if len(p) > 1]
    merged = True
    while merged:
        merged = False
        for i in range(len(parts)):
            for j in range(len(parts)):
                if i == j:
                    continue
                a, b = parts[i], parts[j]
                if math.dist(a[-1], b[0]) < eps:
                    parts[i] = a + b[1:]
                elif math.dist(a[-1], b[-1]) < eps:
                    parts[i] = a + b[::-1][1:]
                elif math.dist(a[0], b[0]) < eps:
                    parts[i] = a[::-1] + b[1:]
                elif math.dist(a[0], b[-1]) < eps:
                    parts[i] = b + a[1:]
                else:
                    continue
                parts.pop(j)
                merged = True
                break
            if merged:
                break
    return parts


# 성경 지도에서 중요한 이름은 Natural Earth 의 세계 축척 등급보다 먼저 나와야 한다.
# (요단강은 세계 기준으로 6등급이라 그대로 두면 거의 끝까지 확대해야 나온다.)
PROMOTE = {'요단강': 3, '티그리스강': 3, '레바논산맥': 3, '토로스산맥': 3,
           '샤트알아랍': 4, '아르논강': 4}

def rings(geom):
    """폴리곤/멀티폴리곤의 바깥 고리 좌표를 모두 모은다."""
    if geom['type'] == 'Polygon':
        return [geom['coordinates'][0]]
    return [poly[0] for poly in geom['coordinates']]


def spine(geom, bins=14):
    """주성분축을 따라 구간을 나누고 구간별 무게중심을 이어 등줄기를 만든다."""
    pts = [p for ring in rings(geom) for p in ring]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    # 위도가 높을수록 경도 1도의 실거리가 짧다. 보정하지 않으면 고위도 산맥의
    # 주축이 동서로 기울어 등줄기가 산맥을 벗어난다.
    k = math.cos(math.radians(my)) or 1e-6
    d = [((p[0] - mx) * k, p[1] - my) for p in pts]
    sxx = sum(x * x for x, _ in d) / n
    syy = sum(y * y for _, y in d) / n
    sxy = sum(x * y for x, y in d) / n
    # 2x2 공분산행렬의 첫 고유벡터
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    vx, vy = math.cos(theta), math.sin(theta)

    ts = [x * vx + y * vy for x, y in d]
    lo, hi = min(ts), max(ts)
    if hi - lo < 1e-9:
        return None
    buckets = [[] for _ in range(bins)]
    for p, t in zip(pts, ts):
        i = min(bins - 1, int((t - lo) / (hi - lo) * bins))
        buckets[i].append(p)
    line = [[sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b)]
            for b in buckets if b]
    if len(line) < 2:
        return None
    # 구간 무게중심은 들쭉날쭉하다. 3점 이동평균으로 한 번 다듬는다.
    sm = [line[0]]
    for i in range(1, len(line) - 1):
        sm.append([(line[i - 1][j] + line[i][j] * 2 + line[i + 1][j]) / 4 for j in (0, 1)])
    sm.append(line[-1])
    return sm


def midpoint(parts):
    """가장 긴 조각의 길이 중앙에 놓는다. 선 배치를 못 쓰는 낮은 줌에서 이름
    하나만 찍을 자리다. 조각마다 라벨이 붙으면 니제르강처럼 이름이 두 번 나온다."""
    best = max(parts, key=lambda pt: sum(math.dist(pt[i], pt[i + 1]) for i in range(len(pt) - 1)))
    seg = [math.dist(best[i], best[i + 1]) for i in range(len(best) - 1)]
    half, run = sum(seg) / 2, 0.0
    for i, d in enumerate(seg):
        if run + d >= half:
            t = (half - run) / d if d else 0
            return [round(best[i][0] + (best[i + 1][0] - best[i][0]) * t, 3),
                    round(best[i][1] + (best[i + 1][1] - best[i][1]) * t, 3)]
        run += d
    return [round(c, 3) for c in best[len(best) // 2]]


def build_ranges(path):
    src = json.load(open(path, encoding='utf-8'))
    out, seen = [], set()
    for f in src['features']:
        p = f['properties']
        if p.get('FEATURECLA') != 'Range/mtn':
            continue
        ko = RANGES.get(p.get('NAME') or '')
        if not ko or ko in seen:
            continue
        s = spine(f['geometry'])
        if not s:
            continue
        seen.add(ko)
        out.append({'type': 'Feature', 'id': 'r' + str(len(out)),
                    'properties': {'ko': ko, 'en': p.get('NAME_EN') or p.get('NAME'),
                                   'rank': PROMOTE.get(ko, int(p.get('SCALERANK') or 4))},
                    'geometry': {'type': 'LineString', 'coordinates': [[round(c, 3) for c in pt] for pt in s]}})
    missing = sorted(set(RANGES.values()) - seen)
    return out, missing


def build_rivers(path):
    src = json.load(open(path, encoding='utf-8'))
    by_name = {}
    for f in src['features']:
        by_name.setdefault(f['properties'].get('name'), []).append(f)
    out, missing = [], []
    for ko, aliases in RIVERS.items():
        parts, rank = [], 9
        for a in aliases:
            for f in by_name.get(a, []):
                g = f['geometry']
                if g['type'] == 'LineString':
                    parts.append(g['coordinates'])
                else:
                    parts.extend(g['coordinates'])
                rank = min(rank, int(f['properties'].get('scalerank') or 9))
        if not parts:
            missing.append(ko)
            continue
        parts = [simplify(pt, 0.06) for pt in join(parts)]
        parts = [pt for pt in parts if len(pt) > 1]
        out.append({'type': 'Feature', 'id': 'w' + str(len(out)),
                    'properties': {'ko': ko, 'en': aliases[0], 'rank': PROMOTE.get(ko, rank),
                                   'parts': len(parts)},
                    'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[[round(c, 3) for c in pt] for pt in part] for part in parts]}})
    return out, missing


if __name__ == '__main__':
    reg, riv = sys.argv[1], sys.argv[2]
    rg, rg_missing = build_ranges(reg)
    rv, rv_missing = build_rivers(riv)
    root = pathlib.Path(__file__).resolve().parent.parent / 'data'
    for name, feats in (('ranges.geojson', rg), ('rivers-major.geojson', rv)):
        (root / name).write_text(json.dumps(
            {'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8')
    # 낮은 줌(지구 시점)에서 쓸 점 앵커. 산맥·강 하나에 정확히 하나씩 만든다.
    pts = []
    for kind, feats in (('range', rg), ('river', rv)):
        for f in feats:
            g = f['geometry']
            parts = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
            pr = dict(f['properties'], kind=kind)
            pr.pop('parts', None)
            pts.append({'type': 'Feature', 'id': kind[0] + 'p' + str(len(pts)),
                        'properties': pr,
                        'geometry': {'type': 'Point', 'coordinates': midpoint(parts)}})
    (root / 'world-labels-pt.geojson').write_text(json.dumps(
        {'type': 'FeatureCollection', 'features': pts}, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8')
    print(f'산맥 {len(rg)}개 · 강 {len(rv)}개 · 점 앵커 {len(pts)}개')
    if rg_missing:
        print('원본에 없는 산맥:', ', '.join(rg_missing))
    if rv_missing:
        print('원본에 없는 강:', ', '.join(rv_missing))
