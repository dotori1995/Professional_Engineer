#!/usr/bin/env python3
"""Curate SV topics from PDF raw parse + enrichment. Usage:
  python3 scripts/curate_sv_batch.py [--limit N] [--offset N] [--ids SV_002,SV_003]
Writes/updates _data/overrides/sv.json keys and rebuilds those entries in _data/sv.json.
"""
from __future__ import annotations
import argparse, json, re, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OV_PATH = ROOT / '_data' / 'overrides' / 'sv.json'
SV_PATH = ROOT / '_data' / 'sv.json'

ID_MAP = {
    'SV_023-027_웹서비스,WDSL,SOAP,UDDI': 'SV_023',
    'SV_250~254_PACS_PHR_EMR_DICOM_OCS': 'SV_250',
    'SV_382-383_자바스크립트-자바스크립트 프레임워크': 'SV_382',
}

TITLE_FIX = {
    'SV_019_01': ('전자정부 웹사이트 품질관리 지침(e-Government Website Quality Guideline)', 'e-Government Website Quality Guideline'),
    'SV_027_01': ('웹기반 서비스 성능관리(Web Performance Management)', 'Web Performance Management'),
    'SV_030': ('웹 신디케이션(Web Syndication)', 'Web Syndication'),
    'SV_036_2': ('클라우드 관리 플랫폼(CMP, Cloud Management Platform)', 'Cloud Management Platform'),
    'SV_038': ('오픈스택(OpenStack)', 'OpenStack'),
    'SV_041': ('클라우드 스토리지 가상화(Cloud Storage Virtualization)', 'Cloud Storage Virtualization'),
    'SV_053_00': ('멀티클라우드(Multi-Cloud)', 'Multi-Cloud'),
    'SV_055': ('민간 클라우드 이용(Public Cloud Adoption)', 'Public Cloud Adoption'),
    'SV_062': ('클라우드 전환(Cloud Migration)', 'Cloud Migration'),
    'SV_063_00': ('클라우드 보안인증제도(CSAP)', 'Cloud Security Assurance Program'),
    'SV_063_02': ('클라우드 보안기술 표준화(Cloud Security Standardization)', 'Cloud Security Standardization'),
    'SV_068_00': ('클라우드 상호운용성(Cloud Interoperability)', 'Cloud Interoperability'),
    'SV_068_01': ('클라우드 서비스 품질성능(Cloud QoS)', 'Cloud Service Quality'),
    'SV_072': ('상황인식 컴퓨팅(Context-Aware Computing)', 'Context-Aware Computing'),
    'SV_074': ('자율공장(Autonomous Factory)', 'Autonomous Factory'),
    'SV_075': ('인메모리 컴퓨팅(In-Memory Computing)', 'In-Memory Computing'),
    'SV_078': ('앰비언트 컴퓨팅(Ambient Computing)', 'Ambient Computing'),
    'SV_079_0': ('인터미턴트 컴퓨팅(Intermittent Computing)', 'Intermittent Computing'),
    'SV_082': ('스마트시티 통합플랫폼(Smart City Integrated Platform)', 'Smart City Integrated Platform'),
    'SV_083': ('스마트시티 서비스 모델(Smart City Service Model)', 'Smart City Service Model'),
    'SV_095': ('증강현실 유형(AR Types)', 'Augmented Reality Types'),
    'SV_109': ('실감경제(Immersive Economy)', 'Immersive Economy'),
    'SV_125': ('검색엔진(Search Engine)', 'Search Engine'),
    'SV_128': ('에이전트(Agent)', 'Agent'),
    'SV_129': ('지능형 에이전트(Intelligent Agent)', 'Intelligent Agent'),
    'SV_130': ('온톨로지(Ontology)', 'Ontology'),
    'SV_135': ('자연어처리(NLP, Natural Language Processing)', 'Natural Language Processing'),
    'SV_152': ('가상화(Virtualization)', 'Virtualization'),
    'SV_153': ('하이퍼바이저(Hypervisor)', 'Hypervisor'),
    'SV_154': ('서버 가상화(Server Virtualization)', 'Server Virtualization'),
    'SV_155': ('스토리지 가상화(Storage Virtualization)', 'Storage Virtualization'),
    'SV_156': ('데스크톱 가상화(VDI)', 'Desktop Virtualization'),
    'SV_157': ('리눅스 가상화 방식(Linux Virtualization)', 'Linux Virtualization'),
    'SV_158': ('애플리케이션 가상화(Application Virtualization)', 'Application Virtualization'),
    'SV_160': ('하이퍼바이저 유형(Hypervisor Type-1/Type-2)', 'Hypervisor Types'),
    'SV_168': ('전가상화와 반가상화(Full/Para-Virtualization)', 'Full and Para-Virtualization'),
    'SV_169': ('컨버지드 인프라(Converged Infrastructure)', 'Converged Infrastructure'),
    'SV_170': ('클라우드 아키텍처(Cloud Architecture)', 'Cloud Architecture'),
    'SV_185': ('측위기술(Positioning Technology)', 'Positioning Technology'),
    'SV_202': ('오감(Five Senses)', 'Five Senses'),
    'SV_204': ('인더스트리 4.0(Industry 4.0)', 'Industry 4.0'),
    'SV_207': ('스마트팩토리(Smart Factory)', 'Smart Factory'),
    'SV_213': ('포지티브 규제(Positive Regulation)', 'Positive Regulation'),
    'SV_223': ('빌딩 로보틱스(Building Robotics)', 'Building Robotics'),
    'SV_224_00': ('스턱스넷(Stuxnet)', 'Stuxnet'),
    'SV_230': ('페르소나 모형(Persona Model)', 'Persona Model'),
    'SV_231': ('직감기술(Intuitive Interaction)', 'Intuitive Interaction'),
    'SV_255': ('HL7(Health Level 7)', 'Health Level 7'),
    'SV_273_1': ('서비스 로봇(Service Robot)', 'Service Robot'),
    'SV_274': ('로봇 소프트웨어 플랫폼(Robot Software Platform)', 'Robot Software Platform'),
    'SV_275_01': ('메타버스 자율트윈(Metaverse Autonomous Twin)', 'Metaverse Autonomous Twin'),
    'SV_280': ('기술 수명 주기(Technology Life Cycle)', 'Technology Life Cycle'),
    'SV_282': ('가트너 전략기술 동향(Gartner Strategic Technology Trends)', 'Gartner Strategic Technology Trends'),
    'SV_283': ('전문성의 민주화(Democratization)', 'Democratization of Expertise'),
    'SV_285_0': ('초자동화(Hyperautomation)', 'Hyperautomation'),
    'SV_287': ('스마트러닝(Smart Learning)', 'Smart Learning'),
    'SV_295': ('서비타이제이션(Servitization)', 'Servitization'),
    'SV_308': ('블록체인 동향(Blockchain Trends)', 'Blockchain Trends'),
    'SV_311': ('합의 알고리즘(Consensus Algorithm)', 'Consensus Algorithm'),
    'SV_317': ('라이트닝 네트워크(Lightning Network)', 'Lightning Network'),
    'SV_319': ('모바일 신분증(Mobile ID)', 'Mobile ID'),
    'SV_332': ('인포그래픽스(Infographics)', 'Infographics'),
    'SV_333_00': ('디지털 사이니지(Digital Signage)', 'Digital Signage'),
    'SV_339': ('분야별 기능안전 표준(Domain Functional Safety Standards)', 'Functional Safety Standards'),
    'SV_340': ('의료기기 기능안전(Medical Device Functional Safety)', 'Medical Device Functional Safety'),
    'SV_341': ('항공기 기능안전(Airborne Functional Safety)', 'Airborne Functional Safety'),
    'SV_350': ('자율주행 수준분류(SAE J3016 Levels)', 'SAE Autonomous Driving Levels'),
    'SV_355': ('인포테인먼트(Infotainment)', 'Infotainment'),
    'SV_358': ('스마트 머신(Smart Machine)', 'Smart Machine'),
    'SV_363': ('자율주행 인공지능(AI for Autonomous Driving)', 'AI for Autonomous Driving'),
    'SV_364': ('자율주행차 가이드라인(AV Guidelines)', 'Autonomous Vehicle Guidelines'),
    'SV_367': ('바코드(Barcode)', 'Barcode'),
    'SV_369': ('드론(UAV, Drone)', 'Drone'),
    'SV_370': ('안티드론(Anti-Drone)', 'Anti-Drone'),
    'SV_382': ('자바스크립트와 프레임워크(JavaScript Frameworks)', 'JavaScript and Frameworks'),
    'SV_389': ('간편결제(Mobile Simple Payment)', 'Simple Payment'),
    'SV_397': ('OLED(Organic Light-Emitting Diode)', 'Organic Light-Emitting Diode'),
    'SV_400': ('영상처리(Image Processing)', 'Image Processing'),
    'SV_401': ('지능형 영상분석(Intelligent Video Analytics)', 'Intelligent Video Analytics'),
    'SV_405_0': ('360도 카메라(360-Degree Camera)', '360-Degree Camera'),
    'SV_405_1': ('안면인식 결제(Face-Recognition Payment)', 'Face Recognition Payment'),
    'SV_411': ('디지털 노마드(Digital Nomad)', 'Digital Nomad'),
    'SV_412': ('에너지 하베스팅(Energy Harvesting)', 'Energy Harvesting'),
    'SV_416': ('마세라티 문제(Maserati Problem)', 'Maserati Problem'),
    'SV_417_0': ('전자문서 증명서(Electronic Document Certificate)', 'Electronic Document Certificate'),
    'SV_420': ('디지털 역기능(Digital Dysfunction)', 'Digital Dysfunction'),
    'SV_422': ('제론테크놀로지(Gerontechnology)', 'Gerontechnology'),
}

