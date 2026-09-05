# bible-atlas2

성경 무대(고대근동·이집트·가나안·바울 선교지)의 3D 지형 지도.
위성 이미지 대신 실제 고도·수심·토지피복 데이터로 "일반 지도" 형식의 입체 지형을 그린다.

- 뷰어: https://parkminhyun0.github.io/bible-atlas2/
- 지형: Mapterhorn(Copernicus DEM 기반) · 수심: Mapzen/AWS Terrain Tiles(ETOPO1)
- 전지구 자연색: NASA Blue Marble Next Generation (2004-08), z0–5 (`bake/world.py`)
- 물·국경: OpenFreeMap(OpenStreetMap) · 지표 텍스처: ESA WorldCover 2021 + Copernicus GLO-30 (`bake/` 참고)
- 엔진: MapLibre GL JS 6 (globe 투영, 3D terrain, color-relief, 다중 광원 음영)
- 배경: 줌에 따라 우주(별) → 고고도 하늘 → 낮 하늘로 이어진다

## 구조

```
index.html        뷰어 (단일 파일, 빌드 없음)
bake/world.py     전지구 자연색 베이스 타일 생성기 (numpy+pillow만 필요)
bake/bake.py      근동 지표 텍스처 베이킹 파이프라인 (rasterio 필요)
bake/README.md    베이킹 사용법
world/            전지구 자연색 타일 z0–5 (14 MB, 커밋됨)
tiles/            구운 근동 텍스처 타일 (bake 산출물, {z}/{x}/{y}.webp)
```

## 조작

- 한 손가락 드래그: 이동 · 두 손가락 좌우/상하: 회전/기울기 · 핀치: 확대/축소
- 패널: 지형 과장, 설선, 구운 텍스처·산림·음영·국경 표시
- 태양·시간대: 현지 태양시 슬라이더로 태양 고도·방위를 계산해 음영과 하늘색을 바꾼다.
  저정밀 USNO 공식 (예루살렘 하지 정오 81.6°, 동지 34.8° — 천문값과 일치)
- 지명: 신약 84곳 (`data/nt-places.geojson`). 붉은 점 + 한글 라벨.
  등급 1~5 로 노출 줌을 나눠(z5.5~z9.5) 넓게 볼 때 겹치지 않게 한다.
  구약 지명은 다음 단계.
- 방위 기준: 북쪽 위(현대) · 동쪽 위(구약 히브리어) · 자전축 23.44° 기울기 · 남쪽 위(아폴로 17 원본)
  중심과 축척은 그대로 두고 '위쪽'만 바꾸므로, 같은 땅이 기준에 따라 어떻게 달라 보이는지 비교된다.

## 전지구 자연색 베이스 다시 만들기

```bash
curl -L -o bake/world-src/bluemarble.jpg \
  https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73776/world.topo.bathy.200408.3x21600x10800.jpg
python3 bake/world.py --src bake/world-src/bluemarble.jpg --out world --zoom 0 5
```

28 MB 내려받아 22초면 1,365장(14 MB)이 나온다. `rasterio`/GDAL 이 필요 없다 —
등장방형에서 메르카토르로 가는 변환은 경도가 선형이라 세로 재표본 하나로 끝난다.

월별 합성본을 바꾸려면 URL 의 `200408` 과 레코드 번호만 바꾼다.
`73909/…200412` 는 12월본인데, 북반구 적설이 지형을 덮어 8월본을 골랐다.
