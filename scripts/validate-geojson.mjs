import { readFileSync } from 'node:fs';
const files = ['data/judea-c30-boundary.geojson','data/judea-c30-regions.geojson','data/korea-equal-area.geojson'];
const seg = (a,b,c,d) => {                       // 두 선분이 교차하나
  const o = (p,q,r) => Math.sign((q[1]-p[1])*(r[0]-q[0])-(q[0]-p[0])*(r[1]-q[1]));
  return o(a,b,c)!==o(a,b,d) && o(c,d,a)!==o(c,d,b);
};
let bad = 0;
for (const f of files) {
  const fc = JSON.parse(readFileSync(f,'utf8'));
  let rings=0, pts=0, empty=0, selfx=0, open=0;
  for (const feat of fc.features) {
    const g = feat.geometry;
    const polys = g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[];
    for (const poly of polys) for (const r of poly) {
      rings++; pts+=r.length;
      if (r.length < 4) { empty++; continue; }
      if (r[0][0]!==r.at(-1)[0]||r[0][1]!==r.at(-1)[1]) open++;
      for (let i=0;i<r.length-1;i++) for (let j=i+2;j<r.length-1;j++) {
        if (i===0 && j===r.length-2) continue;
        if (seg(r[i],r[i+1],r[j],r[j+1])) selfx++;
      }
    }
  }
  const ok = empty===0 && selfx===0 && open===0;
  if (!ok) bad++;
  console.log(`${f.padEnd(36)} 고리 ${String(rings).padStart(3)} · 점 ${String(pts).padStart(6)} · 빈고리 ${empty} · 열린고리 ${open} · 자기교차 ${selfx}  ${ok?'OK':'문제'}`);
}
process.exit(bad?1:0);