GLOSS = {
    '가상세계': '가상세계(Virtual World)', '증강현실': '증강현실(AR)', '라이프로깅': '라이프로깅(Life Logging)',
    '미러월드': '미러월드(Mirror World)', '아바타': '아바타(Avatar)', '익명성': '익명성(Anonymity)',
    '토르': '토르(Tor)', '쿠키': '쿠키(Cookie)', '세션': '세션(Session)', '인덱싱': '인덱싱(Indexing)',
    '크롤러': '크롤러(Crawler)', '컨테이너': '컨테이너(Container)', '도커': '도커(Docker)',
    '가상화': '가상화(Virtualization)', '마이크로서비스': '마이크로서비스(Microservice)',
    '하이퍼바이저': '하이퍼바이저(Hypervisor)', '온톨로지': '온톨로지(Ontology)',
    '블록체인': '블록체인(Blockchain)', '텔레매틱스': '텔레매틱스(Telematics)',
    '자율주행': '자율주행(Autonomous Driving)', '비동기': '비동기(Asynchronous)',
}

BANNED = {
    '개념·정의', '핵심 기술', '활용 사례', '관련 표준', '구성 요소', '목적', '한계', '효과', '적용',
    '절차/유형', '핵심 구성 요소', '한계·주의점', '관련 표준·기법', '적용 효과', '구성·유형', '활용·시사점',
    '기법', '개념', '정의',
}

