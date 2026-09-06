"""세계 지도용 주요 산맥·강 라벨 데이터를 만든다.

원본은 Natural Earth (public domain):
  - ne_10m_geography_regions_polys.geojson  → Range/mtn 폴리곤
  - ne_50m_rivers_lake_centerlines.geojson  → 강 중심선
  - ne_10m_geography_regions_elevation_points.geojson → 봉우리

산맥은 폴리곤이라 그대로는 곡선 라벨을 붙일 수 없다. 주성분축을 따라 잘라
구간마다 무게중심을 잡으면, 히말라야의 호나 안데스의 굽이를 따라가는 등줄기
선이 나온다. 이 선은 그리지 않고 라벨 경로로만 쓴다.

사용법:  python3 bake/world_labels.py <ne_regions.geojson> <ne_rivers.geojson> <ne_peaks.geojson>
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


# ── 세계 주요 산봉우리: 쓸 것과 한국어 이름·등급 ───────────────────────
# Natural Earth 의 scalerank 는 봉우리에서 신뢰하기 어렵다(칸첸중가가 9등급).
# 널리 알려진 정도로 직접 등급을 매긴다. 1 = 지구 시점에서도 보인다.
PEAKS = {
  'Mount Everest': ('에베레스트산', 1), 'K2': ('K2(고드윈오스틴)', 1),
  'Cerro Aconcagua': ('아콩카과산', 1), 'Denali': ('데날리산(매킨리)', 1),
  'Mount Kilimanjaro': ('킬리만자로산', 1), 'Gora Elbrus': ('엘브루스산', 1),
  'Vinson Massif': ('빈슨산괴', 1), 'Puncak Jaya': ('푼착자야산', 1),
  'Kanchenjunga': ('칸첸중가', 2), 'Nanga Parbat': ('낭가파르바트', 2),
  'Dhaulagiri': ('다울라기리', 2), 'Mont Blanc': ('몽블랑산', 2),
  'Fuji': ('후지산', 2), 'Matterhorn': ('마터호른', 2),
  'Mount Kenya': ('케냐산', 2), 'Mount Damavand': ('다마반드산', 2),
  'Mount Ararat': ('아라라트산', 2), 'Nevado Ojos del Salado': ('오호스델살라도산', 2),
  'Nevado Huascarán': ('우아스카란산', 2), 'Chimborazo': ('침보라소산', 2),
  'Aoraki (Mount Cook)': ('쿡산(아오라키)', 2), 'Mount Logan': ('로건산', 2),
  'Pico de Orizaba': ('오리사바산', 2), 'Paektu-san': ('백두산', 2),
  'Mount Erebus': ('에러버스산', 2), 'Kailash': ('카일라스산', 2),
  'Tirich Mir': ('티리치미르', 3), 'Nowshak': ('노샤크산', 3),
  'Pik Imeni Ismail Samani': ('이스모일소모니봉', 3), 'Pik Pobeda': ('포베다산', 3),
  'Gongga Shan': ('궁가산', 3), 'Namcha Barwa': ('남차바르와산', 3),
  'Nanda Devi': ('난다데비', 3), 'Gangkar Punsum': ('강카르푼섬', 3),
  'Volcán Popocatépetl': ('포포카테페틀산', 3), 'Nevado Illimani': ('일리마니산', 3),
  'Ritacuba Blanco': ('리타쿠바블랑코', 3), 'Mount Whitney': ('휘트니산', 3),
  'Mount Rainier': ('레이니어산', 3), 'Mount Elbert': ('엘버트산', 3),
  'Mount Shasta': ('섀스타산', 3), 'Mount Hood': ('후드산', 3),
  'Gunung Kinabalu': ('키나발루산', 3), 'Gunung Rinjani': ('린자니산', 3),
  'Gunung Semeru': ('스메루산', 3), 'Monte Rosa': ('몬테로사산', 3),
  'Grossglockner': ('그로스글로크너산', 3), 'Zugspitze': ('추크슈피체산', 3),
  'Monte Etna': ('에트나산', 3), 'Mount Olympus': ('올림포스산', 3),
  'Jebel Toubkal': ('투브칼산', 3), 'Emi Koussi': ('에미쿠시산', 3),
  'Mont Cameroun': ('카메룬산', 3), 'Volcan Karisimbi': ('카리심비산', 3),
  'Mafadi': ('마파디산', 3), 'Gora Shkhara': ('시하라산', 3),
  'Mount Kosciuszko': ('코지어스코산', 3), 'Mount Tapuaenuku': ('타푸에누쿠산', 3),
  'Halla-san': ('한라산', 3), 'Vesuvio': ('베수비오산', 3),
  'Ben Nevis': ('벤네비스산', 3), 'Galdhpiggen': ('갈회피겐산', 3),
  'Tavan Bogd Uul': ('타반보그드산', 3), 'Aragats Lerr': ('아라가츠산', 3),
  'Bazar Dyuzi': ('바자르뒤쥐산', 3), 'Zard Kuh': ('자르드쿠산', 3),
  'Cheekha Dar': ('치카다르산', 3), 'Jabal ash Shaykh': ('헤르몬산(자발셰이크)', 3),
  'Gebel Katherna': ('카타리나산(시나이 반도 최고봉)', 3),
  'Jabal al Lawz': ('자발알라우즈', 3), 'Amba Farit': ('암바파리트산', 3),
  'Hkakabo Razi': ('카카보라지산', 3), 'Musala': ('무살라산', 3),
  'Triglav': ('트리글라우산', 3), 'Maromokotro': ('마로모코트로산', 3),
  'Phou Bia': ('푸비아산', 3), 'Mount Halcon': ('할콘산', 3),
  'Psiloritis': ('이디산(크레타 최고봉)', 3), 'Wutai Shan': ('우타이산', 3),
  'Pico de Almanzor': ('알만소르봉', 3), 'Mount Sir Sandford': ('서샌드퍼드산', 3),
  'Cerro San Rafael': ('산라파엘산', 3), 'Volcán Tacaná': ('타카나산', 3),
  'Pico de Santa Isabel': ('산타이사벨봉', 3), 'Ayrybaba': ('아이리바바산', 3),
  'Big Ben': ('빅벤산', 3), 'Mtorwi': ('음토르위산', 3),
}


# ── 나라 코드 → 한국어 (봉우리의 '어디에 있는가'를 적기 위해) ────────
NATION = {
'AD':'안도라','AE':'아랍에미리트','AF':'아프가니스탄','AG':'앤티가바부다','AI':'앵귈라','AL':'알바니아',
'AM':'아르메니아','AN':'네덜란드령 안틸레스','AQ':'남극','AS':'아메리칸사모아','AT':'오스트리아','AU':'오스트레일리아',
'AW':'아루바','AZ':'아제르바이잔','BA':'보스니아헤르체고비나','BB':'바베이도스','BD':'방글라데시','BE':'벨기에',
'BF':'부르키나파소','BG':'불가리아','BH':'바레인','BI':'부룬디','BJ':'베냉','BL':'생바르텔레미','BM':'버뮤다',
'BN':'브루나이','BO':'볼리비아','BR':'브라질','BS':'바하마','BT':'부탄','BV':'부베섬','BW':'보츠와나','BY':'벨라루스',
'BZ':'벨리즈','CA':'캐나다','CD':'콩고민주공화국','CF':'중앙아프리카공화국','CG':'콩고공화국','CH':'스위스',
'CK':'쿡 제도','CL':'칠레','CM':'카메룬','CN':'중국','CO':'콜롬비아','CX':'크리스마스섬','CZ':'체코','DE':'독일',
'DJ':'지부티','DK':'덴마크','DM':'도미니카','EE':'에스토니아','EG':'이집트','ER':'에리트레아','ES':'스페인',
'ET':'에티오피아','FI':'핀란드','FM':'미크로네시아','FO':'페로 제도','FR':'프랑스','France':'프랑스','GA':'가봉',
'GD':'그레나다','GE':'조지아','GF':'프랑스령 기아나','GH':'가나','GI':'지브롤터','GP':'과들루프','GQ':'적도기니',
'GR':'그리스','GT':'과테말라','GU':'괌','HK':'홍콩','HM':'허드맥도널드 제도','HN':'온두라스','HR':'크로아티아',
'HT':'아이티','HU':'헝가리','ID':'인도네시아','IL':'이스라엘','IM':'맨섬','IN':'인도','IQ':'이라크','IR':'이란',
'IT':'이탈리아','Italy':'이탈리아','JO':'요르단','JP':'일본','KG':'키르기스스탄','KM':'코모로','KN':'세인트키츠네비스',
'KP':'북한','KR':'대한민국','KY':'케이맨 제도','LA':'라오스','LB':'레바논','LC':'세인트루시아','LI':'리히텐슈타인',
'LR':'라이베리아','LS':'레소토','LU':'룩셈부르크','LY':'리비아','MA':'모로코','MC':'모나코','MD':'몰도바',
'ME':'몬테네그로','MF':'생마르탱','MG':'마다가스카르','ML':'말리','MM':'미얀마','MN':'몽골','MO':'마카오',
'MQ':'마르티니크','MR':'모리타니','MS':'몬트세랫','MT':'몰타','MU':'모리셔스','MW':'말라위','MX':'멕시코',
'NC':'뉴칼레도니아','NF':'노퍽섬','NG':'나이지리아','NL':'네덜란드','NO':'노르웨이','NP':'네팔','NZ':'뉴질랜드',
'PF':'프랑스령 폴리네시아','PG':'파푸아뉴기니','PH':'필리핀','PK':'파키스탄','PL':'폴란드','PM':'생피에르미클롱',
'PR':'푸에르토리코','PT':'포르투갈','PW':'팔라우','PY':'파라과이','RS':'세르비아','RU':'러시아','RW':'르완다',
'SA':'사우디아라비아','SC':'세이셸','SD':'수단','SG':'싱가포르','SH':'세인트헬레나','SI':'슬로베니아','SM':'산마리노',
'SV':'엘살바도르','SY':'시리아','SZ':'에스와티니','TC':'터크스케이커스 제도','TH':'태국','TM':'투르크메니스탄',
'TN':'튀니지','TO':'통가','TP':'동티모르','TR':'튀르키예','TT':'트리니다드토바고','TZ':'탄자니아','UA':'우크라이나',
'US':'미국','UY':'우루과이','VC':'세인트빈센트그레나딘','VE':'베네수엘라','VG':'영국령 버진아일랜드',
'VI':'미국령 버진아일랜드','WF':'왈리스퓌튀나','WS':'사모아','XC':'클리퍼턴섬','XJ':'얀마옌섬','XK':'코소보',
'YT':'마요트','ZA':'남아프리카공화국','ZM':'잠비아',
}

# 나라 정보가 없는 지점(387곳)은 대륙·권역으로 대신한다.
REGION_KO = {'Asia': '아시아', 'Africa': '아프리카', 'Europe': '유럽',
             'North America': '북아메리카', 'South America': '남아메리카',
             'Oceania': '오세아니아', 'Antarctica': '남극', 'Seven seas (open ocean)': '대양'}
SUBREGION_KO = {'Malay Archipelago': '말레이 제도', 'West Indies': '서인도 제도',
                'Central America': '중앙아메리카', 'British Isles': '브리튼 제도',
                'Mediterranean Sea': '지중해', 'Greenland': '그린란드', 'Iceland': '아이슬란드',
                'Arctic Archipelago': '북극 제도', 'Arctic Ocean': '북극해',
                'North Atlantic Ocean': '북대서양', 'Southern Atlantic Ocean': '남대서양',
                'Indian Ocean': '인도양', 'South Indian Ocean': '남인도양',
                'South Pacific Ocean': '남태평양', 'Australia': '오스트레일리아',
                'New Zealand': '뉴질랜드', 'Melanesia': '멜라네시아', 'Micronesia': '미크로네시아',
                'Polynesia': '폴리네시아', 'Comores': '코모로', 'Falkland Islands': '포클랜드 제도',
                'Galapagos Islands': '갈라파고스 제도'}

# ── 이름난 봉우리의 설명과 성경 본문 ──────────────────────────────
# NE 이름 → (설명, 성경 본문). 성경에 나오는 산은 본문을 적고, 그 밖에는 빈 문자열.
PEAK_INFO = {
 'Mount Ararat': ('홍수가 그친 뒤 방주가 머문 산지. 아르메니아 고원에 우뚝 선 화산이다.', '창 8:4'),
 'Jabal ash Shaykh': ('구약의 헤르몬산. 만년설이 요단강의 수원이 되고, 변화산으로 보는 견해가 많다.', '신 3:9; 시 133:3; 마 17:1'),
 'Gebel Katherna': ('시나이 반도의 최고봉. 그 곁의 무사산을 전통적으로 시내산으로 본다.', '출 19:20 참조'),
 'Jabal al Lawz': ('아라비아 북서부의 산. 일부에서 시내산의 다른 후보로 든다.', '갈 4:25 참조'),
 'Mount Olympus': ('헬라 신들이 산다고 믿어진 산. 바울이 만난 다신 신앙의 배경이다.', '행 17:22-23 참조'),
 'Vesuvio': ('79년에 폭발해 폼페이를 묻은 화산. 1세기 로마 도시의 모습을 그대로 남겼다.', ''),
 'Mount Everest': ('세계에서 가장 높은 산. 네팔과 티베트의 경계에 선다.', ''),
 'K2': ('세계 2위 봉우리. 카라코람의 오르기 어려운 산으로 이름났다.', ''),
 'Kanchenjunga': ('세계 3위 봉우리. 인도와 네팔 사이에 있다.', ''),
 'Cerro Aconcagua': ('아메리카 대륙의 최고봉. 안데스 남부에 있다.', ''),
 'Denali': ('북아메리카의 최고봉. 알래스카산맥의 중심이다.', ''),
 'Mount Kilimanjaro': ('아프리카의 최고봉. 적도 부근인데도 정상에 만년설이 있다.', ''),
 'Gora Elbrus': ('유럽의 최고봉으로 꼽히는 캅카스의 화산이다.', ''),
 'Vinson Massif': ('남극 대륙의 최고봉이다.', ''),
 'Puncak Jaya': ('오세아니아의 최고봉. 적도 부근의 만년설로 이름났다.', ''),
 'Mont Blanc': ('알프스의 최고봉. 프랑스와 이탈리아가 나눠 가진다.', ''),
 'Matterhorn': ('네 면이 칼처럼 선 알프스의 상징 같은 봉우리다.', ''),
 'Fuji': ('일본의 최고봉이자 상징인 원뿔 화산이다.', ''),
 'Mount Kenya': ('아프리카 2위 봉우리. 나라 이름의 뿌리다.', ''),
 'Mount Damavand': ('이란 엘부르즈산맥의 최고봉. 페르시아 신화의 무대다.', ''),
 'Nevado Ojos del Salado': ('세계에서 가장 높은 화산. 칠레와 아르헨티나 국경에 있다.', ''),
 'Nevado Huascarán': ('페루의 최고봉. 안데스 열대 빙하로 이름났다.', ''),
 'Chimborazo': ('지구 중심에서 가장 먼 지점. 적도가 부풀어 있어 그렇다.', ''),
 'Aoraki (Mount Cook)': ('뉴질랜드의 최고봉. 마오리 이름은 아오라키다.', ''),
 'Mount Logan': ('캐나다의 최고봉. 밑면이 세계에서 가장 넓은 산으로 꼽힌다.', ''),
 'Pico de Orizaba': ('멕시코의 최고봉이자 북아메리카 3위 화산이다.', ''),
 'Paektu-san': ('한반도의 최고봉. 정상에 천지가 있다.', ''),
 'Mount Erebus': ('남극의 활화산. 용암 호수가 있다.', ''),
 'Kailash': ('힌두교·불교·자이나교·본교가 함께 성산으로 여기는 티베트의 산이다.', ''),
 'Halla-san': ('제주도의 화산. 남한에서 가장 높다.', ''),
 'Ben Nevis': ('영국 제도의 최고봉이다.', ''),
 'Zugspitze': ('독일의 최고봉. 알프스 북쪽 기슭이다.', ''),
 'Grossglockner': ('오스트리아의 최고봉이다.', ''),
 'Monte Rosa': ('알프스에서 몽블랑 다음으로 높은 산괴다.', ''),
 'Monte Etna': ('유럽에서 가장 활발한 화산. 시실리에 있다.', ''),
 'Jebel Toubkal': ('북아프리카의 최고봉. 아틀라스산맥에 있다.', ''),
 'Emi Koussi': ('사하라의 최고봉. 티베스티의 방패 화산이다.', ''),
 'Mont Cameroun': ('서아프리카의 최고봉. 바다에 접한 활화산이다.', ''),
 'Volcan Karisimbi': ('비룽가 화산군의 최고봉이다.', ''),
 'Mafadi': ('남아프리카공화국의 최고봉. 드라켄즈버그산맥에 있다.', ''),
 'Gora Shkhara': ('조지아의 최고봉. 캅카스 주능선에 있다.', ''),
 'Mount Kosciuszko': ('오스트레일리아 대륙의 최고봉이다.', ''),
 'Mount Tapuaenuku': ('뉴질랜드 남섬 북동부의 최고봉이다.', ''),
 'Galdhpiggen': ('북유럽의 최고봉. 노르웨이에 있다.', ''),
 'Tavan Bogd Uul': ('몽골의 최고봉. 알타이산맥에 있다.', ''),
 'Aragats Lerr': ('아르메니아의 최고봉. 아라라트산과 마주 본다.', ''),
 'Bazar Dyuzi': ('아제르바이잔의 최고봉이다.', ''),
 'Zard Kuh': ('자그로스산맥의 주봉. 이란 중부의 강들이 여기서 시작한다.', ''),
 'Cheekha Dar': ('이라크의 최고봉. 자그로스 북부에 있다.', ''),
 'Amba Farit': ('에티오피아 고원의 봉우리. 청나일의 물이 이 고원에서 나온다.', ''),
 'Hkakabo Razi': ('미얀마의 최고봉. 히말라야 동쪽 끝이다.', ''),
 'Musala': ('발칸반도의 최고봉. 불가리아 릴라산맥에 있다.', ''),
 'Triglav': ('슬로베니아의 최고봉이자 나라의 상징이다.', ''),
 'Maromokotro': ('마다가스카르의 최고봉이다.', ''),
 'Phou Bia': ('라오스의 최고봉이다.', ''),
 'Mount Halcon': ('필리핀 민도로섬의 최고봉이다.', ''),
 'Psiloritis': ('그레데(크레타)의 최고봉. 제우스가 자란 동굴 전승이 있다.', '딛 1:5 참조'),
 'Wutai Shan': ('중국 불교의 사대 명산 가운데 하나다.', ''),
 'Pico de Almanzor': ('스페인 중부 그레도스산맥의 최고봉이다.', ''),
 'Gunung Kinabalu': ('보르네오섬의 최고봉이다.', ''),
 'Gunung Rinjani': ('인도네시아 롬복섬의 화산이다.', ''),
 'Gunung Semeru': ('자바섬의 최고봉이자 활화산이다.', ''),
 'Mount Whitney': ('미국 본토의 최고봉. 시에라네바다에 있다.', ''),
 'Mount Rainier': ('캐스케이드산맥의 최고봉. 시애틀에서 보인다.', ''),
 'Mount Elbert': ('로키산맥의 최고봉이다.', ''),
 'Mount Shasta': ('캘리포니아 북부의 큰 화산이다.', ''),
 'Mount Hood': ('오리건의 상징 같은 화산이다.', ''),
 'Volcán Popocatépetl': ('멕시코시티 곁의 활화산이다.', ''),
 'Nevado Illimani': ('볼리비아 라파스를 굽어보는 안데스의 봉우리다.', ''),
 'Ritacuba Blanco': ('콜롬비아의 최고봉이다.', ''),
 'Mount Sir Sandford': ('캐나다 셀커크산맥의 최고봉이다.', ''),
 'Cerro San Rafael': ('파라과이의 최고봉이다.', ''),
 'Volcán Tacaná': ('과테말라와 멕시코 국경의 활화산이다.', ''),
 'Pico de Santa Isabel': ('적도기니 비오코섬의 화산이다.', ''),
 'Ayrybaba': ('투르크메니스탄의 최고봉이다.', ''),
 'Big Ben': ('허드섬의 활화산. 오스트레일리아령 최고봉이다.', ''),
 'Mtorwi': ('탄자니아 남부 고원의 최고봉이다.', ''),
 'Tirich Mir': ('힌두쿠시산맥의 최고봉이다.', ''),
 'Nowshak': ('아프가니스탄의 최고봉이다.', ''),
 'Pik Imeni Ismail Samani': ('파미르고원의 최고봉. 옛 이름은 공산주의봉이다.', ''),
 'Pik Pobeda': ('톈산산맥의 최고봉이다.', ''),
 'Gongga Shan': ('쓰촨 서부의 최고봉이다.', ''),
 'Namcha Barwa': ('히말라야 동쪽 끝의 봉우리. 브라마푸트라강이 그 둘레를 돈다.', ''),
 'Nanda Devi': ('인도 안에 온전히 들어 있는 최고봉이다.', ''),
 'Gangkar Punsum': ('부탄의 최고봉. 아직 오른 사람이 없다.', ''),
 'Nanga Parbat': ('히말라야 서쪽 끝의 거봉. 인더스강이 그 발치를 지난다.', ''),
 'Dhaulagiri': ('네팔 중부의 8천 미터 봉우리다.', ''),
}


def clean_ko(ko, en):
    """Natural Earth 의 한국어 이름은 기계 음역이라 군더더기가 남는다.
    뜻이 바뀔 위험이 없는 기계적 흔적만 다듬는다(뜻을 새로 지어내지 않는다).
      '리우시 샨' → '리우시산'   '샨 다이윈' → '다이윈산'
      '쿠주-산'   → '쿠주산'     '마운트 타푸에누쿠' → '타푸에누쿠산'
      '고라 콘자코프스키 카멘' → '콘자코프스키 카멘산'
    """
    if not ko:
        return en
    ko = ko.strip()
    for head in ('마운트 ', '고라 ', '마운틴 '):
        if ko.startswith(head):
            ko = ko[len(head):] + '산'
    t = ko.split()
    if t and t[0] == '샨':            # 어순이 뒤집힌 중국어 山
        ko = ' '.join(t[1:]) + '산'
    elif t and t[-1] == '샨':
        ko = ' '.join(t[:-1]) + '산'
    if t and t[-1] == '펑':           # 중국어 峰
        ko = ' '.join(t[:-1]) + '봉'
    ko = ko.replace('-산', '산')
    if ko.endswith(' 산'):            # '다테 산' → '다테산'
        ko = ko[:-2] + '산'
    return ko


def peak_rank(ko, elev):
    """알려진 정도(PEAKS)가 있으면 그것을, 없으면 해발로 등급을 정한다."""
    e = elev or 0
    if e >= 5000:
        return 4
    if e >= 3500:
        return 5
    if e >= 2000:
        return 6
    return 7


def build_peaks(path):
    src = json.load(open(path, encoding='utf-8'))
    out, seen = [], set()
    for f in src['features']:
        p = f['properties']
        if p.get('featurecla') != 'mountain':
            continue
        name = p.get('name') or ''
        elev = p.get('elevation')
        hit = PEAKS.get(name)
        ko = hit[0] if hit else clean_ko(p.get('name_ko'), p.get('name_en') or name)
        if not ko or ko in seen:
            continue
        seen.add(ko)
        where = ' · '.join(dict.fromkeys(
            NATION[c] for c in ((p.get('nation1') or '').strip(), (p.get('nation2') or '').strip())
            if c in NATION))
        if not where:
            where = ' · '.join(x for x in (REGION_KO.get(p.get('region') or ''),
                                           SUBREGION_KO.get(p.get('subregion') or '')) if x)
        desc, refs = PEAK_INFO.get(name, ('', ''))
        props = {'ko': ko, 'en': p.get('name_en') or name,
                 'rank': hit[1] if hit else peak_rank(ko, elev), 'm': elev,
                 'elev': f'{elev:,} m' if elev else '', 'where': where}
        if desc:
            props['desc'] = desc
        if refs:
            props['refs'] = refs
        out.append({'type': 'Feature', 'id': 'k' + str(len(out)),
                    'properties': props, 'geometry': f['geometry']})
    missing = sorted(set(v[0] for v in PEAKS.values()) - seen)
    return out, missing



if __name__ == '__main__':
    reg, riv, pk = sys.argv[1], sys.argv[2], sys.argv[3]
    rg, rg_missing = build_ranges(reg)
    rv, rv_missing = build_rivers(riv)
    kk, kk_missing = build_peaks(pk)
    root = pathlib.Path(__file__).resolve().parent.parent / 'data'
    for name, feats in (('ranges.geojson', rg), ('rivers-major.geojson', rv), ('peaks.geojson', kk)):
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
    print(f'산맥 {len(rg)}개 · 강 {len(rv)}개 · 봉우리 {len(kk)}개 · 점 앵커 {len(pts)}개')
    if kk_missing:
        print('원본에 없는 봉우리:', ', '.join(kk_missing))
    if rg_missing:
        print('원본에 없는 산맥:', ', '.join(rg_missing))
    if rv_missing:
        print('원본에 없는 강:', ', '.join(rv_missing))
