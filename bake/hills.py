"""성경에 이름이 나오는 '언덕'을 지명 자료에 넣는다.

지금까지 이 지도의 고도 지명은 '산'(kind=mountain) 뿐이었다. 감람산·다볼산·
시온산처럼 24곳이 있는데, **언덕은 한 곳도 없었다.** 세계 봉우리 자료
(peaks.geojson, Natural Earth)도 이스라엘 상자 안에는 세 곳뿐이라 도움이 되지
않는다. 그런데 성경에서 언덕은 산 못지않은 무대다 — 사울이 살던 기브아가
'언덕'이라는 뜻이고, 다윗성의 등뼈가 오벨이며, 예수께서 달리신 곳이 해골
'언덕'이다.

**산과 따로 둔다.** 언덕은 산이 아니다. 모레 언덕은 515 m, 오벨은 700 m 로
둘레보다 조금 솟은 등성이일 뿐이어서, 헤르몬산(2,814 m)과 같은 삼각형으로
그리면 지형을 잘못 읽게 만든다. `kind=hill` 로 나누고 아이콘도 둥근 둔덕으로
따로 그린다.

**증거 등급을 붙인다.** 회당·정박지 자료와 같은 A/B/C 계약이다.
  A = 발굴로 자리가 확인됨
  B = 동일시가 널리 받아들여지나 이견이 있음
  C = 성경이 말하는 곳이되 자리는 근사·전승

**넣지 않은 것도 적는다.** 자리를 모르면 찍지 않는다 — 찍어 두면 아는 것처럼
보인다. 가렙 언덕(렘 31:39)과 고아(같은 절)는 예루살렘 어딘가라는 것 외에
알려진 것이 없어 뺐다. 사마리아 언덕(왕상 16:24, 오므리가 세멜에게서 산 산)은
이미 있는 '사마리아(세바스테)'와 같은 자리(35.195/32.280)여서 겹쳐 찍지 않았다.

좌표 출처: OpenBible.info 지명 자료(merged.txt), 예루살렘 언덕은 이 저장소의
jerusalem-c1 발굴 앵커와 같은 값을 쓴다 — 두 자료가 어긋나면 안 된다.

출력: data/ot-places.geojson · data/nt-places.geojson 에 kind=hill 로 덧붙인다.
      여러 번 돌려도 같은 결과가 나온다(이 스크립트가 넣은 것만 먼저 걷어낸다).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

GRADE = {
    'A': '발굴로 자리가 확인된 언덕',
    'B': '동일시가 널리 받아들여지나 이견이 있는 언덕',
    'C': '성경이 말하는 언덕이되 자리는 근사·전승',
}

# ko, en, lon, lat, rank, elev(없으면 None), grade, desc, refs
OT_HILLS = [
    ('오벨', 'Ophel', 35.23656, 31.77570, 5, 700, 'A',
     '성전 산 남쪽 등성이. 다윗성과 성전을 잇는 목으로, 웃시야와 므낫세가 성벽을 '
     '쌓고 느헤미야 때 느디님 사람들이 살았다. 발굴로 왕궁·성벽·성문이 드러났다.',
     '대하 27:3; 대하 33:14; 느 3:26-27'),
    ('모레 언덕(515m)', 'Hill of Moreh', 35.35738, 32.61773, 4, 515, 'A',
     '이스르엘 골짜기 북쪽에 홀로 솟은 언덕. 기드온이 삼백 명과 진 친 하롯 샘 '
     '맞은편, 미디안 진영이 있던 곳이다.',
     '삿 7:1'),
    ('할례 산(기브앗 하아랄롯)', 'Gibeath-haaraloth', 35.51855, 31.86378, 5, None, 'B',
     '길갈 부근. 요단을 건넌 이스라엘이 할례를 받고 그 부싯돌을 묻은 언덕이다.',
     '수 5:3'),
    ('하길라 언덕', 'Hill of Hachilah', 35.21669, 31.46660, 5, None, 'B',
     '유다 광야 남쪽. 다윗이 사울을 피해 숨었고, 뒤에 사울의 진영에 밤중에 '
     '내려가 창과 물병을 가져온 곳이다.',
     '삼상 23:19; 삼상 26:1-3'),
    ('하나님의 산 기브아(기브앗 엘로힘)', 'Gibeath-elohim', 35.22103, 31.93054, 5, None, 'C',
     '사무엘이 사울에게 일러 준 언덕. 블레셋 수비대가 있었고, 사울이 선지자 '
     '무리를 만나 예언한 자리다. 벧엘 남쪽으로 보나 자리는 근사다.',
     '삼상 10:5'),
    ('암마 언덕', 'Hill of Ammah', 35.34318, 31.86901, 5, None, 'C',
     '기브온 광야 길가. 아브넬이 요압에게 "칼이 영원히 사람을 상하겠느냐" 하고 '
     '외친 언덕이다. 자리는 근사다.',
     '삼하 2:24'),
    ('기브아(유다)', 'Gibeah (Judah)', 35.13333, 31.43333, 5, None, 'C',
     '유다 산지의 기브아. 베냐민의 기브아(사울의 고향)와는 다른 곳이다. '
     '자리는 근사다.',
     '수 15:57; 대하 13:2'),
]

NT_HILLS = [
    ('골고다(해골 언덕)', 'Golgotha', 35.22972, 31.77835, 4, 757, 'B',
     '"해골의 곳". 1세기에는 성벽 밖 옛 채석장이었고, 그 안에 바위를 파낸 무덤들이 '
     '있었다. 4세기 이래 성묘 교회 자리로 전해지며 채석장과 무덤이 발굴되었다.',
     '마 27:33; 막 15:22; 요 19:17'),
    ('베제다 언덕(새 성)', 'Bezetha', 35.23300, 31.78300, 5, 770, 'B',
     '예루살렘 북쪽의 넷째 언덕. 헤롯 아그립바 때 성벽 안으로 들어온 새 동네로, '
     '베데스다 못과 성전 산 북쪽이 여기에 붙는다.',
     '요세푸스 유대전쟁 5.4.2'),
    ('나사렛 낭떠러지 산', 'Mount Precipice', 35.30170, 32.68660, 5, 397, 'C',
     '나사렛 남쪽 벼랑. 회당에서 쫓겨난 예수를 동네 사람들이 밀쳐 떨어뜨리려 한 '
     '"동네가 건설된 산 낭떠러지"로 전해지는 곳이다.',
     '눅 4:29'),
]

SETS = {
    'ot-places.geojson': OT_HILLS,
    'nt-places.geojson': NT_HILLS,
}

# 아레오바고는 이미 들어 있으나 kind 가 landmark 다. '마르스 언덕'이므로 hill 로 옮긴다.
RECLASS = {'nt-places.geojson': ['아레오바고']}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, doc):
    # 원본이 한 줄로 눌린 자료다. 보기 좋게 펴면 줄 차이가 만 줄 넘게 나서
    # 무엇이 바뀌었는지 읽을 수 없게 된다. 같은 모양으로 되돌린다.
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')),
                    encoding='utf-8')


def main():
    total = 0
    for name, hills in SETS.items():
        path = ROOT / 'data' / name
        doc = load(path)
        feats = doc['features']

        # 이 스크립트가 넣은 것만 걷어낸다. kind 로만 거르면 아래 RECLASS 로 언덕이
        # 된 기존 지명(아레오바고)까지 같이 지워져, 두 번째로 돌릴 때 사라진다.
        # 실제로 그렇게 지워 본 뒤에 표식을 붙였다.
        before = len(feats)
        feats = [f for f in feats if f['properties'].get('src') != 'hills']
        removed = before - len(feats)

        for ko in RECLASS.get(name, []):
            for f in feats:
                if f['properties'].get('ko') == ko:
                    f['properties']['kind'] = 'hill'

        next_id = max(f['id'] for f in feats) + 1
        for ko, en, lon, lat, rank, elev, grade, desc, refs in hills:
            if any(f['properties'].get('ko') == ko for f in feats):
                raise SystemExit('이미 같은 이름이 있다: %s (%s)' % (ko, name))
            props = {'ko': ko, 'en': en, 'rank': rank, 'kind': 'hill',
                     'desc': desc, 'refs': refs, 'grade': grade, 'src': 'hills'}
            if elev is not None:
                props['elev'] = elev
            feats.append({'type': 'Feature', 'properties': props,
                          'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                          'id': next_id})
            next_id += 1

        doc['features'] = feats
        save(path, doc)

        n = sum(1 for f in feats if f['properties'].get('kind') == 'hill')
        by = {}
        for f in feats:
            if f['properties'].get('kind') == 'hill':
                by[f['properties'].get('grade', '-')] = by.get(f['properties'].get('grade', '-'), 0) + 1
        print('%-20s 언덕 %d곳 (앞서 걷어낸 것 %d) · 등급 %s · 전체 지명 %d곳'
              % (name, n, removed, by, len(feats)))
        total += len(hills)

    # 같은 자리에 겹쳐 찍지 않았는지 확인한다. 라벨이 포개지면 읽을 수 없다.
    for name in SETS:
        doc = load(ROOT / 'data' / name)
        pts = [(f['properties']['ko'], f['geometry']['coordinates'])
               for f in doc['features'] if f['geometry']['type'] == 'Point']
        for i, (ka, ca) in enumerate(pts):
            for kb, cb in pts[i + 1:]:
                if abs(ca[0] - cb[0]) < 1e-4 and abs(ca[1] - cb[1]) < 1e-4:
                    print('  겹침 주의: %s · %s (%s)' % (ka, kb, name))
    print('새로 넣은 언덕 %d곳' % total)


if __name__ == '__main__':
    main()