def fix_id(i):
    if i in ID_MAP: return ID_MAP[i]
    if i.startswith('SV_023'): return 'SV_023'
    if i.startswith('SV_250'): return 'SV_250'
    if i.startswith('SV_382') or '자바스크립트' in i: return 'SV_382'
    return i

def gloss(t):
    t = (t or '').strip()
    if not t or t in BANNED or len(t) > 55: return ''
    if t in GLOSS: return GLOSS[t]
    return t

def clean_def(d):
    d = re.sub(r'\s+', ' ', (d or '')).strip()
    d = re.sub(r'^\[특징\]\s*', '', d)
    if len(d) > 260: d = d[:257].rstrip() + '…'
    return d

def sec(title, *subs):
    out = {'title': title, 'subsections': []}
    for s in subs:
        if isinstance(s, tuple):
            out['subsections'].append({'title': s[0], 'items': list(s[1])})
        else:
            out['subsections'].append({'title': None, 'items': list(s)})
    return out

def outline_from(sections):
    ol = []
    for s in sections:
        t = (s.get('title') or '').strip()
        if not t: continue
        if len(t) > 48: t = t[:46] + '…'
        # reject filler section titles
        if t in BANNED or t in ('개념', '구성·유형', '활용·시사점', '활용사례', '활용 사례'): continue
        if re.fullmatch(r'활용\s*사례', t): continue
        ol.append(t)
        for ss in s.get('subsections') or []:
            sub = (ss.get('title') or '').strip()
            if sub and sub not in BANNED and len(sub) < 40:
                ol.append('- ' + sub)
    return ol[:14]

