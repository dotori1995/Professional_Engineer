#!/usr/bin/env python3
"""콘텐츠 품질 검사: 템플릿 문구·제목 번호·중복 정의·빈약한 키워드/목차를 잡는다.
사용: python3 tools/validate_content.py [도메인키 ...]   (예: sv sw). 인자 없으면 전체. 실패 시 exit 1."""
import json, re, sys, glob, os
from collections import defaultdict, Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILLER = re.compile(r'^\s*(핵심:?\s*)?(개념|정의|개념\s*·\s*정의|핵심\s*구성\s*요소|구성\s*요소|핵심\s*기술|활용\s*사례|관련\s*표준(\s*·\s*기법)?|구성\s*·\s*유형|활용\s*·\s*시사점|적용\s*효과|한계\s*·\s*(이슈|주의점)|효과|목적|절차/유형|기법)\s*$')
SEC_FILLER = re.compile(r'^\s*(개념\s*·\s*정의|핵심\s*구성\s*요소|핵심\s*기술|활용\s*사례|관련\s*표준(\s*·\s*기법)?|적용\s*효과|한계\s*·\s*(이슈|주의점)|절차/유형|구성\s*·\s*유형|활용\s*·\s*시사점)\s*$')
ANY_FILLER = re.compile(r'답안\s*구조로\s*정리|표준\s*·\s*비교\s*·\s*한계|(^|\s)(구성|핵심):\s*(핵심|개념)')
TITLE_NUM = re.compile(r'\([A-Z]{2}\s?_?\d')
# Outline sub-items that are ONLY these bare labels (with optional leading "- ")
OL_BARE = re.compile(r'^\s*-?\s*(정의|필요성|특징|핵심\s*요소|유형\s*·\s*동작|목적|구성\s*요소|한계|효과)\s*$')
# Generic short keywords (whole token)
GENERIC_KW = re.compile(r'^(AI|AX|ICT|IT|FMS|Service|PC|OS|HTML|WWW|SV|CDN|JSON|API|SW|HW|UI|UX|DB|NW|SE|PM|MG)$', re.I)
# Fragment definitions
FRAG_DEF = re.compile(r'^(Mass\s|소품종|→)|다루는\s*토픽|디지털서비스\s*영역')
KW_HEADING = re.compile(r'의\s*(정의|특징|개요|배경|등장|필요성|구성요소|기대효과)|(개요|배경|특징)$')
BANNED = ['다루는 핵심', '핵심 암기 포인트', '핵심 기술 요소', '계층·모듈 배치', '요점', '시험 답안', '- -', '디지탈']
KW_DEF_PHRASE = re.compile(r'(위한\s+오픈소스|오케스트레이션\s*플랫폼$|^오픈소스\s)')

def texts(x):
    if isinstance(x, str): yield x
    elif isinstance(x, list):
        for i in x: yield from texts(i)
    elif isinstance(x, dict):
        for v in x.values(): yield from texts(v)

def name_bases(title):
    title = (title or '').strip()
    bases = {title}
    m = re.match(r'^(.+?)\((.+)\)$', title)
    if m:
        bases.add(m.group(1).strip())
        bases.add(m.group(2).strip())
    # strip spaces for compare
    return {re.sub(r'\s+', '', b).lower() for b in bases if b}

