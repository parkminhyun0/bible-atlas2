# bible-atlas2

성경 무대(고대근동·이집트·가나안·바울 선교지)의 3D 지형 지도.
위성 이미지 대신 실제 고도·수심·토지피복 데이터로 "일반 지도" 형식의 입체 지형을 그린다.

- 뷰어: https://parkminhyun0.github.io/bible-atlas2/
- 지형: Mapterhorn(Copernicus DEM 기반) · 수심: Mapzen/AWS Terrain Tiles(ETOPO1)
- 물·국경: OpenFreeMap(OpenStreetMap) · 지표 텍스처: ESA WorldCover 2021 + Copernicus GLO-30 (`bake/` 참고)
- 엔진: MapLibre GL JS 6 (globe 투영, 3D terrain, color-relief)

## 구조

```
index.html        뷰어 (단일 파일, 빌드 없음)
bake/bake.py      지표 텍스처 베이킹 파이프라인
bake/README.md    베이킹 사용법
tiles/            구운 텍스처 타일 (bake 산출물, {z}/{x}/{y}.webp)
```

## 조작

- 한 손가락 드래그: 이동 · 두 손가락 좌우/상하: 회전/기울기 · 핀치: 확대/축소
- 패널: 지형 과장, 설선, 구운 텍스처·산림·음영·국경 표시
