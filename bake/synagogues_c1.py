"""서기 70년 이전 회당 건물·후보·문헌 증언.

정박지와 같은 A/B/C 증거 계약을 사용한다.
A=직접 고고학·명문, B=기능/연대 논쟁, C=문헌만 있고 건물 미확인.
좌표 기준은 building/findspot/site로 따로 밝힌다.
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "synagogues-c1.geojson"

GRADE = {
    "A": ("확인", "서기 70년 이전 회당을 직접 지지하는 건물·층위·명문"),
    "B": ("논쟁", "회당 후보이나 기능·연대 또는 동일시에 중요한 이견이 있음"),
    "C": ("문헌", "1세기 문헌은 회당을 증언하지만 건물 위치가 확인되지 않음"),
}

SOURCES = {
    "DB": "Bornblum Eretz Israel Synagogues research database, Kinneret College",
    "MAG": "Magness 2024, Ancient Synagogues in Palestine, British Academy",
    "GAM": "Gutman 1981, The Synagogue at Gamla",
    "MIG": "Avshalom-Gorni & Najar 2013; Runesson 2020, Magdala synagogue phases",
    "MIG2": "University of Haifa / IAA 2021, second Magdala synagogue excavation",
    "MAS": "Yadin 1966; Netzer 1991, Masada synagogue excavations",
    "HER": "Corbo 1967; Netzer 1981, Herodium synagogue conversion",
    "UMM": "Onn & Weksler-Bdolah 2004, Khirbet Umm el-Umdan",
    "QIR": "Magen, Zionit & Sirkis 2004, Khirbet Badd 'Isa–Qiryat Sefer",
    "REK": "Paz et al. 2018, Tel Rekhesh early Roman synagogue",
    "CAP": "Loffreda 1970–2003, Capernaum synagogue excavations and dating debate",
    "ETR": "Zissu & Ganor 2009, Horvat 'Etri public-building proposal",
    "JER": "Netzer 1999/2004, Hasmonean Jericho building; identification disputed",
    "THE": "CIJ II 1404 / IAA S 842, Theodotus synagogue inscription",
    "JOS": "Josephus, Life 277–280",
    "NT": "New Testament literary witness",
}

# ko, en, lon, lat, region, grade, basis, period, description, refs, source ids, caution
SITES = [
    ("감라 회당", "Gamla synagogue", 35.7400, 32.9020, "골란", "A", "building",
     "기원전 1세기 말–서기 67년",
     "성벽 가까이의 장방형 건물로 네 면의 계단식 벤치와 내부 열주가 확인되었다. 서기 67년 로마군 함락층이 사용 종료 시점을 고정한다.",
     "요세푸스 『유대 전쟁사』 4권", ["DB", "GAM", "MAG"],
     "요세푸스는 감라를 서술하지만 이 건물을 회당이라고 직접 지목하지는 않는다."),
    ("막달라 회당군", "Magdala synagogues", 35.5169, 32.8247, "갈릴리", "A", "building",
     "기원전 1세기 중엽–서기 1세기 후반",
     "2009년 발굴 회당은 벤치·프레스코·모자이크와 성전 기물이 새겨진 막달라 돌을 갖추었다. 2021년에는 같은 도시의 다른 구역에서 두 번째 제2성전기 회당이 확인되었다.",
     "막 15:40", ["MIG", "MIG2", "MAG"],
     "복음서는 예수께서 이 특정 건물에서 가르치셨다고 말하지 않는다. 점은 2009년 발굴지를 대표한다."),
    ("마사다 회당", "Masada synagogue", 35.3540, 31.3150, "유대 광야", "A", "building",
     "서기 66–73/74년 회당 단계",
     "헤롯 궁전·요새의 기존 공간을 제1차 유대전쟁 중 회당으로 개조했다. 벽면 벤치와 게니자에서 나온 성서 두루마리 조각이 기능 판정의 핵심이다.",
     "요세푸스 『유대 전쟁사』 7권", ["MAS", "MAG"],
     "예수 공생애기의 회당 건물이 아니라 서기 66년 이후 개조 단계다."),
    ("헤로디온 회당", "Herodium synagogue", 35.2410, 31.6660, "유대", "A", "building",
     "서기 66–71년 회당 단계",
     "헤롯 시대 접견 공간으로 보이는 방을 제1차 유대전쟁 때 벤치가 둘린 집회 공간으로 개조했다.",
     "요세푸스 『유대 전쟁사』 1권", ["HER", "DB", "MAG"],
     "예수 공생애기부터 사용된 회당이 아니라 전쟁기 전용 단계다."),
    ("움 엘우므단 회당", "Khirbet Umm el-'Umdan synagogue", 34.99785, 31.88338, "모디인 인근", "A", "building",
     "하스몬기–서기 2세기 초; 제2성전기 단계 포함",
     "여러 건축 단계와 삼면 벤치, 인접 미크베가 조사된 마을 회당이다. 후기 제2성전기까지 이어진 단계가 확인된다.",
     "마카베오상 2:1", ["UMM", "MAG"],
     "고대 모디인과의 정확한 동일시는 논쟁 중이며 회당 판정과 도시 동일시를 분리해야 한다."),
    ("키르벳 바드 이사 회당", "Khirbet Badd 'Isa / Qiryat Sefer synagogue", 35.04232, 31.92651, "베냐민", "A", "building",
     "후기 제2성전기–바르코크바 전후",
     "중앙 열주와 삼면 벤치를 갖춘 농촌 정착지의 공공 집회 건물로 발굴되었다. 회당 판정은 널리 수용되지만 사용 단계는 서기 70년 전후를 걸친다.",
     "", ["QIR", "DB", "MAG"], "서기 1세기 한 시점의 단일 건축 단계로 단순화하지 않는다."),
    ("텔 레케쉬 회당", "Tel Rekhesh synagogue", 35.46614, 32.65345, "하부 갈릴리", "A", "building",
     "서기 1세기; 서기 70년 이전",
     "농촌 정착지의 현무암·석회암 건물로 벽면 벤치와 내부 열주가 확인되었다. 토기와 동전이 서기 1세기 사용을 지지한다.",
     "마 4:23", ["REK", "MAG"],
     "마태복음의 여러 회당을 보여 주는 비교 자료이지 본문 속 특정 회당으로 동일시된 것은 아니다."),
    ("가버나움 회당 후보", "Capernaum synagogue candidate", 35.5750, 32.8808, "갈릴리", "B", "site",
     "현존 건물은 후기 로마기; 하부 단계 연대 논쟁",
     "현재 보이는 흰 석회암 회당은 대체로 후기 로마기에 속한다. 아래 현무암 벽과 바닥을 1세기 회당으로 연결하는 견해가 있으나 층위와 기능 해석에 이견이 크다.",
     "막 1:21; 눅 7:5", ["CAP", "DB", "MAG"],
     "흰 회당 자체를 예수께서 가르치신 1세기 건물로 표시해서는 안 된다."),
    ("호르밧 에트리 회당 후보", "Horvat 'Etri synagogue candidate", 34.97201, 31.64947, "유대 구릉", "B", "building",
     "후기 제2성전기–바르코크바기",
     "마을의 공공 건물에 벤치와 회당으로 해석되는 요소가 있으나 건물 기능과 정확한 사용 단계가 확정적이지 않다.",
     "", ["ETR", "MAG"], "확인된 서기 70년 이전 회당 목록과 동일한 등급으로 세지 않는다."),
    ("여리고 하스몬 궁전 회당 후보", "Jericho Hasmonean synagogue candidate", 35.43508, 31.85350, "여리고", "B", "building",
     "기원전 75–50년경 제안",
     "하스몬 궁전 단지의 장방형 건물을 발굴자는 초기 회당으로 해석했다. 그러나 연회·접견 공간 등 다른 기능 해석이 있다.",
     "", ["JER", "MAG"], "세계에서 가장 오래된 회당처럼 확정적으로 서술하지 않는다."),
    ("예루살렘 회당·테오도투스 비문", "Jerusalem synagogue / Theodotus inscription", 35.2354, 31.7784, "예루살렘", "C", "findspot",
     "후기 제2성전기",
     "테오도투스 비문은 율법 낭독·계명 교육과 순례자 숙박을 위한 회당 및 부속시설을 명시한다. 비문은 오벨에서 발견되었지만 원래 건물의 정확한 자리는 확인되지 않았다.",
     "행 6:9", ["THE", "MAG"], "점은 비문 발견권의 대표 위치이며 회당 건물 좌표가 아니다."),
    ("나사렛 회당 문헌 위치", "Nazareth synagogue literary location", 35.2978, 32.7019, "갈릴리", "C", "site",
     "서기 1세기 문헌 증언",
     "누가복음은 예수께서 안식일에 나사렛 회당에서 이사야서를 읽으셨다고 전한다. 현재까지 그 1세기 회당 건물은 확인되지 않았다.",
     "눅 4:16-30", ["NT"], "점은 고대 나사렛 취락 대표점이지 회당 발굴점이 아니다."),
    ("디베랴 프로슈케 문헌 위치", "Tiberias proseuche literary location", 35.5312, 32.7959, "갈릴리", "C", "site",
     "서기 1세기 문헌 증언",
     "요세푸스는 서기 66년 디베랴에서 많은 사람이 모인 큰 프로슈케를 언급한다. 회당 또는 기도처로 해석되지만 건물은 확인되지 않았다.",
     "요세푸스 『자서전』 277–280", ["JOS", "MAG"],
     "프로슈케와 회당 건물의 관계를 단정하지 않으며 점은 도시 대표점이다."),
]


def main():
    features = []
    for ko, en, lon, lat, region, grade, basis, period, desc, refs, source_ids, caution in SITES:
        label, criterion = GRADE[grade]
        props = {
            "ko": ko, "en": en, "region": region, "grade": grade,
            "confidence": label, "criterion": criterion,
            "coordinate_basis": basis, "period": period, "desc": desc,
            "sources": " · ".join(SOURCES[s] for s in source_ids),
            "caution": caution,
        }
        if refs:
            props["refs"] = refs
        features.append({"type": "Feature", "properties": props,
                         "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    collection = {
        "type": "FeatureCollection",
        "attribution": "Kinneret College Bornblum database · Magness 2024 · excavation publications and literary witnesses",
        "note": "장소 단위 13곳. A/B/C는 1세기 회당 건물에 대한 증거 유형과 확실성을 나타낸다.",
        "evidence_model": {g: GRADE[g][1] for g in GRADE},
        "features": features,
    }
    OUT.write_text(json.dumps(collection, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {g: sum(f["properties"]["grade"] == g for f in features) for g in GRADE}
    print(f"{len(features)}곳 · {counts}")


if __name__ == "__main__":
    main()