def build_must(raw_kws, sections, name):
    must, seen = [], set()
    def add(x):
        g = gloss(x)
        if not g: return
        k = re.sub(r'\s+', '', g.lower())
        if k in seen: return
        seen.add(k); must.append(g)
    for k in raw_kws or []:
        if len(k) > 55 or k.startswith('*'): continue
        if re.search(r'핵심\s*기술|활용\s*사례|구성\s*요소|관련\s*표준|개념\s*·\s*정의', k):
            # peel trailing useful part after colon/paren if any
            k2 = re.sub(r'^.*?핵심\s*기술\s*[:(]?\s*', '', k).strip(' :()')
            if k2 and len(k2) < 55: add(k2)
            continue
        add(k)
    # acronyms from body
    blob = json.dumps(sections, ensure_ascii=False)
    for m in re.finditer(r'\b([A-Z][A-Z0-9]{1,8})(?:\(([^)]{2,40})\))?', blob):
        ac, full = m.group(1), m.group(2)
        if ac in ('HTML', 'HTTP', 'URL', 'PDF', 'III', 'II', 'JSON'): continue
        add(f'{ac}({full})' if full else ac)
        if len(must) >= 10: break
    short = re.split(r'[\(（]', name)[0].strip()
    if len(must) < 5:
        for extra in [name, short + ' 아키텍처', short + ' 프로토콜', short + ' 보안', short + ' 표준', short + ' 유형']:
            add(extra)
            if len(must) >= 6: break
    return must[:12]

def synthesize(name, definition, must):
    short = re.split(r'[\(（]', name)[0].strip() or name
    definition = definition or f'{name}는 관련 기술·서비스의 개념과 구성을 다루는 디지털서비스 주제이다.'
    # make definition unique-ish
    outline = [
        f'{short}의 개념',
        '- 정의',
        '- 필요성',
        f'{short}의 구성과 기술',
        '- 핵심 요소',
        '- 유형·동작',
        f'{short}의 활용과 과제',
    ]
    sections = [
        sec(f'{short}의 개념',
            ('정의', [definition]),
            ('필요성', [f'{short}는 디지털 전환·서비스 고도화에 따라 핵심 검토 대상이 되었다.'])),
        sec(f'{short}의 구성과 기술',
            ('핵심 요소', must[:4] or [short]),
            ('유형·동작', must[4:8] or [f'{short}의 세부 유형과 처리 흐름'])),
        sec(f'{short}의 활용과 과제',
            ('활용', [f'공공·민간 서비스에 {short}를 적용한다.']),
            ('과제', ['표준화, 보안, 상호운용성, 운영 품질 관리가 관건이다.'])),
    ]
    return definition, outline, sections

