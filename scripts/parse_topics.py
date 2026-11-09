#!/usr/bin/env python3
"""정보관리기술사 토픽 PDF -> 단어장 데이터(JSON) 파서.

사용법:
  python3 scripts/parse_topics.py SOURCE.pdf --domain NW --out _data/nw.json
  python3 scripts/parse_topics.py SOURCE.txt --domain DB --out _data/db.json   # pdftotext -layout 결과

전제(현재 기술사 스터디 PDF 양식):
  * 앞쪽 '목록' 페이지에 `NW_001_제목 ······ 1` 형태의 목차가 있음
  * 각 토픽 첫 페이지에 '토픽 이름 / 분류 / 키워드(암기) / 암기법(해당경우) / 기출문제' 헤더 표가 있음
  * 본문은 'I. ...', 'II. ...' 섹션과 '- ' 불릿으로 구성

결과 JSON 각 항목: id, code, title, domain, category, definition, keywords[], sections[{title, subsections[{title|null, items[]}]}],
dueum(원문 '암기법' 칸에 값이 있을 때만), pages[start,end], questions[], warnings[], outline[](목차)
검토 필드(overrides에서만): review[] = '[A]/[B]/[C]/[D] ...' 형식의 검토 메모 (A 사실오류·B 최신화·C 모호·D 파싱깨짐)
같은 id에 대해 `_data/overrides/<domain>.json` 이 있으면 해당 필드를 덮어씀(수동 보정용).
"""
import argparse, json, os, re, subprocess, sys

ROMAN = r'(?:I{1,3}|IV|V|VI{0,3}|IX|X|Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ)'
SEC_RE = re.compile(r'^\s*(' + ROMAN + r'|\d{1,2})\s*[\.\)]\s*(\S.*)$')
SUB_RE = re.compile(r'^\s*([가-하])\s*[\.\)]\s*(\S.*)$')
BULLET_RE = re.compile(r'^\s*(?:[-–•▪◦∙·－]\.?\s*|o\s+|\d\)\s+|\.\s+)(\S.*)$')
HDR_RE = re.compile(r'토픽\s*이름')
LABELS = [('category', r'분\s*류'), ('keywords', r'(?:키워드(?:\s*\(암기\))?|주요\s*키워드)'), ('dueum', r'암기법(?:\s*\(해당\s*경우\))?')]
END_MARK = re.compile(r'^\s*["“”\']?\s*끝\s*["“”\']?\s*$')


def load_pages(src):
    if src.lower().endswith('.pdf'):
        txt = subprocess.run(['pdftotext', '-layout', src, '-'], capture_output=True, text=True).stdout
    else:
        txt = open(src, encoding='utf-8').read()
    return txt.split('\f')


def norm(s):
    s = s.replace('\u00a0', ' ').replace('’', "'").replace('‘', "'")
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_toc(pages, domain):
    toc = []
    rx = re.compile(r'^\s*(' + re.escape(domain) + r'_[0-9][^\n]*?)\s*[·\.…]{3,}\s*(\d+)\s*$')
    for i, p in enumerate(pages[:10]):
        if HDR_RE.search(p):
            break
        for line in p.splitlines():
            m = rx.match(line)
            if m:
                toc.append((m.group(1).strip(), int(m.group(2))))
    return toc


def split_code(raw, domain):
    # NW_004_00_맨체스터 코딩 -> code NW_004_00, title 맨체스터 코딩
    m = re.match(re.escape(domain) + r'_(\d+)(?:_(\d{1,2}))?_(.*)$', raw)
    if not m:
        return raw, raw
    code = f"{domain}_{m.group(1)}" + (f"_{m.group(2)}" if m.group(2) else '')
    return code, m.group(3).strip()


def parse_header(page):
    """레이아웃 텍스트에서 헤더 표 필드를 읽음."""
    out = {'title': '', 'category': '', 'keywords': '', 'dueum': ''}
    lines = page.splitlines()
    cur = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if re.match(r'^기출\s*문제', s) or re.match(r'^번\s*호', s) or SEC_RE.match(s):
            break
        m = HDR_RE.search(s)
        if m and cur is None:
            rest = s[m.end():]
            rest = re.sub(r'^\s*\([^)]{1,6}\)', '', rest).strip()
            out['title'] = rest
            cur = 'title'
            continue
        hit = False
        for key, lab in LABELS:
            mm = re.match(r'^' + lab + r'\s*(.*)$', s)
            if mm:
                cur = key
                out[key] = mm.group(1).strip()
                hit = True
                break
        if hit:
            continue
        if cur in ('keywords', 'category', 'title') and line.startswith(' ' * 8):
            out[cur] = (out[cur] + ' ' + s).strip()
        elif cur == 'dueum' and line.startswith(' ' * 8):
            out['dueum'] = (out['dueum'] + ' ' + s).strip()
        else:
            # 헤더가 끝난 뒤 다른 텍스트(링크 등) -> 중단
            if cur == 'dueum':
                break
    return {k: norm(v) for k, v in out.items()}


