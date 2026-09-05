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
- 지명: 신약 269곳(`data/nt-places.geojson`, 붉은 점) · 구약 216곳(`data/ot-places.geojson`, 남색 점).
  구약은 성경 이름을 앞에 두고 신약·헬라·고고학 이름을 괄호에 병기한다
  (벧산(스구도볼리) · 므깃도(아마겟돈) · 랍바(빌라델비아) · 갈라(님루드)).
  산은 해발 고도를 함께 적는다 (헤르몬산(시룐·스닐, 2,814m)).
- 위치 확실성: Barrington Atlas · Pleiades 관행을 따른다.
  확정 ● 속 채운 점 · 유력하나 미확정 ○ 빈 점 · 추정 ○ 빈 점 + 이름 뒤 물음표.
  점을 누르면 근거를 볼 수 있다. 에덴은 학설 4곳을 모두 추정으로 표시한다.
  도시·마을·요새는 점, 산은 산 모양 아이콘, 바다·강·지역은 라벨만.
  등급 1~5 로 노출 줌을 나눈다(z5.5~z9.5). 등급은 줌별로 라벨 62px 이 겹치지
  않을 최소 간격을 계산해 자동 조정한다.
- 지형 가림: 눕혀서 가까이 보면 산 뒤의 지명을 숨긴다. MapLibre 는 지형 가림을
  하지 않으므로, 카메라에서 지명까지 시선을 그어 중간 지형이 넘는지 직접 판정한다.
- 패널: 데스크톱은 왼쪽 손잡이로 밀어 넣고, 모바일은 바텀시트로 올린다.
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
