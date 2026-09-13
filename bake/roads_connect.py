"""마을 안 연결로를 따로 구워, 길찾기가 짧은 구간에서도 실제 길을 따라가게 한다.

roads_modern.py 는 지방도(secondary)까지만 담는다. 그리면 지도가 읽히고 파일도
가볍기 때문이다. 그런데 **길찾기**에는 그것만으로 모자란다. 성지 사이를 잇는 마지막
한두 킬로미터가 대개 `residential` 이어서, 그 한 토막이 빠지면 길이 통째로 끊긴다.

실측: 예루살렘→베다니는 직선 2.6 km 인데 지방도까지만으로는 그 상자 안에 길이
아예 없어(∞) 라우터가 남쪽으로 12.5 km 를 돌았다. `residential` 을 얹으면 3.52 km 로
붙는다. 감람산 능선을 넘는 그 길은 OSM 에 멀쩡히 있고, 등급이 `residential` 일
뿐이었다. 이런 짝이 전체의 15.0%(2,770짝 중 416짝)였다.

그래서 이 파일은 **그리지 않고 길찾기에만 쓴다.** 지도에 얹으면 마을 골목이
1세기 지형을 덮어 버리고, 파일도 크다. 길찾기를 처음 누를 때만 받으므로 지도를
여는 속도에는 영향이 없다.

상자는 이스라엘·팔레스타인·골란으로 좁힌다. 다마스쿠스·카이로·베이루트까지 넣으면
길찾기에 쓰이지도 않는 대도시 골목이 파일의 대부분을 차지한다.

Overpass 는 한 번에 이만큼을 내주지 못하므로 격자로 나눠 받고 way id 로 중복을
지운다. `way(bbox)` 는 꼭짓점이 하나라도 상자에 걸치면 **전체 도형**을 주므로
경계에서 잘리지 않는다.

출력:  data/roads-connect.json   (roads-modern.json 과 같은 형식)
"""
import json, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'bake'))
from roads_modern import build, PRECISION          # 굽는 방법은 똑같이 쓴다

BBOX = (29.3, 34.2, 33.4, 36.0)                    # 남, 서, 북, 동
CLASSES = ('residential', 'unclassified', 'living_street', 'road')
OUT = ROOT / 'data' / 'roads-connect.json'

LAT_STEP = 0.5
LON_STEP = 0.6
ENDPOINTS = ['https://overpass-api.de/api/interpreter',
             'https://overpass.kumi.systems/api/interpreter',
             'https://overpass.private.coffee/api/interpreter']


def frange(a, b, step):
    x = a
    while x < b - 1e-9:
        yield x, min(x + step, b)
        x += step


CACHE = ROOT / 'bake' / '.cache-roads-connect'


def fetch_cell(s, w, n, e):
    # 칸마다 받은 것을 남겨 둔다. Overpass 가 붐벼 중간에 끊기는 일이 잦은데,
    # 다시 돌릴 때마다 처음부터 받으면 한 시간이 그대로 날아간다.
    CACHE.mkdir(exist_ok=True)
    hit = CACHE / ('%s_%s_%s_%s.json' % (s, w, n, e))
    if hit.exists():
        return json.loads(hit.read_text(encoding='utf-8'))
    d = _fetch_cell(s, w, n, e)
    hit.write_text(json.dumps(d), encoding='utf-8')
    return d


def _fetch_cell(s, w, n, e):
    q = ('[out:json][timeout:600];\n'
         'way["highway"~"^(%s)$"](%s,%s,%s,%s);\n'
         'out geom;' % ('|'.join(CLASSES), s, w, n, e))
    for attempt in range(6):
        ep = ENDPOINTS[attempt % len(ENDPOINTS)]
        r = subprocess.run(['curl', '-s', '--max-time', '900',
                            '--data-urlencode', 'data=' + q, ep],
                           capture_output=True, text=True)
        body = r.stdout.strip()
        if body.startswith('{'):
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                pass
        time.sleep(20)                              # 붐빌 때가 잦다. 쉬었다 다시 묻는다.
    sys.exit('Overpass 가 %s,%s,%s,%s 를 끝내 내주지 않았다' % (s, w, n, e))


def main():
    s0, w0, n0, e0 = BBOX
    cells = [(s, w, n, e) for s, n in frange(s0, n0, LAT_STEP)
                          for w, e in frange(w0, e0, LON_STEP)]
    print('격자 %d칸을 받는다 (%s)' % (len(cells), ', '.join(CLASSES)))
    seen, elements = set(), []
    for i, c in enumerate(cells, 1):
        d = fetch_cell(*c)
        new = 0
        for el in d.get('elements', []):
            if el.get('id') in seen:
                continue
            seen.add(el['id'])
            elements.append(el)
            new += 1
        print('  %2d/%d  %s  way %d개 (새것 %d)' % (i, len(cells), c, len(d.get('elements', [])), new))
    print('중복 뺀 way %d개' % len(elements))
    build({'elements': elements}, CLASSES, OUT)


if __name__ == '__main__':
    main()