def split_keywords(s):
    s = s.strip().strip('"').strip()
    if not s:
        return []
    parts = re.split(r',(?![^()]*\))|，|/(?=\s)|;', s)
    kws = []
    for p in parts:
        p = norm(p).strip(' .,')
        if p and p not in kws:
            kws.append(p)
    return kws


def body_lines(pages_txt):
    """레이아웃 본문 -> 논리 라인. 표 왼쪽 라벨을 버리고, 들여쓰기를 보고 줄바꿈된 불릿을 이어붙임."""
    out = []          # (kind, text)
    bul_col = None    # 현재 불릿 텍스트 시작 컬럼
    for raw in pages_txt.splitlines():
        if not raw.strip():
            continue
        raw = raw.replace('\t', '    ')
        s = raw.strip()
        if END_MARK.match(s):
            out.append(('end', '')); bul_col = None
            continue
        indent = len(raw) - len(raw.lstrip())
        m = SEC_RE.match(s)
        if m and len(s) < 90 and indent < 6:
            out.append(('sec', norm(m.group(2)))); bul_col = None
            continue
        m = SUB_RE.match(s)
        if m and len(s) < 90 and indent < 8:
            out.append(('sub', norm(m.group(2)))); bul_col = None
            continue
        # '라벨      - 불릿' 형태 -> 라벨 제거
        m = re.match(r'^(\s*)(\S.{0,24}?)\s{3,}((?:[-–•▪－]\s*)\S.*)$', raw)
        if m and not BULLET_RE.match(s):
            raw = ' ' * (len(raw) - len(m.group(3))) + m.group(3)
            s = m.group(3).strip()
            indent = len(raw) - len(raw.lstrip())
        m = BULLET_RE.match(s)
        if m:
            text = m.group(1)
            out.append(('bullet', norm(text)))
            bul_col = indent + (len(s) - len(text))
            continue
        if bul_col is not None and out and out[-1][0] == 'bullet':
            # '라벨      꼬리텍스트' 형태
            m2 = re.match(r'^(\s*)(\S.{0,24}?)\s{3,}(\S.*)$', raw)
            tail_col = None
            if m2 and len(raw) - len(m2.group(3)) >= bul_col - 3:
                tail_col = len(raw) - len(m2.group(3)); tail = m2.group(3)
            elif indent >= bul_col - 3 and not re.search(r'\s{3,}', s):
                tail_col = indent; tail = s
            elif indent < bul_col - 3 and len(s) <= 14:
                continue  # 표 왼쪽 라벨만 있는 줄 -> 무시
            if tail_col is not None and len(tail) < 120:
                prev = out[-1][1]
                if not re.search(r'(\.|다)$', prev):
                    joiner = '' if (re.search(r'[가-힣]$', prev) and re.match(r'^[가-힣]', tail)) else ' '
                    out[-1] = ('bullet', norm(prev + joiner + tail))
                    continue
        out.append(('text', norm(s)))
        bul_col = None
    return out


def clean_title(t):
    t = re.sub(r'\s+', ' ', t).strip(' :-')
    return t


def to_nested(sec):
    """{title, bullets['▸ 소제목', '내용', ...]} -> {title, subsections[{title|None, items[]}]}.
    '▸ '로 시작하는 줄(원문 PDF의 '가./나.'·소제목 레벨)을 소제목으로, 그 뒤 불릿을 하위 항목으로 묶음."""
    if 'subsections' in sec:
        return sec
    subs = []
    for b in sec.get('bullets', []):
        if b.startswith('▸ '):
            subs.append({'title': b[2:].strip(), 'items': []})
        else:
            if not subs:
                subs.append({'title': None, 'items': []})
            subs[-1]['items'].append(b)
    subs = [x for x in subs if x['items'] or x['title']]
    return {'title': sec.get('title', ''), 'subsections': subs}


