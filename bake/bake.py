#!/usr/bin/env python3
"""
bible-atlas2 텍스처 베이킹 파이프라인
=====================================
ESA WorldCover(10 m 토지피복) + Copernicus GLO-30(30 m DEM)을 합쳐
"고대 위성지도" 풍의 지표 텍스처를 XYZ WebP 타일(512px)로 굽는다.
건물·도로·국경·지명은 애초에 넣지 않는다. 물은 투명(alpha=0)으로 남겨
런타임의 해저 깊이색·호수 레이어가 그대로 비치게 한다.

사용법
------
  python bake.py download --bbox 8 20 56 46 --out data
  python bake.py bake     --data data --out tiles --zoom 4 10 --bbox 8 20 56 46 --workers 8
  python bake.py preview  --data data --lon 35.5 --lat 32.8 --zoom 9   # 타일 1장만 PNG로 확인

준비
----
  pip install rasterio numpy pillow requests
  (rasterio 휠에 GDAL이 포함되어 있어 별도 GDAL 설치가 필요 없다)

데이터 출처 (모두 무료·키 불필요)
--------------------------------
  WorldCover 2021 v200 (3°×3° COG):
    https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{N30E033}_Map.tif
    라이선스 CC BY 4.0 — 표기: "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021)"
  Copernicus GLO-30 (1°×1° COG):
    https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{N30_00_E033_00}_DEM/Copernicus_DSM_COG_10_{N30_00_E033_00}_DEM.tif
    표기: "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA"
  두 URL 패턴은 각 프로젝트의 공개 버킷 규칙을 따른 것이며, 첫 실행 때 404가 나오면 파일명 규칙이 바뀐 것이니
  버킷 인덱스에서 실제 이름을 확인해 URL_WC / URL_DEM 만 고치면 된다.
"""
import argparse
import math
import os
import sys
from pathlib import Path

import numpy as np

# ------------------------------------------------------------------
# 1. 색상 팔레트 — 여기만 바꾸면 화풍이 바뀐다
# ------------------------------------------------------------------
# WorldCover 클래스 코드 → 기본색 (RGB 0-255)
WC_COLORS = {
    10: (58, 96, 52),     # 수목  tree cover
    20: (128, 138, 84),   # 관목  shrubland
    30: (165, 168, 108),  # 초지  grassland
    40: (178, 170, 112),  # 농경지 cropland (고대 지도이므로 초지에 가깝게)
    50: (150, 140, 120),  # 건조지(도시) → 나지처럼 처리
    60: None,             # 나지  bare/sparse → 고도·경사로 모래/암석 분리 (아래)
    70: (246, 248, 250),  # 눈·빙하
    80: None,             # 영구 수역 → 투명
    90: (120, 140, 110),  # 습지
    95: (90, 120, 90),    # 맹그로브
    100: (150, 150, 130), # 이끼·지의류
}
SAND = np.array([214, 196, 150], np.float32)   # 저지·완경사 나지
ROCK = np.array([140, 122, 102], np.float32)   # 고지·급경사 나지
SNOW = np.array([246, 248, 250], np.float32)
SNOW_LINE = 2500.0                             # m, 이 위는 눈 (WorldCover 눈 클래스와 별개로 고도 기준 추가)
SNOW_BLEND = 400.0                             # 설선 위 몇 m에 걸쳐 흰색으로 섞을지

# ------------------------------------------------------------------
# 2. 순수 numpy 렌더링 코어 (rasterio 없이도 테스트 가능)
# ------------------------------------------------------------------
def hillshade(dem, res_m, azimuth=315.0, altitude=45.0):
    """DEM(m) → 0..1 음영. res_m: 픽셀 한 변의 지상 길이(m)."""
    dem = np.nan_to_num(dem.astype(np.float32), nan=0.0)
    gy, gx = np.gradient(dem, res_m)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, al = math.radians(azimuth), math.radians(altitude)
    hs = math.sin(al) * np.cos(slope) + math.cos(al) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1), np.degrees(slope)


