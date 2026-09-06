"""지도에 그려지는 지역 하천에 이름을 붙인다.

OSM 벡터 타일에는 하천 이름이 들어 있지만 대개 아랍어·히브리어이고, name:ko 가
달린 것은 이 지역 521개 가운데 8개뿐이다. 그래서 이름을 직접 얹은 선을 따로 만든다.

라벨 놓는 방식을 두 번 바꿨다. 벡터 타일 소스에 선 배치 라벨을 바로 붙이면 하나도
그려지지 않았고(같은 화면 점 배치는 9개), 물줄기 기하를 geojson 으로 옮겨도 선 배치는
화면당 한 개꼴이었다. 이 지역 와디는 굽이가 촘촘해 글자를 얹을 곧은 구간이 안 나온다.
그래서 물줄기마다 점 하나를 찍어 이름을 붙인다.

입력:  타일에서 훑어 모은 하천 기하 (name → 조각들)
출력:  data/rivers-local.geojson
"""
import json, math, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from world_labels import join, simplify, midpoint   # 조각 잇기·단순화는 세계 강과 같은 것을 쓴다

# 성경·고대사에서 뜻이 있는 물줄기의 한국어 이름.
# 라벨은 구불구불한 물줄기 위에 글자를 얹으므로 짧아야 한다. 긴 이름은 아예 놓이지
# 못한다 — '하스바니강 (요단 수원)'은 자리를 못 잡고 '하스바니강'은 잡힌다.
# 빈 문자열은 '[신약]·[구약] 지명 레이어가 이미 라벨을 다니 여기서는 빼라'는 뜻이다.
KO = {
  'River Jordan': '', 'Zarqa River': '', 'Wadi Mujib': '', 'Nahal Kishon': '',
  'Nahal HaBsor': '', 'Nahal Sorek': '', 'Wadi al-Arish': '', 'Wadi al Hasa': '',
  'Barada River': '', 'Al Aawaj': '', 'Orontes': '', 'Nile River': '', 'Euphrates': '',
  # 요단강 수원
  'Hasbani River': '하스바니강', 'Nahal Snir (Hatsbani)': '스닐 시내',
  'Nahal Dan': '단 시내', 'Nahal Hermon (Banias)': '바니아스 시내',
  # 갈릴리·북부·데가볼리
  'Litani River': '리타니강', 'Yarmuk River': '야르묵강',
  'Nahal Yarmukh': '야르묵강', 'Wadi Ruqqad': '루카드 시내', 'Ruqqad': '루카드 시내',
  'Nahal Tabor': '다볼 시내', 'Nahal Harod': '하롯 시내', 'Nahal Tsalmon': '찰몬 시내',
  'Nahal Amud': '아무드 시내', 'Nahal Tzalmon': '찰몬 시내', 'Wadi Shallalah': '와디 샬랄라',
  'Wadi al Arab': '와디 알아랍', 'Wadi Ziqlab': '와디 지클라브', 'Wadi al Yabis': '와디 알야비스',
  'Wadi Kufranjah': '와디 쿠프란자', 'Wadi Rajib': '와디 라지브',
  # 해안 평야
  'Nahal Yarkon': '야르콘강', 'Nahal Alexander': '알렉산더 시내',
  'Nahal Hadera': '하데라 시내', 'Nahal Poleg': '폴레그 시내', 'Ayalon River': '아얄론 시내',
  'Nahal Lakhish': '라기스 시내', 'Nahal Shikma': '시크마 시내',
  'Nahal Beersheba': '브엘세바 시내', 'Nahal Guvrin': '구브린 시내', 'Nahal Ela': '엘라 시내',
  'Nahal Ayalon': '아얄론 시내', 'Nahal Gerar': '그랄 시내', 'Nahal Besor': '브솔 시내',
  # 네게브·아라바·시내
  'Nahal Arava': '아라바 시내', 'Nahal Zin': '신 시내', 'Nahal Tsin': '신 시내',
  'Nahal Paran': '바란 시내', 'Nahal Nekarot': '네카롯 시내',
  'Wadi Feiran': '와디 페이란', 'Wadi Gharandal': '와디 가란델',
  'Wadi Uqabah': '와디 우카바', 'Wadi Gira': '와디 기라',
  # 요단 동편·모압
  "Wadi Zerka Ma'in": '와디 제르카 마인', 'Wadi Dhulayl': '와디 둘라일',
  'Wadi Jais': '와디 자이스', 'Wadi Safra': '와디 사프라', 'Wadi Rihab': '와디 리합',
  'Wadi al Sarah': '와디 앗사라', 'Wadi Madsus ash shamali': '와디 맛수스',
  # 베니게 해안
  'Nahr ed Damour': '다무르강', 'Nahr El Awali': '아왈리강',
  'Nahr el Aouali': '아왈리강', 'Nahr ez Zahrani': '자흐라니강',
  'Nahr El Barouk': '바루크강', 'Nahr El Safa': '사파강', 'Nahr Aray': '아라이강',
  'Ghzayyel River': '그자옐강', 'Sayniq River': '사이니크강', 'Hafir River': '하피르강',
  'Nahr El Kebir': '케비르강', 'Nahr Jaair': '자이르강',
  'Nahr el Ghaziri': '가지리강', 'Nahr Ibrahim': '이브라힘강',
  'Nahr al Kalb': '칼브강', 'Nahr Beirut': '베이루트강',
}


def latin(s):
    return any('a' <= c.lower() <= 'z' for c in s)


def length_km(parts):
    tot = 0.0
    for p in parts:
        for i in range(len(p) - 1):
            (x1, y1), (x2, y2) = p[i], p[i + 1]
            tot += math.hypot((x2 - x1) * math.cos(math.radians(y1)), y2 - y1) * 111.32
    return tot


def main(src, out_path):
    rows = json.loads(pathlib.Path(src).read_text(encoding='utf-8'))
    feats, skipped_ko, dropped = [], 0, 0
    for r in rows:
        key = r['k']
        ko = KO.get(key, None)
        if ko == '':
            skipped_ko += 1
            continue
        if ko is None:
            # 표에 없는 하천: OSM 의 한국어 이름 → 로마자 이름 순.
            ko = r['ko'] or (key if latin(key) else '')
        if not ko:
            dropped += 1          # 아랍어·히브리어 이름뿐이라 옮길 근거가 없다
            continue
        # 조각 잇기 허용 오차를 넉넉히 잡으면 안 된다. 이 지역 와디는 촘촘해서
        # 2km 짜리 오차로 이으면 상관없는 물줄기끼리 붙어 라벨이 놓일 수 없는
        # 지그재그가 된다(실측: 268개 중 167개가 최대 9.6km 를 건너뛰었다).
        parts = [simplify(p, 0.0008) for p in join(r['parts'], eps=0.0008)]
        parts = [p for p in parts if len(p) > 1]
        if not parts:
            continue
        km = length_km(parts)
        feats.append({'type': 'Feature', 'id': 'lr' + str(len(feats)),
                      'properties': {'ko': ko, 'en': key, 'km': round(km, 1),
                                     # 긴 물줄기부터 나오게 한다.
                                     'rank': 1 if km > 60 else 2 if km > 25 else 3 if km > 10 else 4},
                      # 가장 긴 조각의 가운데. 조각마다 찍으면 같은 이름이 여러 번 나온다.
                      'geometry': {'type': 'Point', 'coordinates': midpoint(parts)}})
    # 같은 한국어 이름이 여러 개면 가장 긴 물줄기만 남긴다 — 'Yarmuk River' 와
    # 'Nahal Yarmukh' 가 둘 다 야르묵강이라 화면에 이름이 두 번 나왔다.
    best = {}
    for f in feats:
        k = f['properties']['ko']
        if k not in best or f['properties']['km'] > best[k]['properties']['km']:
            best[k] = f
    dup = len(feats) - len(best)
    feats = sorted(best.values(), key=lambda f: -f['properties']['km'])
    for i, f in enumerate(feats):
        f['id'] = 'lr' + str(i)

    p = pathlib.Path(out_path)
    p.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats},
                            ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    import collections
    print(f'하천 {len(feats)}개 → {p.name} ({p.stat().st_size/1024:.0f} KB)')
    print(f'  지명 레이어와 겹쳐 뺀 것 {skipped_ko}개 · 옮길 이름이 없어 뺀 것 {dropped}개 · '
          f'같은 이름이라 합친 것 {dup}개')
    print('  등급', sorted(collections.Counter(f['properties']['rank'] for f in feats).items()))
    print('  한국어 이름을 직접 붙인 것', sum(1 for f in feats if f['properties']['ko'] != f['properties']['en']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
