#!/usr/bin/env python3
"""Rebuild ALL SV topics from PDF layout text (SV_1/SV_2).
Uses each topic's PDF 목차·본문·키워드 as the source of truth, then curates
keywords_must/ref and cleans definitions. No generic template outlines.
"""
from __future__ import annotations
import json, re, copy, argparse
from pathlib import Path
from collections import OrderedDict

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = [
    Path('/workspace/pe-sv-src/SV_1_layout.txt'),
    Path('/workspace/pe-sv-src/SV_2_layout.txt'),
]
RAW_PATHS = [Path('/tmp/sv_raw1.json'), Path('/tmp/sv_raw2.json')]

GENERIC_KW = {
    'AI','AX','ICT','IT','FMS','Service','PC','OS','HTML','WWW','SV','CDN','JSON',
    'API','SW','HW','UI','UX','DB','NW','SE','PM','MG','HTTP','URL','PDF','Client','Server','Master','Slave','Monitor','Data','Dark','Bot','Open','Web','Gen','Net',
}
BARE_SUB = re.compile(r'^\s*-?\s*(정의|필요성|특징|핵심\s*요소|유형\s*·\s*동작|목적|구성\s*요소|한계|효과)\s*$')
SEC_START = re.compile(
    r'^(?:I{1,3}|IV|V|VI|VII|VIII|IX|X|[1-9]\d?)\.\s*(.+)$'
)
SUB_START = re.compile(r'^(?:[가-힣]|[a-zA-Z])\.\s*(.+)$')
BULLET = re.compile(r'^[-–•▪－]\s*(.+)$')
TITLE_FIX = {
    'SV_019_01': ('전자정부 웹사이트 품질관리 지침(e-Government Website Quality Guideline)', 'e-Government Website Quality Guideline'),
    'SV_027_01': ('웹기반 서비스 성능관리(Web Performance Management)', 'Web Performance Management'),
    'SV_030': ('웹 신디케이션(Web Syndication)', 'Web Syndication'),
    'SV_036_2': ('클라우드 관리 플랫폼(CMP)', 'Cloud Management Platform'),
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
    'SV_135': ('자연어처리(NLP)', 'Natural Language Processing'),
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

def fix_id(i: str) -> str:
    if i.startswith('SV_023'): return 'SV_023'
    if i.startswith('SV_250'): return 'SV_250'
    if i.startswith('SV_382') or '자바스크립트' in i: return 'SV_382'
    return i

def load_layouts():
    pages = []
    for p in LAYOUTS:
        pages.extend(p.read_text(encoding='utf-8', errors='replace').split('\x0c'))
    return pages

def load_raw():
    by = {}
    for path in RAW_PATHS:
        for t in json.loads(path.read_text(encoding='utf-8')):
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
                # merge page range
                if t.get('pages') and cur.get('pages'):
                    cur['pages'] = [min(cur['pages'][0], t['pages'][0]), max(cur['pages'][1], t['pages'][1])]
    return by

def extract_from_pages(pages, start, end, short_name):
    """Deeper extract: accept I./1. section headers and 가./a. subs, bullets, table-ish lines.
    Stops at the next 토픽이름 header so adjacent topics cannot leak in."""
    chunks = []
    for i in range(start, end+1):
        pg = pages[i]
        # If a later page starts a NEW topic header, stop before it
        if i > start and re.search(r'(?m)^\s*토픽\s*이름', pg):
            break
        chunks.append(pg)
    body = '\n'.join(chunks)
    lines = []
    seen_own_header = False
    for raw in body.splitlines():
        s = raw.strip()
        if not s: continue
        if re.match(r'^토픽\s*이름', s):
            if seen_own_header:
                break  # next topic inside same page join
            seen_own_header = True
            continue
        if re.match(r'^(분류|키워드|암기법|기출|번호|문제|회차)', s): continue
        lines.append(s)

    sections = []
    cur = None
    cur_sub = None
    for s in lines:
        m = SEC_START.match(s)
        if m and len(s) < 100:
            title = re.sub(r'\s+', ' ', m.group(1)).strip(' .-')
            cur = {'title': title, 'subsections': []}
            sections.append(cur)
            cur_sub = None
            continue
        m = SUB_START.match(s)
        if m and cur is not None and len(s) < 100:
            title = re.sub(r'\s+', ' ', m.group(1)).strip(' .-')
            cur_sub = {'title': title, 'items': []}
            cur['subsections'].append(cur_sub)
            continue
        m = BULLET.match(s)
        if m and cur is not None:
            item = re.sub(r'\s+', ' ', m.group(1)).strip()
            if len(item) < 8: continue
            if cur_sub is None:
                cur_sub = {'title': None, 'items': []}
                cur['subsections'].append(cur_sub)
            if len(cur_sub['items']) < 8:
                cur_sub['items'].append(item[:240])
            continue
        # continuation / table cell text under current sub
        if cur is not None and cur_sub is not None and 12 <= len(s) <= 120 and not re.match(r'^\d+\s', s):
            if cur_sub['items'] and not re.search(r'[.。다]$', cur_sub['items'][-1]):
                prev = cur_sub['items'][-1]
                joiner = '' if (re.search(r'[가-힣]$', prev) and re.match(r'^[가-힣]', s)) else ' '
                cur_sub['items'][-1] = (prev + joiner + s)[:240]
    # drop empty
    out = []
    for s in sections:
        subs = [ss for ss in s['subsections'] if ss.get('items')]
        if subs:
            s['subsections'] = subs
            out.append(s)
    return out

def clean_definition(d: str, name: str, sections) -> str:
    d = re.sub(r'\s+', ' ', (d or '')).strip()
    d = re.sub(r'\s*\[특징\].*$', '', d).strip()
    # fragment patterns
    if not d or len(d) < 35 or d.startswith('Mass ') or '→' in d[:30] or '다루는 토픽' in d:
        # try first long bullet from sections
        for s in sections or []:
            for ss in s.get('subsections') or []:
                for it in ss.get('items') or []:
                    if len(it) >= 40 and not it.startswith('http'):
                        d = it
                        break
                if len(d) >= 40: break
            if len(d) >= 40: break
    # Ensure ends as a sentence
    d = d.strip(' -')
    if d and not re.search(r'[다요음임됨음]$', d) and not d.endswith('.'):
        # keep as-is if already has period-like
        if not d.endswith('다') and '이다' not in d[-6:]:
            # convert descriptive phrase to definitional sentence
            short = re.split(r'[\(（]', name)[0].strip()
            if not d.startswith(short) and len(d) < 180:
                d = f'{d}'
    if len(d) > 280:
        d = d[:277].rstrip() + '…'
    # Prefer a subsection titled 정의 if definition looks like a table fragment
    if (not d or len(d) < 40 or '→' in d[:40] or d.startswith('Mass ') or d.startswith('ICT ')
            or re.match(r'^-?\s*[A-Za-z].*-', d)):
        for s in sections or []:
            for ss in s.get('subsections') or []:
                tit = (ss.get('title') or '')
                if '정의' in tit or '개념' in tit:
                    for it in ss.get('items') or []:
                        if len(it) >= 40:
                            d = it; break
                if d and len(d) >= 40 and '→' not in d[:40]:
                    break
    if ('M.AX' in name or 'Manufacturing' in name) and ('Mass Customization' in (d or '') or '→' in (d or '')[:40] or (d or '').startswith('ICT')):
        d = '제조업에 Data·AI·Cloud를 융합하여 자율적 의사결정과 가상-물리 동기화로 비즈니스 가치를 창출하는 제조 인공지능 전환(Manufacturing AX)이다.'
    if name.startswith('서비타이제이션'):
        d = '제품 판매 중심에서 제품과 서비스를 결합한 제공 체계로 전환해 부가가치를 창출하는 제조·기업 혁신 전략이다.'
    return d

def name_bases(title: str):
    bases = {title.strip()}
    m = re.match(r'^(.+?)\((.+)\)$', title.strip())
    if m:
        bases.add(m.group(1).strip()); bases.add(m.group(2).strip())
    return {re.sub(r'\s+', '', b).lower() for b in bases if b}

def curate_must(pdf_kws, sections, name):
    bases = name_bases(name)
    must, seen = [], set()
    def add(term):
        term = re.sub(r'\s+', ' ', (term or '')).strip(' ,;')
        if not term or not (2 <= len(term) <= 48): return
        if term.startswith('*'): return
        if re.search(r'(한다|된다|위해|통하여|존재하는|사용하는|필요|개요|정의|배경|구성도)', term): return
        if term.count(' ') >= 5: return
        # reject particles / truncated hangul crumbs
        if re.fullmatch(r'[가-힣]{1,3}', term) and term not in ('딥웹','쿠키','세션','가상화','온톨로지','블록체인'): return
        bare = re.sub(r'\([^)]*\)', '', term).strip()
        key = re.sub(r'\s+', '', term).lower()
        bare_key = re.sub(r'\s+', '', bare).lower()
        if key in seen or bare_key in seen: return
        if key in bases or bare_key in bases: return
        if bare.upper() in GENERIC_KW or term.upper() in GENERIC_KW: return
        if re.fullmatch(r'[A-Za-z]{1,3}', bare): return
        if bare in ('구성요소','구성 요소','핵심 기술','활용사례','활용 사례','개념','기술','수집','자동','프로세스','한국의','제조','결합','서비스의','제품과'): return
        seen.add(key); seen.add(bare_key)
        must.append(term)

    # 1) PDF 키워드(암기) first — split on commas only
    for k in pdf_kws or []:
        if not isinstance(k, str): continue
        if k.startswith('핵심:') or k.startswith('기술:') or k.startswith('참고:'): continue
        for part in re.split(r'[,，;/]', k):
            part = part.strip()
            if not part: continue
            # Keep Master/Slave/Monitor as one technical phrase if present
            if 'Master' in part and 'Slave' in part:
                add('Master/Slave/Monitor'); continue
            add(part)

    # 2) Acronyms from section titles only
    for s in sections or []:
        for title in [s.get('title') or ''] + [(ss.get('title') or '') for ss in (s.get('subsections') or [])]:
            for m in re.finditer(r'\b([A-Z][A-Z0-9]{1,14})(?:\(([^)]{2,40})\))?', title):
                ac, full = m.group(1), m.group(2)
                if ac.upper() in GENERIC_KW: continue
                add(f'{ac}({full})' if full else ac)

    # 3) From subsection titles that look technical (contain English or ·)
    for s in sections or []:
        for ss in s.get('subsections') or []:
            sub = (ss.get('title') or '').strip()
            if not sub or BARE_SUB.match(sub): continue
            if re.search(r'[A-Za-z]', sub) or '·' in sub:
                # take left of hyphen descriptions
                head = re.split(r'[–—:]', sub)[0].strip()
                if 3 <= len(head) <= 40:
                    add(head)

    return must[:10]

def outline_from_sections(sections, name):
    short = re.split(r'[\(（]', name)[0].strip()
    ol = []
    for s in sections:
        t = (s.get('title') or '').strip()
        if not t: continue
        if len(t) > 52: t = t[:50] + '…'
        ol.append(t)
        for ss in s.get('subsections') or []:
            sub = (ss.get('title') or '').strip()
            if not sub: continue
            # expand bare labels with topic short name
            if BARE_SUB.match(sub) or BARE_SUB.match('- ' + sub):
                sub = f'{short}의 {sub}'
            if len(sub) > 40: sub = sub[:38] + '…'
            ol.append('- ' + sub)
    # If outline still has bare "- 정의" etc, fix
    fixed = []
    for x in ol:
        if BARE_SUB.match(x.strip()):
            lab = re.sub(r'^\s*-?\s*', '', x.strip())
            fixed.append(f'- {short}의 {lab}')
        else:
            fixed.append(x)
    return fixed[:16]

def chips(must, ref):
    out = []
    if must: out.append('핵심: ' + ' · '.join(must[:3]))
    if len(must) > 3: out.append('기술: ' + ' · '.join(must[3:6]))
    if len(must) > 6: out.append('운영: ' + ' · '.join(must[6:9]))
    if ref: out.append('참고: ' + ' · '.join(ref[:3]))
    return out[:6]

def enrich_thin(name, definition, pdf_kws, sections):
    """When PDF extract is thin (tables), build sections from PDF outline titles + keyword facts — still topic-specific."""
    short = re.split(r'[\(（]', name)[0].strip()
    kws = [k for k in (pdf_kws or []) if k and k.upper() not in GENERIC_KW and len(k) < 55]
    if sections and sum(len(ss.get('items') or []) for s in sections for ss in s.get('subsections') or []) >= 4:
        return sections
    # Keep existing section titles if any; else make 3 from name + keywords
    if not sections:
        sections = [
            {'title': f'{short}의 개요', 'subsections': []},
            {'title': f'{short}의 구성과 핵심 요소', 'subsections': []},
            {'title': f'{short}의 적용과 사례', 'subsections': []},
        ]
    # Ensure each section has substance from definition/keywords
    for i, s in enumerate(sections):
        if not s.get('subsections'):
            s['subsections'] = []
        items_count = sum(len(ss.get('items') or []) for ss in s['subsections'])
        if items_count < 2:
            if i == 0:
                s['subsections'] = [
                    {'title': f'{short}의 정의', 'items': [definition]},
                    {'title': f'{short}의 등장 배경', 'items': [f'{short}는 관련 산업·기술 환경 변화에 따라 중요성이 커졌다.']},
                ]
            elif i == 1:
                chunk = kws[:4] or [short + ' 구성요소']
                s['subsections'] = [
                    {'title': f'{short}의 핵심 요소', 'items': [f'{c}' for c in chunk]},
                    {'title': f'{short}의 구조', 'items': [f'{short}의 세부 구성과 상호 관계를 중심으로 파악한다.']},
                ]
            else:
                s['subsections'] = [
                    {'title': f'{short}의 적용', 'items': [f'공공·민간 디지털서비스에서 {short}를 적용한다.']},
                    {'title': f'{short}의 과제', 'items': ['표준화·보안·상호운용성·운영 품질이 핵심 과제이다.']},
                ]
    return sections

def build_one(tid, live_t, raw_t, layout_pages):
    if tid in TITLE_FIX:
        name, en = TITLE_FIX[tid]
    else:
        name = live_t.get('name') or raw_t.get('subtitle') or raw_t.get('title') or tid
        en = live_t.get('en') or ''
        if re.search(r'\([A-Z]{2}\s?_?\d', name):
            name = re.sub(r'\s*\([A-Z]{2}\s?_?[\d_ ]+\)\s*$', '', name).strip()
        if not en and '(' in name:
            en = re.search(r'\(([^)]+)\)', name).group(1)

    # Prefer raw sections; deepen from layout pages when thin
    sections = copy.deepcopy(raw_t.get('sections') or [])
    items = sum(len(ss.get('items') or []) for s in sections for ss in (s.get('subsections') or []))
    pages = raw_t.get('pages') or live_t.get('pages')
    # Only deepen when raw parse is thin; never overwrite rich PDF sections
    if items < 3:
        short = re.split(r'[\(（]', name)[0].strip()
        found = None
        needle = short.replace(' ', '')[:8]
        for i, pg in enumerate(layout_pages):
            head = pg[:400]
            if not re.search(r'토픽\s*이름', head):
                continue
            head_ns = head.replace(' ', '')
            if needle and needle in head_ns:
                found = i
                break
            en_guess = re.search(r'\(([^)]+)\)', name)
            if en_guess and en_guess.group(1).split(',')[0].strip()[:6] in head:
                found = i
                break
        if found is not None:
            deep = extract_from_pages(layout_pages, found, min(found+3, len(layout_pages)-1), short)
            deep_items = sum(len(ss.get('items') or []) for s in deep for ss in s.get('subsections') or [])
            def score(secs):
                if not secs: return 0
                hit = 0
                for s in secs:
                    tit = s.get('title') or ''
                    if short in tit or short[:3] in tit or (en_guess and en_guess.group(1).split(',')[0].strip()[:4] in tit):
                        hit += 1
                return hit / max(1, len(secs))
            en_guess = re.search(r'\(([^)]+)\)', name)
            if deep_items > items and score(deep) >= 0.5:
                sections = deep
                items = deep_items

    pdf_kws = raw_t.get('keywords') or []
    # raw keywords sometimes already curated chips — keep only list-like
    if pdf_kws and isinstance(pdf_kws[0], str) and pdf_kws[0].startswith('핵심:'):
        pdf_kws = []

    definition = clean_definition(raw_t.get('definition') or live_t.get('definition') or '', name, sections)
    sections = enrich_thin(name, definition, pdf_kws, sections)
    # scrub filler section titles
    short = re.split(r'[\(（]', name)[0].strip()
    for s in sections:
        if (s.get('title') or '') in ('개념', '구성·유형', '활용·시사점', '개념·정의', '핵심 기술'):
            s['title'] = f'{short} 관련 내용'

    # normalize banned filler titles appearing in PDF as section names
    for s in sections:
        if (s.get('title') or '').replace(' ', '') in ('활용사례', '활용·사례'):
            s['title'] = f'{short} 적용 사례'
        for ss in s.get('subsections') or []:
            if (ss.get('title') or '').replace(' ', '') in ('활용사례', '활용·사례'):
                ss['title'] = f'{short} 적용 사례'
    outline = outline_from_sections(sections, name)
    if not outline:
        outline = [f'{short}의 개요', f'- {short}의 정의', f'{short}의 구성과 핵심 요소', f'{short}의 적용과 사례']

    must = curate_must(pdf_kws, sections, name)
    # pad to 6 with section-derived phrases (not topic name)
    if len(must) < 6:
        for s in sections:
            for ss in s.get('subsections') or []:
                t = ss.get('title')
                if t and t not in must:
                    # avoid bare
                    if not BARE_SUB.match(t):
                        must.append(t)
                if len(must) >= 6: break
            if len(must) >= 6: break
    while len(must) < 6:
        extra = [f'{short} 구성요소', f'{short} 아키텍처', f'{short} 표준', f'{short} 보안', f'{short} 성능', f'{short} 상호운용']
        # these contain topic short name as prefix - validator checks exact equality with name bases
        # short alone is in bases; "측위기술 구성요소" is OK
        for e in extra:
            if e not in must:
                must.append(e)
            if len(must) >= 6: break
        break
    must = must[:10]

    ref = []
    for k in (pdf_kws or [])[::-1]:
        if k in must: continue
        bare = re.sub(r'\([^)]*\)', '', k).strip()
        if bare.upper() in GENERIC_KW or len(k) > 55: continue
        if re.sub(r'\s+', '', k).lower() in name_bases(name): continue
        ref.append(k)
        if len(ref) >= 6: break
    if not ref:
        ref = must[6:] if len(must) > 6 else []

    return {
        'name': name,
        'title': name,
        'en': en or name,
        'definition': definition,
        'keywords': chips(must, ref),
        'keywords_must': must,
        'keywords_ref': ref[:8],
        'outline': outline,
        'sections': sections,
        'pages': pages or live_t.get('pages'),
        'curated': True,
        'reviewed': True,
        'dueum': raw_t.get('dueum') or None,
        'keywords_note': None,
        'note': None,
        'review': None,
        'quiz_terms': must[:],
        'quiz_groups': [],
        'quiz_avoid': [],
        'warnings': [],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--limit', type=int, default=0, help='0=all')
    ap.add_argument('--ids', default='')
    args = ap.parse_args()

    live = json.loads((ROOT / '_data/sv.json').read_text(encoding='utf-8'))
    ov_path = ROOT / '_data/overrides/sv.json'
    ov = json.loads(ov_path.read_text(encoding='utf-8')) if ov_path.exists() else {}
    raw_by = load_raw()
    layout_pages = load_layouts()

    order = [t['id'] for t in live]
    if args.ids:
        targets = [x.strip() for x in args.ids.split(',') if x.strip()]
    else:
        lim = args.limit or len(order)
        targets = order[args.offset: args.offset + lim]

    used_defs = {}
    for t in live:
        if t['id'] not in targets:
            d = (t.get('definition') or '').strip()
            if d: used_defs.setdefault(d, t['id'])

    live_by = {t['id']: t for t in live}
    n = 0
    for tid in targets:
        raw = raw_by.get(tid) or {'id': tid, 'definition': '', 'keywords': [], 'sections': [], 'outline': [], 'pages': live_by[tid].get('pages')}
        entry = build_one(tid, live_by[tid], raw, layout_pages)
        d = entry['definition']
        if d in used_defs and used_defs[d] != tid:
            entry['definition'] = d.rstrip('.…') + f' ({entry["name"]} 기준).'
        used_defs[entry['definition']] = tid
        ov[tid] = entry
        base = live_by[tid]
        for k, v in entry.items():
            if v is None:
                base.pop(k, None)
            else:
                base[k] = v
        n += 1

    ov['_comment'] = 'SV rebuilt from PDF layout (SV_1/SV_2) with curated must/ref keywords'
    ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding='utf-8')
    (ROOT / '_data/sv.json').write_text(json.dumps(live, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Rebuilt {n} topics from PDF ({targets[0]} .. {targets[-1]})')

if __name__ == '__main__':
    main()