def main(keys):
    files = [f'{ROOT}/_data/{k}.json' for k in keys] if keys else sorted(glob.glob(f'{ROOT}/_data/*.json'))
    errs = []; defs = defaultdict(list); dom_descs = defaultdict(list)
    for f in files:
        file_descs = defaultdict(set)
        try: d = json.load(open(f))
        except Exception: continue
        if not isinstance(d, list): continue
        for t in d:
            tid = t.get('id'); title = t.get('title') or t.get('name') or ''
            if TITLE_NUM.search(title): errs.append(f'{tid}: 제목에 번호 "{title}"')
            m = re.match(r'^(.+?)\((.+)\)$', title.strip())
            if m and m.group(1).strip().replace(' ', '').lower() == m.group(2).strip().replace(' ', '').lower():
                errs.append(f'{tid}: 제목 중복 표기 "{title}"')
            must = t.get('keywords_must') or []
            if not must: errs.append(f'{tid}: 필수 키워드 없음')
            if must and (len(must) < 6 or len(must) > 12):
                errs.append(f'{tid}: 필수 키워드 개수 {len(must)} (6–10 권장, 허용 6–12)')
            bases = name_bases(title)
            for fld in ('keywords_must', 'keywords_ref'):
                for k in (t.get(fld) or []):
                    if KW_HEADING.search(k) or KW_DEF_PHRASE.search(k):
                        errs.append(f'{tid}: {fld}가 목차/정의 문구 "{k[:40]}"')
            for k in must:
                if len(k) > 55: errs.append(f'{tid}: 키워드가 문장 조각 "{k[:40]}"')
                kk = re.sub(r'\s+', '', k).lower()
                kb = re.sub(r'\s+', '', re.sub(r'\([^)]*\)', '', k)).lower()
                if kk in bases or kb in bases:
                    errs.append(f'{tid}: 필수 키워드가 토픽명과 동일 "{k}"')
                if GENERIC_KW.match(k.strip()) or GENERIC_KW.match(re.sub(r'\([^)]*\)', '', k).strip()):
                    errs.append(f'{tid}: 너무 일반적 필수 키워드 "{k}"')
            for fld in ('keywords_must', 'keywords_ref', 'keywords', 'outline', 'sections'):
                for s in texts(t.get(fld)):
                    parts = re.split(r'[·/]', s) + [s] if fld != 'sections' else [s]
                    pat = FILLER if fld != 'sections' else SEC_FILLER
                    for part in parts:
                        if pat.search(part.strip()) or ANY_FILLER.search(s):
                            errs.append(f'{tid}: {fld} 템플릿 문구 "{s[:40]}"'); break
                    else: continue
                    break
            for s in (t.get('outline') or []):
                if OL_BARE.match(s.strip()):
                    errs.append(f'{tid}: outline 빈약한 소항목 "{s}"')
            df = (t.get('definition') or '').strip()
            if not df: errs.append(f'{tid}: 정의 없음')
            elif len(df) < 35: errs.append(f'{tid}: 정의가 너무 짧음')
            elif FRAG_DEF.search(df): errs.append(f'{tid}: 정의가 조각/템플릿 "{df[:40]}"')
            if df: defs[df].append(tid)
            # sections substance
            secs = t.get('sections') or []
            items = sum(len(ss.get('items') or []) for s in secs for ss in (s.get('subsections') or []))
            if items < 4: errs.append(f'{tid}: 자세히 항목 부족 ({items})')
            # (b) banned template phrases anywhere in the topic
            hit = set()
            for s in texts(t):
                for b in BANNED:
                    if b in s and b not in hit:
                        hit.add(b); errs.append(f'{tid}: 금지 문구 "{b}" in "{s[:40]}"')
            # section description quality
            descs = []
            for s in secs:
                for ss in (s.get('subsections') or []):
                    for it in (ss.get('items') or []):
                        if '시험 답안' in it:
                            errs.append(f'{tid}: 섹션 템플릿 문구 "{it[:40]}"')
                        if ':' in it:
                            descs.append(it.split(':', 1)[1].strip())
                        else:
                            descs.append(it.strip())
            # (a) description repeated 3+ in a topic
            for d, c in Counter(descs).items():
                if d and c >= 3:
                    errs.append(f'{tid}: 설명 반복 {c}회 "{d[:40]}"')
                    break
            # collect domain-level descs
            for d in descs:
                if d: dom_descs[d].append(tid); file_descs[d].add(tid)
            # (d) outline must not repeat the topic title / its expansion
            # Flag only the full Korean topic name or the full English name.
            # Abbreviations (MOLAP, gRPC, COCOMO II, RPO, QA) are allowed in sub-headings.
            tb = set()
            def _abbr(x):
                if re.search(r'[가-힣]', x): return False
                toks = x.split()
                return bool(toks) and all(sum(c.isupper() for c in w) >= 2 or re.fullmatch(r'[0-9IVXx.+/-]+', w) for w in toks)
            kor = re.sub(r'\(.*\)', '', title).strip()
            cands = [kor, (t.get('en') or '').strip()]
            for inner in re.findall(r'\(([^()]*)\)', title):
                cands += [x.strip() for x in re.split(r',\s*', inner)]
            for x in cands:
                if not x or _abbr(x): continue
                x = re.sub(r'\s+', '', x).lower()
                if len(x) >= 2: tb.add(x)
            # whole-name match: not glued to a longer Hangul compound (표본오차, 이산확률분포 are distinct terms)
            # A repeat = the whole name at the heading start, or followed by a particle/generic heading word.
            # Names inside a longer term (표본오차, 로지스틱 회귀분석) are not repeats.
            GEN = r'(?:의|와|과|\s*(?:정의|특징|개념|개요|필요성|목적|효과|구성|한계|유형|비교|종류|절차|활용|동작|원리|기술|장단점|등장))'
            tbre = []
            for b in tb:
                core = r'\s*'.join(map(re.escape, b))
                tbre.append((b, re.compile(r'^(?:[IVX]+\.\s*)?-?\s*' + core + r'(?![가-힣])|^(?:[IVX]+\.\s*)?-?\s*' + core + GEN + r'|(?<![가-힣])' + core + GEN + r'(?![가-힣])', re.I)))
            for o in (t.get('outline') or []):
                hitb = [b for b, rx in tbre if rx.search(o)]
                if hitb: errs.append(f'{tid}: outline에 토픽명 반복 "{o[:40]}" ({hitb[0]})')
            # (c) outline length / glued
            for o in (t.get('outline') or []):
                if len(o) > 45:
                    errs.append(f'{tid}: outline 과장 "{o[:40]}" ({len(o)}자)')
                if re.search(r'[가-힣][A-Za-z]|개요[가-힣A-Za-z]|정의[가-힣A-Za-z]|특징[가-힣A-Za-z]', o):
                    errs.append(f'{tid}: outline 붙음 "{o[:40]}"')
        # same description in 3+ topics of one domain = template text
        for d, ids in file_descs.items():
            if len(ids) >= 3 and len(d) >= 8:
                errs.append(f'설명 3개+ 토픽 반복 {len(ids)}개 "{d[:40]}" (예: {sorted(ids)[:3]})')
    # (a) description repeated 20+ in a domain
    for d, ids in dom_descs.items():
        if len(ids) >= 20:
            errs.append(f'도메인 설명 반복 {len(ids)}회 "{d[:40]}" (예: {ids[0]})')
    for df, ids in defs.items():
        if len(ids) > 1: errs.append(f'정의 중복 {ids}: "{df[:40]}"')
    for e in errs: print(e)
    print(f'-- {len(errs)} issue(s)')
    return 1 if errs else 0
if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
