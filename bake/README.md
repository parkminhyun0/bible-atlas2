# bible-atlas2 · 지표 텍스처 베이킹

실제 토지피복(ESA WorldCover 10 m)과 DEM(Copernicus GLO-30)으로
"고대 위성지도" 풍의 지표 텍스처를 구워 3D 지형 위에 입힌다.
건물·도로·국경·지명은 포함하지 않는다. 물은 투명하게 남겨 뷰어의 해저 깊이색이 비친다.

## 1. 준비 (Mac, 한 번만)

```bash
cd bible-atlas2
python3 -m venv .venv && source .venv/bin/activate
pip install rasterio numpy pillow requests
```

## 2. 데이터 내려받기 (성경 무대 전체: 경도 8–56°, 위도 20–46°)

```bash
python bake/bake.py download --bbox 8 20 56 46 --out bake/data
```

- WorldCover 3°×3° 타일 최대 170장, DEM 1°×1° 타일 최대 1,248장. 바다뿐인 칸은 서버에 파일이 없어 404로 건너뛴다(정상).
- 용량은 수십 GB 단위가 될 수 있다. 먼저 작은 영역으로 시험하려면 예: `--bbox 34 29 37 34` (가나안).
- `bake/data/` 는 `.gitignore` 에 넣을 것 (원본은 저장소에 올리지 않는다).

## 3. 한 장 미리보기로 화풍 확인

```bash
python bake/bake.py preview --data bake/data --lon 35.5 --lat 32.8 --zoom 9
open preview.png
```

색이 마음에 안 들면 `bake.py` 상단의 `WC_COLORS`, `SAND`, `ROCK`, `SNOW_LINE` 만 고친다.

## 4. 굽기

```bash
# 시험: 가나안만, z6–z10
python bake/bake.py bake --data bake/data --out tiles --bbox 34 29 37 34 --zoom 6 10 --workers 8

# 전체: z4–z9 (GitHub Pages에 올릴 수 있는 규모)
python bake/bake.py bake --data bake/data --out tiles --bbox 8 20 56 46 --zoom 4 9 --workers 8
```

타일 수(전체 영역 기준): z8 약 800장, z9 약 3,100장, z10 약 12,400장. 이미 있는 타일은 건너뛰므로 중단 후 재실행해도 된다.

## 5. 배포

`tiles/` 폴더를 `index.html` 옆에 두고 커밋하면 뷰어가 `tiles/{z}/{x}/{y}.webp` 를 바로 읽는다.
z10까지 넣어 저장소가 무거워지면 `tiles/` 를 PMTiles 한 파일로 묶어 외부 스토리지(Cloudflare R2 등)에 두는 방식으로 바꾼다.

## 6. 뷰어에서 보이는 것

- 구운 텍스처가 있는 곳: 텍스처가 고도색·OSM 삼림을 대신한다.
- 텍스처가 없는 곳(범위 밖, 아직 안 구운 줌): 고도별 색상이 그대로 보인다.
- 패널의 "구운 지표 텍스처" 체크로 전후를 비교할 수 있다.

## 출처 표기 (뷰어 attribution에 이미 들어 있음)

- © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021), CC BY 4.0
- Copernicus DEM: © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA
