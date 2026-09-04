#!/usr/bin/env python3
"""
전지구 자연색 베이스 타일 생성기
================================
NASA Blue Marble Next Generation(트루컬러 위성 합성, 퍼블릭 도메인)의
21600x10800 등장방형 이미지를 Web Mercator XYZ 타일로 자른다.

고도 램프만으로는 위도·강수 차이를 표현할 수 없어 지구 전체 뷰에서
콩고 분지와 유럽까지 사막색이 된다. 저줌 구간만 실제 위성색으로 덮는다.

  python bake/world.py --src bake/world-src/bluemarble.jpg --out world --zoom 0 5

의존성은 numpy 와 pillow 뿐이다. 등장방형 → 메르카토르 변환은 경도가 선형이라
'세로 방향 재표본' 하나로 끝나므로 GDAL/rasterio 가 필요 없다.

출처: NASA Earth Observatory, Blue Marble Next Generation (Visible Earth). 퍼블릭 도메인.
"""
import argparse, math, time
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
TILE = 512


def mercator_row_map(world_px, src_h):
    """메르카토르 세로 픽셀 -> 등장방형 소스 행(실수). 위도 매핑이 비선형인 부분이 여기다."""
    v = (np.arange(world_px, dtype=np.float64) + 0.5) / world_px      # 0..1
    lat = np.arctan(np.sinh(np.pi * (1 - 2 * v)))                     # rad
    return (90.0 - np.degrees(lat)) / 180.0 * src_h - 0.5


def build(src_path, out_dir, z0, z1, quality):
    src = Image.open(src_path).convert('RGB')
    print(f'소스 {src.size[0]}x{src.size[1]}')
    total = 0
    for z in range(z0, z1 + 1):
        world = TILE * 2 ** z
        if world > src.size[0]:
            print(f'  z{z}: 소스 해상도({src.size[0]}px)를 넘어 건너뜀')
            continue
        t0 = time.time()
        # 가로는 경도가 선형이라 폭만 맞추면 타일 열이 그대로 대응한다.
        # LANCZOS 로 먼저 줄여야 저줌에서 계단현상이 생기지 않는다.
        img = np.asarray(src.resize((world, world // 2), Image.LANCZOS), dtype=np.float32)
        rows = mercator_row_map(world, img.shape[0])
        r0 = np.clip(np.floor(rows), 0, img.shape[0] - 1).astype(np.int32)
        r1 = np.clip(r0 + 1, 0, img.shape[0] - 1)
        frac = (rows - r0).astype(np.float32)[:, None, None]

        n = 2 ** z
        for x in range(n):
            col = img[:, x * TILE:(x + 1) * TILE, :]
            for y in range(n):
                s = slice(y * TILE, (y + 1) * TILE)
                tile = col[r0[s]] * (1 - frac[s]) + col[r1[s]] * frac[s]
                dst = Path(out_dir, str(z), str(x), f'{y}.webp')
                dst.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(np.clip(tile, 0, 255).astype(np.uint8), 'RGB').save(
                    dst, 'WEBP', quality=quality, method=4)
                total += 1
        print(f'  z{z}: {n * n:,}장  ({time.time() - t0:.1f}s)')
    print(f'완료: {total:,}장 → {out_dir}/{{z}}/{{x}}/{{y}}.webp')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--src', required=True)
    p.add_argument('--out', default='world')
    p.add_argument('--zoom', nargs=2, type=int, default=[0, 5])
    p.add_argument('--quality', type=int, default=80)
    a = p.parse_args()
    build(a.src, a.out, a.zoom[0], a.zoom[1], a.quality)
