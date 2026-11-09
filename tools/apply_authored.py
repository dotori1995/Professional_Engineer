#!/usr/bin/env python3
"""Apply hand-authored topic content (compact text format) to _data/<domain>.json and overrides.

Format (one topic per block):
  #ID 제목(English) | en
  = 정의 문장
  라벨: 필수1 | 필수2 | 필수3      (필수 키워드 묶음; 칩으로도 사용)
  + 참고1 | 참고2 | ...            (참고 키워드)
  두음: XXX                        (선택, 실제 통용 두음만)
  I 섹션 제목
  - 소제목: 항목1 ; 항목2 ; 항목3
목차(outline)는 섹션 제목과 소제목으로 자동 생성.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROMAN = re.compile(r'^(I|II|III|IV)\s+(.*)$')

def parse(text):
    topics, cur = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('//'):
            continue
        if line.startswith('#'):
            head = line[1:]
            tid, rest = head.split(' ', 1)
            name, _, en = rest.partition('|')
            cur = {'id': tid, 'name': name.strip(), 'en': en.strip(), 'groups': [], 'ref': [], 'sections': [], 'dueum': None}
            topics[tid] = cur
        elif line.startswith('='):
            cur['definition'] = line[1:].strip()
        elif line.startswith('+'):
            cur['ref'] += [x.strip() for x in line[1:].split('|') if x.strip()]
        elif line.startswith('두음:'):
            cur['dueum'] = line[3:].strip()
        elif ROMAN.match(line):
            cur['sections'].append({'title': ROMAN.match(line).group(2).strip(), 'subsections': []})
        elif line.startswith('- '):
            body = line[2:]
            title, sep, items = body.partition(':')
            if not sep:
                raise ValueError(f"{cur['id']}: subsection needs ':' -> {line}")
            cur['sections'][-1]['subsections'].append({'title': title.strip(), 'items': [x.strip() for x in items.split(' ; ') if x.strip()]})
        elif ':' in line:
            label, _, items = line.partition(':')
            cur['groups'].append((label.strip(), [x.strip() for x in items.split('|') if x.strip()]))
        else:
            raise ValueError(f"{cur['id'] if cur else '?'}: cannot parse line -> {line}")
    return topics

def build(t):
    must = [k for _, g in t['groups'] for k in g]
    outline = []
    for s in t['sections']:
        outline.append(s['title'])
        outline += ['- ' + ss['title'] for ss in s['subsections']]
    return {
        'name': t['name'], 'title': t['name'], 'en': t['en'] or t['name'],
        'definition': t['definition'],
        'keywords': [f"{lab}: " + ' · '.join(g) for lab, g in t['groups']],
        'keywords_must': must, 'keywords_ref': t['ref'],
        'outline': outline, 'sections': t['sections'],
        'dueum': t['dueum'], 'curated': True, 'reviewed': True, 'quiz_terms': must,
        'keywords_note': None, 'note': None, 'review': None,
    }

def main():
    domain = sys.argv[1].lower()
    files = sys.argv[2:]
    topics = {}
    for f in files:
        topics.update(parse(Path(f).read_text(encoding='utf-8')))
    dpath = ROOT / '_data' / f'{domain}.json'
    opath = ROOT / '_data' / 'overrides' / f'{domain}.json'
    data = json.loads(dpath.read_text(encoding='utf-8'))
    ov = json.loads(opath.read_text(encoding='utf-8')) if opath.exists() else {}
    ids = {x['id'] for x in data}
    unknown = set(topics) - ids
    if unknown:
        sys.exit(f'unknown ids: {sorted(unknown)}')
    for x in data:
        if x['id'] in topics:
            b = build(topics[x['id']])
            for k, v in b.items():
                if v is None:
                    x.pop(k, None)
                else:
                    x[k] = v
            x.pop('quiz_avoid', None)
            o = ov.setdefault(x['id'], {})
            o.update(b)
            o.pop('quiz_avoid', None)
    dpath.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    opath.write_text(json.dumps(ov, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'applied {len(topics)} topics to {domain}')

if __name__ == '__main__':
    main()
