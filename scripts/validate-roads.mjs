#!/usr/bin/env node
// 도로 자료가 스스로 근거를 갖추고 있는지 본다.
//
//   node scripts/validate-roads.mjs
//
// 좌표와 Evidence 가 따로 놀지 않도록, 출처 없는 선과 연대 근거 없는 서기 30년 구간을 막는다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const road = JSON.parse(readFileSync(join(ROOT, 'data/roads-c30.geojson'), 'utf8'));
const ev   = JSON.parse(readFileSync(join(ROOT, 'data/roads-c30-evidence.json'), 'utf8'));

const fail = [], warn = [];
const check = (ok, msg) => { if (!ok) fail.push(msg); };

// 1) GeoJSON 형식
check(road.type === 'FeatureCollection', 'FeatureCollection 이 아니다');
check(Array.isArray(road.features) && road.features.length > 0, 'feature 가 없다');

// 2) ID 고유성 · 좌표 범위 · 빈 선 금지
const ids = new Set();
let pts = 0, empty = 0, dup = 0, oob = 0;
const BOX = [32.0, 28.0, 39.0, 35.0];                 // 이번 시범이 다루는 범위
for (const f of road.features) {
  const p = f.properties;
  if (ids.has(p.id)) { dup++; fail.push(`중복 id: ${p.id}`); }
  ids.add(p.id);
  const parts = f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [f.geometry.coordinates];
  for (const line of parts) {
    if (!line || line.length < 2) { empty++; continue; }
    for (const c of line) {
      pts++;
      if (c[0] < BOX[0] || c[0] > BOX[2] || c[1] < BOX[1] || c[1] > BOX[3]) oob++;
    }
  }
}
check(empty === 0, `점이 2개 미만인 선 ${empty}개`);
check(dup === 0, `중복 id ${dup}개`);
check(oob === 0, `범위를 벗어난 좌표 ${oob}개`);

// 3) 출처 없는 도로 금지 · Evidence 의 source id 와 일치
const evSources = new Set(ev.sources.map(s => s.id));
const evRoads = new Map(ev.roads.map(r => [r.id, r]));
const evLater = new Map(ev.later.map(r => [r.id, r]));
const roadIds = new Set(road.features.map(f => f.properties.roadId));
for (const f of road.features) {
  const p = f.properties;
  check(Array.isArray(p.sourceIds) && p.sourceIds.length > 0, `출처 없는 구간: ${p.id}`);
  for (const s of p.sourceIds || []) check(evSources.has(s), `Evidence 에 없는 출처 ${s} (${p.id})`);
  check(typeof p.license === 'string' && p.license.length > 0, `라이선스 표기 없음: ${p.id}`);
  // 4) 서기 30년 구간은 연대 근거가 있어야 한다
  if (p.activeC30) {
    const r = evRoads.get(p.roadId);
    check(!!r, `Evidence 에 없는 도로: ${p.roadId}`);
    check(r && typeof r.c30Basis === 'string' && r.c30Basis.length > 20,
          `서기 30년 연대 근거가 없다: ${p.roadId}`);
    // 5) 후대 도로가 기준 층에 섞이지 않았는지
    check(p.periodStart == null || p.periodStart <= 30,
          `기준 층에 후대 도로가 섞였다: ${p.roadId} (${p.periodStart}년)`);
    check(p.routeType !== 'later', `기준 층에 later 유형이 섞였다: ${p.id}`);
  } else {
    check(evLater.has(p.roadId), `Evidence 의 later 목록에 없다: ${p.roadId}`);
    check(typeof p.periodStart === 'number' && p.periodStart > 30,
          `후대 도로인데 연대가 서기 30년 이후가 아니다: ${p.roadId}`);
  }
  check(['confirmed', 'probable', 'hypothetical'].includes(p.certainty), `확실성 값 이상: ${p.id}`);
}
// 6) Evidence 에만 있고 자료에 없는 도로
for (const id of [...evRoads.keys(), ...evLater.keys()])
  check(roadIds.has(id), `Evidence 에만 있고 선이 없는 도로: ${id}`);

const c30 = road.features.filter(f => f.properties.activeC30);
const later = road.features.filter(f => !f.properties.activeC30);
console.log(`도로 ${roadIds.size}개 · 구간 ${road.features.length}개 (서기 30년 ${c30.length} · 후대 ${later.length}) · 점 ${pts}개`);
console.log(`출처 ${ev.sources.length}개 · 보류(HOLD) ${ev.hold.length}건`);
const mix = {};
for (const f of c30) mix[f.properties.certainty] = (mix[f.properties.certainty] || 0) + 1;
console.log('서기 30년 구간 확실성:', JSON.stringify(mix));
if (warn.length) console.log('경고:\n  ' + warn.join('\n  '));
if (fail.length) { console.log('FAIL\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('RESULT: PASS');
