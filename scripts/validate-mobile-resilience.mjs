import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const checks = [
  ['터치 판정에 maxTouchPoints 포함',
    /const TOUCH_DEVICE = navigator\.maxTouchPoints > 0/],
  ['메모리 미보고 모바일을 저전력으로 처리',
    /const LOW_POWER = TOUCH && \(saveData \|\| !memoryKnown/],
  ['모바일 픽셀 상한 단일 적용',
    /const want = gestureBusy \? 1 : Math\.min\(window\.devicePixelRatio \|\| 1, pixelRatioCap\)/],
  ['육지 DEM 소스 한 벌만 선언',
    /terrain:\s*\{ type: 'raster-dem'/],
  ['고도색이 terrain 소스 공유',
    /id: 'relief', type: 'color-relief', source: 'terrain'/],
  ['음영이 terrain 소스 공유',
    /id: 'hillshade', type: 'hillshade', source: 'terrain'/],
  ['3D terrain 은 0단계에서만 붙인다',
    /\.\.\.\(TERRAIN_ON \? \{ terrain: \{ source: 'terrain'/],
  ['터치 기기 기본 안전 단계는 2',
    /return TOUCH \? 2 : 0;/],
  ['2단계에서 DEM 소스를 스타일에서 뺀다',
    /delete style\.sources\.terrain;/],
  ['2단계에서 DEM 을 쓰는 레이어를 걸러낸다',
    /style\.layers = style\.layers\.filter\(l => l\.source !== 'terrain' && l\.source !== 'bathy'\)/],
  ['죽은 자리 기록을 남긴다',
    /localStorage\.setItem\(DIAG_ALIVE, '1'\)/],
  ['URL 해시를 단계 범위로 정규화',
    /const HASH_MAX_ZOOM = FLAT_MAP \? 14 :/],
  ['안전 단계에서 생성자 기울기 0도',
    /pitch: SAFE_LEVEL > 0 \? 0 : 50/],
  ['모바일 hillshade 초기 비표시',
    /layout: \{ visibility: TOUCH \? 'none' : 'visible' \}/],
  ['MapLibre 버전 고정',
    /maplibre-gl@6\.9\.0\/dist\/maplibre-gl\.mjs/],
  ['TerrainControl 은 0단계에서만 붙인다',
    /if \(TERRAIN_ON\) map\.addControl\(new maplibregl\.TerrainControl/],
  ['WebGL 컨텍스트 손실 복구',
    /addEventListener\('webglcontextlost'/],
  ['비정상 세션 자동 복구',
    /recoverFromCrash = Boolean/],
  ['백그라운드 렌더 중단',
    /document\.addEventListener\('visibilitychange'/],
];

let failed = 0;
for (const [name, pattern] of checks) {
  const ok = pattern.test(html);
  console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}`);
  if (!ok) failed++;
}

const landDemDeclarations = (html.match(/type: 'raster-dem', tiles: \[LAND_DEM\]/g) || []).length;
const duplicateLandSource = /\bland:\s*\{\s*type: 'raster-dem'/.test(html);
const stalePixelReset = /gestureBusy \? 1 : Math\.min\(window\.devicePixelRatio \|\| 1, 2\)/.test(html);

if (landDemDeclarations !== 1) {
  console.log(`FAIL 육지 DEM 선언 수=${landDemDeclarations} (기대값 1)`);
  failed++;
}
if (duplicateLandSource) {
  console.log('FAIL 중복 land DEM 소스가 남아 있음');
  failed++;
}
if (stalePixelReset) {
  console.log('FAIL 제스처 종료 시 픽셀 배율 2 복귀 경로가 남아 있음');
  failed++;
}

if (failed) process.exit(1);
console.log('PASS 모바일 안정성 정적 회귀 검사');
