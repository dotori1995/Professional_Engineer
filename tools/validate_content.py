#!/usr/bin/env python3
"""콘텐츠 품질 검사: 템플릿 문구·제목 번호·중복 정의 등을 잡는다.
사용: python3 tools/validate_content.py [도메인키 ...]   (예: sv sw). 인자 없으면 전체. 실패 시 exit 1."""
import json, re, sys, glob, os
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILLER = re.compile(r'^\s*(핵심:?\s*)?(개념|정의|개념\s*·\s*정의|핵심\s*구성\s*요소|구성\s*요소|핵심\s*기술|활용\s*사례|관련\s*표준(\s*·\s*기법)?|구성\s*·\s*유형|활용\s*·\s*시사점|적용\s*효과|한계\s*·\s*(이슈|주의점)|효과|목적|절차/유형|기법)\s*$')
SEC_FILLER = re.compile(r'^\s*(개념\s*·\s*정의|핵심\s*구성\s*요소|핵심\s*기술|활용\s*사례|관련\s*표준(\s*·\s*기법)?|적용\s*효과|한계\s*·\s*(이슈|주의점)|절차/유형|구성\s*·\s*유형|활용\s*·\s*시사점)\s*$')
ANY_FILLER = re.compile(r'답안\s*구조로\s*정리|표준\s*·\s*비교\s*·\s*한계|(^|\s)(구성|핵심):\s*(핵심|개념)')
TITLE_NUM = re.compile(r'\([A-Z]{2}\s?_?\d')
def texts(x):
    if isinstance(x, str): yield x
    elif isinstance(x, list):
        for i in x: yield from texts(i)
    elif isinstance(x, dict):
        for v in x.values(): yield from texts(v)
def main(keys):
    files = [f'{ROOT}/_data/{k}.json' for k in keys] if keys else sorted(glob.glob(f'{ROOT}/_data/*.json'))
    errs = []; defs = defaultdict(list)
    for f in files:
        try: d = json.load(open(f))
        except Exception: continue
        if not isinstance(d, list): continue
        for t in d:
            tid = t.get('id'); title = t.get('title') or t.get('name') or ''
            if TITLE_NUM.search(title): errs.append(f'{tid}: 제목에 번호 "{title}"')
            m = re.match(r'^(.+?)\((.+)\)$', title.strip())
            if m and m.group(1).strip().replace(' ', '').lower() == m.group(2).strip().replace(' ', '').lower():
                errs.append(f'{tid}: 제목 중복 표기 "{title}"')
            if not (t.get('keywords_must') or []): errs.append(f'{tid}: 필수 키워드 없음')
            for fld in ('keywords_must', 'keywords_ref', 'keywords', 'outline', 'sections'):
                for s in texts(t.get(fld)):
                    parts = re.split(r'[·/]', s) + [s] if fld != 'sections' else [s]
                    pat = FILLER if fld != 'sections' else SEC_FILLER
                    for part in parts:
                        if pat.search(part.strip()) or ANY_FILLER.search(s):
                            errs.append(f'{tid}: {fld} 템플릿 문구 "{s[:40]}"'); break
                    else: continue
                    break
            for k in (t.get('keywords_must') or []):
                if len(k) > 60: errs.append(f'{tid}: 키워드가 문장 조각 "{k[:40]}"')
            df = (t.get('definition') or '').strip()
            if df: defs[df].append(tid)
    for df, ids in defs.items():
        if len(ids) > 1: errs.append(f'정의 중복 {ids}: "{df[:40]}"')
    for e in errs: print(e)
    print(f'-- {len(errs)} issue(s)')
    return 1 if errs else 0
if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
