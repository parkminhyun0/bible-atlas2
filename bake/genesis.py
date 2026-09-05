#!/usr/bin/env python3
"""창세기 인물 동선 정의 → 지형 최소비용경로로 GeoJSON 생성."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import routes as R

P = {  # 지점 좌표 (지명 데이터와 같은 값)
 "에덴(아르메니아설)":(41.00,39.00), "놋 땅":(47.80,31.60), "에녹 성":(45.996,30.816), "아라랏":(44.30,39.70),
 "시날(바벨)":(44.42,32.54), "우르":(46.103,30.962), "하란":(39.03,36.86),
 "세겜":(35.283,32.213), "벧엘":(35.22,31.93), "브엘세바":(34.79,31.25),
 "고센":(31.80,30.70), "헤브론":(35.0998,31.5326), "소돔":(35.40,31.10),
 "단":(35.652,33.249), "호바":(36.10,33.75), "살렘":(35.2354,31.7784),
 "그랄":(34.55,31.40), "모리아":(35.2354,31.7780), "브엘라해로이":(34.60,30.85),
 "르호봇":(34.70,31.20), "길르앗 산":(35.85,32.40), "마하나임":(35.68,32.20),
 "브니엘":(35.65,32.19), "숙곳":(35.62,32.20), "에브랏":(35.2024,31.7054),
 "도단":(35.20,32.42), "아닷 타작마당":(35.55,31.85), "네게브":(34.90,30.95),
}
# (id, 인물, 제목, 성경, 확실성, [지점...])
#   attested     본문이 지명과 이동을 함께 밝힘        → 실선
#   inferred     지명은 있으나 경로·중간지가 추정      → 파선
#   hypothetical 지점 자체가 학설·미상                 → 점선
ROUTES = [
 ("adam","아담·하와","에덴에서 쫓겨나다","창 3:23-24","hypothetical",["에덴(아르메니아설)","놋 땅"]),
 ("cain","가인","놋 땅으로 가 에녹 성을 세우다","창 4:16-17","hypothetical",["에덴(아르메니아설)","놋 땅","에녹 성"]),
 ("noah","노아 후손","아라랏에서 시날로","창 8:4·11:2","hypothetical",["아라랏","시날(바벨)"]),
 ("terah","데라","우르에서 하란으로","창 11:31","inferred",["우르","하란"]),
 ("abram1","아브람","하란에서 가나안으로","창 12:4-9","attested",["하란","세겜","벧엘","네게브"]),
 ("abram2","아브람","기근에 애굽으로","창 12:10-13:1","inferred",["네게브","고센"]),
 ("abram3","아브람","롯과 갈라서다","창 13:10-18","attested",["벧엘","소돔"]),
 ("abram4","아브람","롯을 구하러 북진","창 14:14-17","attested",["헤브론","단","호바","살렘"]),
 ("abr5","아브라함","그랄에 머물다","창 20:1-21:34","attested",["헤브론","그랄","브엘세바"]),
 ("isaac1","아브라함·이삭","모리아 산으로","창 22:1-19","attested",["브엘세바","모리아"]),
 ("servant","아브라함의 종","리브가를 데리러","창 24","inferred",["브엘세바","하란"]),
 ("isaac2","이삭","그랄에서 브엘세바로","창 26","attested",["브엘라해로이","그랄","르호봇","브엘세바"]),
 ("jacob1","야곱","도피, 하란으로","창 28:10-29:1","attested",["브엘세바","벧엘","하란"]),
 ("jacob2","야곱","귀환","창 31-35","attested",["하란","길르앗 산","마하나임","브니엘","숙곳","세겜","벧엘","에브랏","헤브론"]),
 ("joseph","요셉","형들에게 팔리다","창 37:12-36","attested",["헤브론","세겜","도단","고센"]),
 ("jacob3","야곱 일가","애굽으로 내려가다","창 46:1-7","attested",["헤브론","브엘세바","고센"]),
 ("burial","장례 행렬","야곱을 막벨라에 묻다","창 50:7-13","inferred",["고센","아닷 타작마당","헤브론"]),
]

def main(out):
    feats, total = [], 0.0
    for rid, who, title, ref, cert, stops in ROUTES:
        print(f'{rid:9} {who} — {title}')
        coords, dist_km, hours = [], 0.0, 0.0
        for i in range(len(stops) - 1):
            a, b = P[stops[i]], P[stops[i+1]]
            print(f'    {stops[i]} → {stops[i+1]}')
            pts, km, hrs = R.leg(a, b)
            if coords and pts and coords[-1] == list(pts[0]): pts = pts[1:]
            coords += [list(p) for p in pts]
            dist_km += km; hours += (hrs or 0)
        total += dist_km
        feats.append({"type":"Feature",
            "properties":{"id":rid,"who":who,"title":title,"ref":ref,"certainty":cert,
                          "stops":" → ".join(stops),"km":round(dist_km),
                          "walk_h":round(hours) if hours else None},
            "geometry":{"type":"LineString","coordinates":coords}})
        print(f'    합계 {dist_km:.0f} km · 점 {len(coords)}')
    p = pathlib.Path(out)
    p.write_text(json.dumps({"type":"FeatureCollection","features":feats},
                            ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    print(f'\n{len(feats)}개 동선 · 총 {total:.0f} km · {p.stat().st_size/1024:.0f} KB → {out}')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/genesis-routes.geojson')
