#!/usr/bin/env node
// 서기 30년경 성경 지리권과 대한민국 동일 면적 영역의 넓이를 잰다.
//
//   node scripts/calculate-area-comparison.mjs
//
// 넓이는 서로 근거가 다른 두 방식으로 재고 차이를 함께 찍는다. 화면 픽셀로 환산해
// 재지 않는다.
//   1) EPSG:6933 — WGS84 람베르트 정적 원통(표준위선 30°N)으로 투영한 뒤 평면 신발끈.
//      정적 도법이라 투영 평면의 넓이가 곧 타원체 위의 넓이다.
//   2) 등적 반지름 구면 위의 구면 다각형 넓이 (Chamberlain–Duquette).
// 구멍(안쪽 고리)은 빼고, MultiPolygon 은 조각마다 더한다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const A = 6378137.0, F = 1 / 298.257223563;
const E2 = F * (2 - F), E = Math.sqrt(E2);
const R_AUTHALIC = 6371007.181;                     // m · WGS84 등적 반지름
const D2R = Math.PI / 180;

const qOf = phi => {
  const s = Math.sin(phi);
  return (1 - E2) * (s / (1 - E2 * s * s) - (1 / (2 * E)) * Math.log((1 - E * s) / (1 + E * s)));
};
const LAT_TS = 30 * D2R;
const K0 = Math.cos(LAT_TS) / Math.sqrt(1 - E2 * Math.sin(LAT_TS) ** 2);

function ringArea6933(ring) {
  const p = ring.map(([lon, lat]) => [A * K0 * lon * D2R, A * qOf(lat * D2R) / (2 * K0)]);
  let s = 0;
  for (let i = 0; i < p.length - 1; i++) s += p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1];
  return s / 2;
}
function ringAreaSphere(ring) {
  let s = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [l1, p1] = ring[i], [l2, p2] = ring[i + 1];
    s += (l2 - l1) * D2R * (2 + Math.sin(p1 * D2R) + Math.sin(p2 * D2R));
  }
  return s * R_AUTHALIC * R_AUTHALIC / 2;
}
const close = r => (r[0][0] === r.at(-1)[0] && r[0][1] === r.at(-1)[1]) ? r : [...r, r[0]];

function area(geom, fn) {
  const polys = geom.type === 'Polygon' ? [geom.coordinates]
              : geom.type === 'MultiPolygon' ? geom.coordinates : [];
  let total = 0;
  for (const poly of polys) poly.forEach((ring, i) => {
    total += (i === 0 ? 1 : -1) * Math.abs(fn(close(ring)));   // 첫 고리가 겉, 나머지는 구멍
  });
  return total / 1e6;                                          // km²
}
export const areaKm2 = geom => ({ epsg6933: area(geom, ringArea6933), sphere: area(geom, ringAreaSphere) });

function line(label, geom) {
  const { epsg6933, sphere } = areaKm2(geom);
  const pct = Math.abs(epsg6933 - sphere) / epsg6933 * 100;
  console.log(`${label.padEnd(34)} ${epsg6933.toFixed(1).padStart(10)} km²   (구면 ${sphere.toFixed(1)} · 차이 ${pct.toFixed(3)}%)`);
  return epsg6933;
}
const read = p => JSON.parse(readFileSync(join(ROOT, p), 'utf8'));
const merge = fc => ({ type: 'MultiPolygon', coordinates: fc.features.flatMap(f =>
  f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates) });

console.log('■ 검산 — 위도 30~31 · 경도 35~36 의 1°×1° (참값 약 10,645 km²)');
line('1°×1°', { type: 'Polygon', coordinates: [[[35,30],[36,30],[36,31],[35,31],[35,30]]] });

console.log('\n■ 서기 30년경 유대·갈릴리 전체 성경 지리권');
const hist = line('복원 바깥 경계', merge(read('data/judea-c30-boundary.geojson')));
const ev = read('data/judea-c30-evidence.json');
console.log(`  ${ev.area.headline.display}`);
console.log(`  ${ev.area.headline.caveat}`);
for (const [k, v] of Object.entries(ev.regions_km2)) if (k !== 'note')
  console.log(`   · ${k.padEnd(8)} ${String(v).padStart(6)} km²`);

console.log('\n■ 대한민국 동일 면적 영역');
const cmp = read('data/korea-area-comparison.json');
const sel = cmp.selection;
console.log(`  ${sel.regions.join(' + ')} = ${sel.sum_km2.toLocaleString()} km²  (공식 통계 합)`);
console.log(`  목표 ${cmp.target_km2.toLocaleString()} km² 대비 오차 ${sel.error_pct > 0 ? '+' : ''}${sel.error_pct}%`
          + (Math.abs(sel.error_pct) <= 1 ? '  → ±1% 이내 PASS' : '  → ±1% 초과 FAIL'));
line('그리기용 폴리곤(NE 1:10m)', merge(read('data/korea-equal-area.geojson')));
console.log('  ※ 폴리곤은 1:10m 일반화본이라 통계보다 작다. 표시 숫자는 공식 통계를 쓴다.');
console.log(`\n  국토 대비 ${cmp.feel.share_of_korea_pct}% · 서울 ${cmp.feel.times_seoul}배 · 제주 ${cmp.feel.times_jeju}배`);
console.log(`  뻗은 모양: 성경 지리권 남북 ${ev.extent.north_south_km} × 동서 ${ev.extent.east_west_max_km} km`
          + ` ↔ 한국 영역 남북 ${sel.extent.north_south_km} × 동서 ${sel.extent.east_west_max_km} km`);