def render(lc, dem, res_m):
    """
    lc  : (H,W) uint8 WorldCover 클래스
    dem : (H,W) float32 고도(m), 바다/결측은 0 또는 NaN
    반환: (H,W,4) uint8 RGBA
    """
    H, W = lc.shape
    rgb = np.zeros((H, W, 3), np.float32)
    alpha = np.full((H, W), 255, np.uint8)

    dem = np.nan_to_num(dem.astype(np.float32), nan=0.0)
    hs, slope_deg = hillshade(dem, res_m)

    # 2-1) 클래스별 기본색
    for code, col in WC_COLORS.items():
        m = lc == code
        if not m.any():
            continue
        if code == 80:                       # 수역 → 투명
            alpha[m] = 0
            continue
        if code in (60, 50):                 # 나지: 모래 ↔ 암석
            # 고도 700 m 이하 & 경사 8° 이하 = 모래, 그 위로 갈수록 암석
            t_e = np.clip((dem[m] - 400.0) / 1200.0, 0, 1)
            t_s = np.clip((slope_deg[m] - 4.0) / 14.0, 0, 1)
            t = np.maximum(t_e, t_s)[:, None]
            rgb[m] = SAND * (1 - t) + ROCK * t
            continue
        rgb[m] = np.array(col, np.float32)

    # 2-2) 고도에 따른 은근한 색 변화 (같은 클래스도 높을수록 탁하고 붉게)
    t_h = np.clip(dem / 3000.0, 0, 1)[..., None]
    tint = np.array([150, 130, 110], np.float32)
    rgb = rgb * (1 - 0.25 * t_h) + tint * (0.25 * t_h)

    # 2-3) 설선: 고도 기준 눈 (수역 제외)
    t_snow = np.clip((dem - SNOW_LINE) / SNOW_BLEND, 0, 1)[..., None]
    rgb = rgb * (1 - t_snow) + SNOW * t_snow

    # 2-4) 음영 곱하기 (너무 어둡지 않게 0.55~1.15 범위)
    shade = (0.55 + 0.6 * hs)[..., None]
    rgb = rgb * shade

    # 2-5) 결측(클래스 0) → 투명
    alpha[lc == 0] = 0

    out = np.empty((H, W, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = alpha
    return out


# ------------------------------------------------------------------
# 3. 타일 수학 (Web Mercator)
# ------------------------------------------------------------------
R = 6378137.0
MAXLAT = 85.05112878

def tile_bounds_3857(z, x, y):
    n = 2 ** z
    size = 2 * math.pi * R / n
    minx = -math.pi * R + x * size
    maxy = math.pi * R - y * size
    return minx, maxy - size, minx + size, maxy

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat = max(min(lat, MAXLAT), -MAXLAT)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y

def tiles_in_bbox(bbox, z):
    w, s, e, n = bbox
    x0, y0 = lonlat_to_tile(w, n, z)
    x1, y1 = lonlat_to_tile(e, s, z)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            yield x, y


# ------------------------------------------------------------------
# 4. 다운로드
# ------------------------------------------------------------------
URL_WC = ('https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'
          'ESA_WorldCover_10m_2021_v200_{tile}_Map.tif')
URL_DEM = ('https://copernicus-dem-30m.s3.amazonaws.com/'
           'Copernicus_DSM_COG_10_{tile}_DEM/Copernicus_DSM_COG_10_{tile}_DEM.tif')

def wc_tile_names(bbox):
    w, s, e, n = bbox
    for lat in range(int(math.floor(s / 3)) * 3, int(math.ceil(n / 3)) * 3, 3):
        for lon in range(int(math.floor(w / 3)) * 3, int(math.ceil(e / 3)) * 3, 3):
            yield f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}{'E' if lon >= 0 else 'W'}{abs(lon):03d}"

def dem_tile_names(bbox):
    w, s, e, n = bbox
    for lat in range(int(math.floor(s)), int(math.ceil(n))):
        for lon in range(int(math.floor(w)), int(math.ceil(e))):
            yield f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}_00_{'E' if lon >= 0 else 'W'}{abs(lon):03d}_00"

def cmd_download(a):
    import requests
    out = Path(a.out); (out / 'wc').mkdir(parents=True, exist_ok=True); (out / 'dem').mkdir(exist_ok=True)
    jobs = [(URL_WC.format(tile=t), out / 'wc' / f'{t}.tif') for t in wc_tile_names(a.bbox)]
    jobs += [(URL_DEM.format(tile=t), out / 'dem' / f'{t}.tif') for t in dem_tile_names(a.bbox)]
    ok = miss = 0
    for url, dst in jobs:
        if dst.exists():
            ok += 1; continue
        r = requests.get(url, stream=True, timeout=120)
        if r.status_code == 404:            # 바다만 있는 칸은 파일이 없다 — 정상
            miss += 1; continue
        r.raise_for_status()
        tmp = dst.with_suffix('.part')
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.rename(dst); ok += 1
        print(f'  ↓ {dst.name}')
    print(f'완료: {ok}개 확보, {miss}개 없음(바다 칸)')


# ------------------------------------------------------------------
# 5. 베이킹 (rasterio)
# ------------------------------------------------------------------
TILE_PX = 512

def _open_sources(data):
    import rasterio
    wc = [rasterio.open(p) for p in sorted(Path(data, 'wc').glob('*.tif'))]
    dem = [rasterio.open(p) for p in sorted(Path(data, 'dem').glob('*.tif'))]
    if not wc or not dem:
        sys.exit('data/wc, data/dem 에 tif가 없습니다. 먼저 download를 실행하세요.')
    return wc, dem

def _read_mosaic(sources, z, x, y, dtype, resampling, fill):
    """타일 영역을 EPSG:3857 512px 격자로 워핑해 읽고, 여러 소스를 겹쳐 합친다."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT
    from rasterio.transform import from_bounds
    from rasterio.warp import transform_bounds
    b = tile_bounds_3857(z, x, y)
    tr = from_bounds(*b, TILE_PX, TILE_PX)
    out = np.full((TILE_PX, TILE_PX), fill, dtype)
    for src in sources:
        sb = transform_bounds(src.crs, 'EPSG:3857', *src.bounds)
        if sb[2] <= b[0] or sb[0] >= b[2] or sb[3] <= b[1] or sb[1] >= b[3]:
            continue
        with WarpedVRT(src, crs='EPSG:3857', transform=tr, width=TILE_PX, height=TILE_PX,
                       resampling=resampling, nodata=fill) as v:
            arr = v.read(1)
        m = arr != fill
        out[m] = arr[m]
    return out

def bake_tile(sources, z, x, y):
    from rasterio.enums import Resampling
    wc, dem = sources
    lc = _read_mosaic(wc, z, x, y, np.uint8, Resampling.mode, 0)
    if not lc.any():
        return None
    el = _read_mosaic(dem, z, x, y, np.float32, Resampling.bilinear, np.float32(np.nan))
    el = np.nan_to_num(el, nan=0.0)
    # 픽셀 지상 길이(m): Mercator 축척 보정 (타일 중심 위도 기준)
    minx, miny, maxx, maxy = tile_bounds_3857(z, x, y)
    lat_c = math.degrees(2 * math.atan(math.exp((miny + maxy) / 2 / R)) - math.pi / 2)
    res_m = (maxx - minx) / TILE_PX * math.cos(math.radians(lat_c))
    return render(lc, el, res_m)

def _worker(args):
    data, out, z, x, y = args
    global _SRC
    if '_SRC' not in globals():
        _SRC = _open_sources(data)
    dst = Path(out, str(z), str(x), f'{y}.webp')
    if dst.exists():
        return 0
    rgba = bake_tile(_SRC, z, x, y)
    if rgba is None or not rgba[..., 3].any():
        return 0
    from PIL import Image
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, 'RGBA').save(dst, 'WEBP', quality=82, method=4)
    return 1

def cmd_bake(a):
    from multiprocessing import Pool
    z0, z1 = a.zoom
    jobs = [(a.data, a.out, z, x, y) for z in range(z0, z1 + 1) for x, y in tiles_in_bbox(a.bbox, z)]
    print(f'타일 {len(jobs):,}장 (z{z0}–z{z1}), 워커 {a.workers}')
    done = 0
    with Pool(a.workers) as pool:
        for i, n in enumerate(pool.imap_unordered(_worker, jobs, chunksize=8), 1):
            done += n
            if i % 200 == 0:
                print(f'  {i:,}/{len(jobs):,} 처리, {done:,}장 저장')
    print(f'완료: {done:,}장 저장 → {a.out}/{{z}}/{{x}}/{{y}}.webp')

def cmd_preview(a):
    x, y = lonlat_to_tile(a.lon, a.lat, a.zoom)
    rgba = bake_tile(_open_sources(a.data), a.zoom, x, y)
    if rgba is None:
        sys.exit('해당 위치에 데이터가 없습니다.')
    from PIL import Image
    Image.fromarray(rgba, 'RGBA').save('preview.png')
    print(f'preview.png 저장 (z{a.zoom} x{x} y{y})')


# ------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('download'); d.add_argument('--bbox', nargs=4, type=float, required=True, metavar=('W', 'S', 'E', 'N'))
    d.add_argument('--out', default='data'); d.set_defaults(fn=cmd_download)
    b = sub.add_parser('bake'); b.add_argument('--data', default='data'); b.add_argument('--out', default='tiles')
    b.add_argument('--zoom', nargs=2, type=int, default=[4, 9]); b.add_argument('--bbox', nargs=4, type=float, required=True)
    b.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 2) - 1)); b.set_defaults(fn=cmd_bake)
    v = sub.add_parser('preview'); v.add_argument('--data', default='data'); v.add_argument('--lon', type=float, required=True)
    v.add_argument('--lat', type=float, required=True); v.add_argument('--zoom', type=int, default=9); v.set_defaults(fn=cmd_preview)
    a = p.parse_args(); a.fn(a)

if __name__ == '__main__':
    main()
