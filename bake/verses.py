"""지명·산 설명에 적어 둔 성경 본문을, 인용에 필요한 절만 뽑아 파일로 만든다.

본문은 『성경전서 개역한글판』. 대한성서공회는 이 판의 저작재산권 보호기간(50년)이
지나 저작권료 없이 쓸 수 있다고 밝히고 있으므로, 출처를 밝히고 본문을 한 글자도
고치지 않는 조건으로 담는다. 널리 쓰이는 개역개정판은 아직 저작권 보호를 받아
담을 수 없다.

출처를 고르며 확인한 것: seven1m/open-bibles 의 kor OSIS 와
m0ty/bible-io-json 의 kor-krv-1938 은 둘 다 빠지거나 어긋난 절이 있었다
(역대하 26장이 통째로 없거나, 26:10·32:30·35:20 이 모두 같은 엉뚱한 본문을 돌려줌).
getbible.net v2 의 korean 은 장별 절 수가 맞아 이것을 쓴다.

사용법:  python3 bake/verses.py data/verses.json data/*.geojson
"""
import json, pathlib, re, subprocess, sys, time

# 한국어 약어 → (책 번호, 표준 이름)
BOOKS = {
 '창':1,'출':2,'레':3,'민':4,'신':5,'수':6,'삿':7,'룻':8,'삼상':9,'삼하':10,
 '왕상':11,'왕하':12,'대상':13,'대하':14,'스':15,'느':16,'에':17,'욥':18,'시':19,
 '잠':20,'전':21,'아':22,'사':23,'렘':24,'애':25,'겔':26,'단':27,'호':28,'욜':29,
 '암':30,'옵':31,'욘':32,'미':33,'나':34,'합':35,'습':36,'학':37,'슥':38,'말':39,
 '마':40,'막':41,'눅':42,'요':43,'행':44,'롬':45,'고전':46,'고후':47,'갈':48,'엡':49,
 '빌':50,'골':51,'살전':52,'살후':53,'딤전':54,'딤후':55,'딛':56,'몬':57,'히':58,
 '약':59,'벧전':60,'벧후':61,'요일':62,'요이':63,'요삼':64,'유':65,'계':66,
}
# 긴 약어부터 맞춰야 '삼상' 이 '삼' 으로 잘리지 않는다.
BOOK_RE = '|'.join(sorted(BOOKS, key=len, reverse=True))
PART_RE = re.compile(rf'^\s*(?:({BOOK_RE})\s+)?(\d+):([\d,\s\-]+)\s*$')
CACHE = pathlib.Path('/tmp/getbible-korean')


def chapter(book, ch):
    """장 하나를 받아 {절 번호: 본문} 으로 돌려준다. 한 번 받은 장은 캐시에서 읽는다."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f'{book}-{ch}.json'
    if not f.exists():
        url = f'https://api.getbible.net/v2/korean/{book}/{ch}.json'
        r = subprocess.run(['curl', '-s', '--max-time', '30', url], capture_output=True, text=True)
        f.write_text(r.stdout, encoding='utf-8')
        time.sleep(0.1)
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        f.unlink()
        return {}
    return {int(v['verse']): ' '.join(v['text'].split()) for v in d.get('verses', [])}


def expand(ref):
    """'창 12:5-7; 17:8' → [('창', 12, 5), ('창', 12, 6), ('창', 12, 7), ('창', 17, 8)]
    앞부분에 책 이름이 없으면 바로 앞의 책을 잇는다."""
    out, book = [], None
    for part in ref.split(';'):
        m = PART_RE.match(part)
        if not m:
            return None
        if m.group(1):
            book = m.group(1)
        if not book:
            return None
        ch = int(m.group(2))
        for span in m.group(3).split(','):
            span = span.strip()
            if not span:
                continue
            if '-' in span:
                a, b = span.split('-', 1)
                if not (a.strip().isdigit() and b.strip().isdigit()):
                    return None
                out += [(book, ch, v) for v in range(int(a), int(b) + 1)]
            elif span.isdigit():
                out.append((book, ch, int(span)))
            else:
                return None
    return out


def collect(paths):
    refs = set()
    for p in paths:
        for f in json.loads(pathlib.Path(p).read_text(encoding='utf-8'))['features']:
            r = (f['properties'].get('refs') or '').strip()
            if r:
                refs.add(r)
    return sorted(refs)


def main(out_path, data_paths):
    table, skipped, missing = {}, [], []
    cache = {}
    for ref in collect(data_paths):
        # '참조' 꼬리표와 '성경에 …' 같은 안내문은 인용할 절이 없다.
        body = ref.replace('참조', '').strip()
        if body.startswith('성경'):
            continue
        verses = expand(body)
        if verses is None:
            skipped.append(ref)
            continue
        groups, book = [], None
        for seg in body.split(';'):
            seg = seg.strip()
            part = expand(seg if PART_RE.match(seg).group(1) else f'{book} {seg}')
            book = PART_RE.match(seg).group(1) or book
            rows = []
            for bk, ch, v in part:
                key = (BOOKS[bk], ch)
                if key not in cache:
                    cache[key] = chapter(*key)
                text = cache[key].get(v)
                if text:
                    rows.append([f'{bk} {ch}:{v}', text])
                else:
                    missing.append(f'{bk} {ch}:{v}')
            if rows:
                groups.append({'r': seg if PART_RE.match(seg).group(1) else f'{book} {seg}', 'v': rows})
        if groups:
            table[ref] = groups
    p = pathlib.Path(out_path)
    p.write_text(json.dumps(table, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'참조 {len(table)}개 · 절 {sum(len(g["v"]) for gs in table.values() for g in gs)}개 · '
          f'받은 장 {len(cache)}개 → {p.name} ({p.stat().st_size/1024:.0f} KB)')
    if skipped:
        print('해석 못한 참조:', ' | '.join(skipped[:10]))
    if missing:
        print('본문에 없는 절:', ' '.join(missing[:10]))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