def build_entry(domain, raw_name, code, toc_title, header_page, body):
    hdr = parse_header(header_page) if header_page else {'title': '', 'category': '', 'keywords': '', 'dueum': ''}
    warnings = []
    if not header_page:
        warnings.append('헤더 표(토픽 이름/키워드) 없음')
    lines = body_lines(body)
    # 기출문제 부분 건너뛰기: 첫 섹션 헤더부터 사용
    first_sec = next((i for i, (k, _) in enumerate(lines) if k == 'sec'), 0)
    content = lines[first_sec:]
    # 정의: 첫 섹션 안에서 '정의/개념' 이 들어간 소제목·라벨 뒤 첫 불릿, 없으면 첫 불릿
    definition = []
    for i, (k, t) in enumerate(content):
        if k == 'sec' and i > 0:
            if definition:
                break
        if k == 'bullet' and len(t) > 15:
            definition.append(t)
            if len(definition) >= 2 or len(' '.join(definition)) >= 45:
                break
    sections = []
    cur = None
    for k, t in content:
        if k == 'end':
            break
        if k == 'sec':
            cur = {'title': clean_title(t), 'bullets': []}
            sections.append(cur)
        elif k == 'sub' and cur is not None and len(cur['bullets']) < 6:
            cur['bullets'].append('▸ ' + clean_title(t))
        elif k == 'bullet' and cur is not None and len(cur['bullets']) < 6:
            if t not in definition and len(t) >= 14 and '개념도' not in t[-4:]:
                cur['bullets'].append(t[:220])
    # 소제목만 있고 내용 없는 꼬리 정리
    for s in sections:
        while s['bullets'] and s['bullets'][-1].startswith('▸ '):
            s['bullets'].pop()
    sections = [s for s in sections if s['bullets'] or len(sections) <= 2][:5]
    sections = [to_nested(x) for x in sections]
    title = hdr['title'] or toc_title
    if not definition:
        warnings.append('정의 불릿 자동 추출 실패')
    entry = {
        'id': code,
        'code': code,
        'title': toc_title,
        'subtitle': title if title != toc_title else '',
        'domain': domain,
        'category': hdr['category'],
        'definition': ' '.join(definition)[:400],
        'keywords': split_keywords(hdr['keywords']),
        'sections': sections,
        'warnings': warnings,
    }
    if hdr['dueum']:
        entry['dueum'] = hdr['dueum']
    if not entry['keywords']:
        warnings.append('원문 키워드 칸 비어 있음')
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--domain', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--overrides', default=None)
    a = ap.parse_args()
    pages = load_pages(a.src)
    toc = parse_toc(pages, a.domain)
    # 전체 텍스트에서 헤더(토픽 이름) 위치를 문자 오프셋으로 찾음 -> 한 페이지에 여러 토픽이 있어도 분리 가능
    offsets, full = [], ''
    for p in pages:
        offsets.append(len(full)); full += p + '\n'
    def page_of(pos):
        lo = 0
        for i, o in enumerate(offsets):
            if o <= pos: lo = i
            else: break
        return lo
    hdr_pos = [m.start() for m in re.finditer(r'(?m)^[ \t]*(?:I\.\s*)?(?:토픽\s*이름|DN-\d+\s)', full)]
    hdr_pos = [p for p in hdr_pos if page_of(p) >= 1 and not re.match(r'\s*목록', full[p:p+10])]
    from collections import Counter
    offs = Counter()
    for _, pg in toc:
        for h in hdr_pos:
            d = page_of(h) - pg
            if 0 <= d <= 6:
                offs[d] += 1
    base_off = offs.most_common(1)[0][0] if offs else 0
    starts, used, last = [], set(), -1
    for name, pg in toc:
        exp = pg + base_off
        cand = [h for h in hdr_pos if h not in used and h > last and exp - 1 <= page_of(h) <= exp + 4]
        if cand:
            h = cand[0]; used.add(h); starts.append((h, True)); last = h
        else:
            h = max(offsets[min(exp, len(offsets) - 1)], last + 1); starts.append((h, False)); last = h
    entries = []
    for idx, ((name, pg), (st, has_hdr)) in enumerate(zip(toc, starts)):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(full)
        code, title = split_code(name, a.domain)
        body = full[st:end]
        e = build_entry(a.domain, name, code, title, body if has_hdr else None, body)
        e['pages'] = [pg, max(pg, page_of(max(st, end - 1)) - base_off)]
        entries.append(e)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ov_path = a.overrides or os.path.join(repo, '_data', 'overrides', a.domain.lower() + '.json')
    if os.path.exists(ov_path):
        ov = json.load(open(ov_path, encoding='utf-8'))
        for e in entries:
            if e['id'] in ov:
                for k, v in ov[e['id']].items():
                    if v is None:
                        e.pop(k, None)
                    else:
                        e[k] = v
                e['reviewed'] = True
                e['warnings'] = [w for w in e['warnings'] if not (('키워드' in w and e.get('keywords')) or ('정의' in w and e.get('definition')))]
    for e in entries:
        e['sections'] = [to_nested(x) for x in e.get('sections', [])]
    # 목차(outline): 섹션 제목 + 섹션 안 '▸' 소제목. 문자열 목록, '- '로 시작하면 하위 항목. overrides의 outline이 있으면 대체.
    for e in entries:
        if 'outline' in e:
            continue
        ol = []
        for s in e.get('sections', []):
            t = re.sub(r'^[\s\.\-·]+', '', s.get('title', '')).rstrip(' .')
            if not t:
                continue
            ol.append(t)
            for ss in s.get('subsections', []):
                sub = (ss.get('title') or '').strip()
                if sub and sub != t:
                    ol.append('- ' + sub)
        e['outline'] = ol
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(entries, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'TOC {len(toc)}개, 헤더 매칭 {sum(1 for s in starts if s[1])}개, 출력 {len(entries)}개 -> {a.out}', file=sys.stderr)
    for e in entries:
        if e['warnings']:
            print('  WARN', e['id'], e['title'], e['warnings'], file=sys.stderr)


if __name__ == '__main__':
    main()