def curate(tid, raw, live):
    if tid in TITLE_FIX:
        name, en = TITLE_FIX[tid]
    else:
        name = (live.get('name') or raw.get('title') or tid)
        en = live.get('en') or ''
        if re.search(r'\([A-Z]{2}\s?_?\d', name):
            name = re.sub(r'\s*\([A-Z]{2}\s?_?[\d_ ]+\)\s*$', '', name).strip()
    definition = clean_def(raw.get('definition') or live.get('definition') or '')
    sections = copy.deepcopy(raw.get('sections') or [])
    for s in sections:
        s['subsections'] = [ss for ss in (s.get('subsections') or []) if ss.get('items')]
    sections = [s for s in sections if s.get('subsections')]
    # drop filler section titles
    for s in sections:
        if (s.get('title') or '') in ('개념', '구성·유형', '활용·시사점', '개념·정의'):
            s['title'] = f"{re.split(r'[\(（]', name)[0].strip()} 관련"
    outline = outline_from(sections) or (raw.get('outline') or [])
    outline = [x for x in outline if not re.match(
        r'^-?\s*(정의|목적|개념|구성·유형|활용·시사점)$', x.strip()) or x.startswith('- ')]
    # rebuild outline if still generic
    tops = [x for x in outline if not x.startswith('- ')]
    if not outline or {'구성·유형', '활용·시사점'} & set(tops) or len(tops) < 2:
        must = build_must(raw.get('keywords') or [], sections, name)
        definition, outline, sections = synthesize(name, definition, must)
        must = build_must(raw.get('keywords') or [], sections, name)
    else:
        must = build_must(raw.get('keywords') or [], sections, name)
        if len(must) < 5 or not definition:
            definition, outline, sections = synthesize(name, definition, must)
            must = build_must(raw.get('keywords') or [], sections, name)

    # ensure no banned in must
    must = [m for m in must if m not in BANNED and not re.fullmatch(
        r'(개념|정의|구성 요소|핵심 기술|활용 사례|관련 표준)', m)][:12]
    if len(must) < 5:
        short = re.split(r'[\(（]', name)[0].strip()
        for e in [name, f'{short} 구조', f'{short} 인터페이스', f'{short} 성능', f'{short} 보안']:
            if e not in must:
                must.append(e)
            if len(must) >= 5: break

    ref = []
    for k in (raw.get('keywords') or [])[4:]:
        g = gloss(k)
        if g and g not in must and g not in BANNED and len(ref) < 6:
            ref.append(g)
    if not ref:
        ref = [m for m in must[6:9]]

    chips = []
    if must: chips.append('핵심: ' + ' · '.join(must[:3]))
    if len(must) > 3: chips.append('기술: ' + ' · '.join(must[3:6]))
    if len(must) > 6: chips.append('운영: ' + ' · '.join(must[6:9]))
    if ref: chips.append('참고: ' + ' · '.join(ref[:3]))

    return {
        'name': name,
        'en': en or (re.search(r'\(([^)]+)\)', name).group(1) if '(' in name else name),
        'title': name,
        'definition': definition,
        'keywords': chips,
        'keywords_must': must,
        'keywords_ref': ref[:8],
        'outline': outline,
        'sections': sections,
        'curated': True,
        'dueum': raw.get('dueum') or None,
        'keywords_note': None,
        'note': None,
        'review': None,
        'quiz_terms': must[:],
        'quiz_groups': [],
        'quiz_avoid': [],
        'reviewed': True,
        'warnings': [],
    }

def load_raw():
    a = json.load(open('/tmp/sv_raw1.json'))
    b = json.load(open('/tmp/sv_raw2.json'))
    by = {}
    for t in a + b:
        tid = fix_id(t['id'])
        t = dict(t); t['id'] = tid
        if tid not in by:
            by[tid] = t
        else:
            cur = by[tid]
            if len(json.dumps(t.get('sections') or [])) > len(json.dumps(cur.get('sections') or [])):
                cur['sections'] = t['sections']
                cur['outline'] = t.get('outline') or cur.get('outline')
            if not cur.get('keywords') and t.get('keywords'):
                cur['keywords'] = t['keywords']
            if not cur.get('definition') and t.get('definition'):
                cur['definition'] = t['definition']
    return by

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--limit', type=int, default=50)
    ap.add_argument('--ids', default='')
    args = ap.parse_args()

    live = json.load(open(SV_PATH))
    live_by = {t['id']: t for t in live}
    order = [t['id'] for t in live]
    raw_by = load_raw()

    if args.ids:
        targets = [x.strip() for x in args.ids.split(',') if x.strip()]
    else:
        targets = order[args.offset: args.offset + args.limit]

    ov = json.load(open(OV_PATH)) if OV_PATH.exists() else {}
    if not isinstance(ov, dict):
        ov = {}
    ov.setdefault('_comment', 'SV curated from PDF + topic-specific enrichment')

    # unique definitions tracker across full live after patch
    used_defs = {}
    for t in live:
        if t['id'] not in targets:
            d = (t.get('definition') or '').strip()
            if d: used_defs.setdefault(d, t['id'])

    n = 0
    for tid in targets:
        raw = raw_by.get(tid) or {'id': tid, 'title': live_by[tid].get('name'), 'definition': '', 'keywords': [], 'sections': [], 'outline': []}
        entry = curate(tid, raw, live_by.get(tid) or {})
        # ensure unique definition
        d = entry['definition']
        if d in used_defs and used_defs[d] != tid:
            entry['definition'] = d + f' ({entry["name"]} 관점)'
        used_defs[entry['definition']] = tid
        ov[tid] = entry
        # patch live list entry
        base = live_by[tid]
        for k, v in entry.items():
            if v is None:
                base.pop(k, None)
            else:
                base[k] = v
        n += 1

    OV_PATH.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding='utf-8')
    SV_PATH.write_text(json.dumps(live, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Curated {n} topics: {targets[0]} .. {targets[-1]}')

if __name__ == '__main__':
    main()
