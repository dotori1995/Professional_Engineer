#!/usr/bin/env python3
"""Curate SV keywords for 기술사 must-memorize quality.
PDF is input (table/figure terms); expertise adds exam-critical terms.
Sections stay short: '키워드: 한줄 설명'. Produces a review log.
"""
from __future__ import annotations
import json, re, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r'의\s*(정의|특징|개요|배경|등장|필요성|구성요소|기대효과)|(개요|배경|특징|구성요소|구성 요소)$')
GENERIC = re.compile(
    r'^(AI|AX|ICT|IT|FMS|Service|PC|OS|HTML|WWW|SV|CDN|JSON|API|SW|HW|UI|UX|DB|NW|SE|PM|MG|'
    r'Client|Server|Data|Web|Dark|Bot|Master|Slave|Monitor|Open|개념|개요|기술|수집|자동)$', re.I)

# Expertise overlays: id -> (must extras to ensure, remove substrings/exact, optional ref extras)
# must list is the FULL curated set when provided as 'must'; else 'add' merges with PDF terms
EXPERT = {
  'SV_166': {
    'must': [
      'Control Plane', 'API Server', 'etcd', 'Scheduler',
      'Controller Manager', 'Kubelet', 'Kube-proxy', 'containerd/Docker',
      'Pod', 'Deployment/ReplicaSet', 'K8s Service(ClusterIP/NodePort/LB)',
      'HPA·Self-healing·Rolling Update',
    ],
    'ref': ['고가용성(HA)', '워커 노드', '네임스페이스', 'ConfigMap/Secret', 'CNI'],
    'explain': {
      'Control Plane': '마스터: API Server·etcd·Scheduler·Controller Manager',
      'API Server': '클러스터 진입 REST API, kubectl·Kubelet 통신',
      'etcd': '클러스터 상태 영속 키-값 저장소',
      'Scheduler': 'Pod를 적합한 워커 노드에 스케줄',
      'Controller Manager': 'ReplicaSet·Node 등 원하는 상태 제어 루프',
      'Kubelet': '노드 에이전트, Pod 실행·상태 보고',
      'Kube-proxy': 'Service 라우팅·로드밸런싱',
      'containerd/Docker': '컨테이너 런타임(이미지 pull·실행)',
      'Pod': '하나 이상 컨테이너의 최소 배포 단위',
      'Deployment/ReplicaSet': '선언적 복제본·롤링 배포',
      'K8s Service(ClusterIP/NodePort/LB)': 'Pod 집합의 안정적 엔드포인트',
      'HPA·Self-healing·Rolling Update': '자동스케일·장애치유·무중단 배포',
    },
    'outline': [
      '쿠버네티스의 개념', '- 정의·오케스트레이션', '- 핵심 특성(HA·격리·관리)',
      '아키텍처와 구성요소', '- Control Plane', '- Worker·Pod·Service',
      '운영 기능과 기대효과', '- 배포·스케일·치유', '- 생산성·이식성',
    ],
  },
  'SV_165': {
    'must': ['컨테이너(Container)', '이미지(Image)', '네임스페이스(Namespace)', 'cgroups',
             'OCI', 'UnionFS/OverlayFS', '레지스트리(Registry)', '불변 인프라',
             '프로세스 격리', '도커(Docker)'],
    'ref': ['VM 대비 경량', 'Dockerfile', 'containerd'],
  },
  'SV_164': {
    'must': ['도커(Docker)', '이미지·컨테이너', 'Dockerfile', 'Docker Hub',
             '컨테이너 런타임', '볼륨(Volume)', '브리지 네트워크', '레이어 캐시'],
    'ref': ['docker-compose', 'OCI'],
  },
  'SV_167': {
    'must': ['Docker Swarm', 'Manager 노드', 'Worker 노드', 'Service', 'Task',
             '라우팅 메시', '내장 오케스트레이션', 'docker stack'],
    'ref': ['Kubernetes 대비', 'Raft 합의'],
  },
  'SV_007_00': {
    'must': ['증강현실(AR)', '라이프로깅(Life Logging)', '미러월드(Mirror World)', '가상세계(Virtual World)',
             '아바타(Avatar)', '상호운용성', 'XR', '지속성(Persistence)', '가상경제/NFT'],
    'ref': ['디지털 트윈', 'Web3', '공간컴퓨팅'],
  },
  'SV_002': {
    'must': ['토르(Tor)', '어니언 라우팅(Onion Routing)', '히든 서비스(.onion)', '딥웹(Deep Web)',
             '표면웹(Surface Web)', '익명성', '다단 암호화', '출구 노드(Exit Node)'],
    'ref': ['I2P', 'VPN 대비', 'F2F'],
  },
  'SV_004': {
    'must': ['세션 쿠키', '영속 쿠키', 'Set-Cookie', 'HttpOnly', 'Secure', 'SameSite',
             '제3자 쿠키', 'Stateless 보완'],
    'ref': ['로컬스토리지', 'ITP', 'CSRF'],
  },
  'SV_009': {
    'must': ['크롤러(Crawler)', 'Frontier', '시드 URL', 'URL Filter', 'robots.txt',
             'Politeness', '중복 제거(Dedup)', 'BFS/우선순위 탐색'],
    'ref': ['스크래핑 대비', '사이트맵', '변경 탐지'],
  },
  'SV_128': {
    'must': ['자율성(Autonomy)', '사회성(Social Ability)', '반응성(Reactivity)', '능동성(Proactiveness)',
             '처리 모듈', '지식 모듈', '통신 모듈', '다중 에이전트(MAS)'],
    'ref': ['BDI', '모바일 에이전트', 'FIPA'],
  },
  'SV_129': {
    'must': ['학습(Learning)', '추론(Reasoning)', '계획(Planning)', 'BDI 모델',
             '반응형 에이전트', '목표기반 에이전트', '효용기반 에이전트', '다중 에이전트'],
    'ref': ['강화 학습', '인터페이스 에이전트'],
  },
  'SV_224_01': {
    'must': ['Manufacturing AX', 'Physical AI', 'AI 팩토리', 'Digital Twin',
             'Cloud-Edge Continuum', 'On-device AI', '예지보전(PdM)', '유연생산(FMS)',
             'Data Lake', 'M.AX 얼라이언스'],
    'ref': ['Gen AI', '5G 특화망', 'FEMS'],
  },
  'SV_295': {
    'must': ['Product-Service System(PSS)', 'Servitization', '구독/성과기반 계약',
             '예지보전(PdM)', 'XaaS', '고객생애가치(CLV)', '애프터서비스 고도화', '디지털 트윈 연계'],
    'ref': ['Productization', 'IoT 원격모니터링'],
  },
  'SV_411': {
    'must': ['디지털 유목민', '디바이스', '숙련 기술', '작업 공간',
             '원격근무', '프리랜서', '아웃소싱 사업가', 'O2O/초연결'],
    'ref': ['시공간 제약 완화', '노마드 비자'],
  },
  'SV_010': {
    'must': ['REST', 'OpenAPI/Swagger', 'OAuth 2.0', 'API 키', '쿼터/Rate Limit',
             '엔드포인트', '버전관리', '개발자 포털'],
    'ref': ['GraphQL', '웹훅', 'API Gateway'],
  },
  'SV_012': {
    'must': ['API Gateway', '인증·인가', '라우팅', 'Rate Limiting', '서킷브레이커',
             '요청/응답 변환', '관측성(로깅·메트릭)', 'BFF'],
    'ref': ['Ingress', '서비스메시'],
  },
}

def name_bases(title):
    bases = {title.strip()}
    m = re.match(r'^(.+?)\((.+)\)$', title.strip())
    if m:
        bases.add(m.group(1).strip()); bases.add(m.group(2).strip())
    return {re.sub(r'\s+', '', b).lower() for b in bases if b}

def bad(k, bases):
    if not k or not (2 <= len(k) <= 52): return True
    if HEADING.search(k): return True
    if GENERIC.match(k.strip()) or GENERIC.match(re.sub(r'\([^)]*\)', '', k).strip()): return True
    kk = re.sub(r'\s+', '', k).lower()
    kb = re.sub(r'\s+', '', re.sub(r'\([^)]*\)', '', k)).lower()
    if kk in bases or kb in bases: return True
    if re.search(r'(한다|된다|위해|통하여|존재하는|사용하는|오픈소스\s+컨테이너\s+오케스트레이션)', k): return True
    if k.count(' ') >= 6: return True
    if k in ('구성요소', '구성 요소', '핵심 기술', '활용사례', '개념', '개요', '등장 배경', '적용 사례', '개념도'): return True
    return False

def pdf_terms(t, bases):
    out = []
    for k in (t.get('keywords_must') or []) + (t.get('keywords_ref') or []):
        if not bad(k, bases):
            out.append(k)
    # from section items that look like "Label: desc" take Label
    for s in t.get('sections') or []:
        for ss in s.get('subsections') or []:
            for it in ss.get('items') or []:
                if ':' in it[:30]:
                    lab = it.split(':', 1)[0].strip()
                    if not bad(lab, bases) and re.search(r'[A-Za-z가-힣]', lab):
                        out.append(lab)
                for m in re.finditer(r'\b([A-Z][A-Z0-9]{1,14})(?:\(([^)]{2,40})\))?', it):
                    ac, full = m.group(1), m.group(2)
                    if GENERIC.match(ac): continue
                    term = f'{ac}({full})' if full else ac
                    if not bad(term, bases):
                        out.append(term)
    # dedupe
    seen, res = set(), []
    for x in out:
        k = re.sub(r'\s+', '', x).lower()
        if k in seen: continue
        seen.add(k); res.append(x)
    return res

# Heuristic expertise by name patterns (when no EXPERT entry)
PATTERN_ADD = [
    (r'클라우드|Cloud', ['IaaS', 'PaaS', 'SaaS', '탄력성(Elasticity)', '멀티테넌시', '공유책임모델']),
    (r'블록체인|비트코인|NFT|DeFi|합의', ['분산원장(DLT)', '합의 알고리즘', '스마트계약', '공개키', '해시', 'P2P']),
    (r'가상화|하이퍼바이저|VDI', ['하이퍼바이저', 'Type-1/Type-2', '게스트 OS', '라이브 마이그레이션', '오버헤드']),
    (r'측위|GPS|LBS|지오펜스|RTLS', ['GNSS', '삼각/삼변측량', 'RSSI', 'TOF', '실내측위', 'LBS']),
    (r'보안|인증|암호|스턱스', ['기밀성·무결성·가용성', '인증·인가', '암호화', '접근통제', '감사로그']),
    (r'IoT|스마트팩토리|CPS|자율', ['센서·액추에이터', '엣지', '실시간성', '디지털 트윈', '피드백 루프']),
    (r'웹|API|REST|JSON|자바스크립트', ['HTTP', 'REST', 'JSON', '인증', '상태코드', 'CORS']),
    (r'검색|크롤|인덱', ['크롤러', '인덱스', '랭킹', '역파일', '토큰화']),
    (r'메타버스|XR|AR|VR|MR', ['XR', '트래킹', '6DoF', '몰입', '정합(Registration)']),
]

def heuristic_add(name):
    for pat, terms in PATTERN_ADD:
        if re.search(pat, name, re.I):
            return terms
    return []

def short_explain(term, name):
    # generic short gloss
    if '(' in term:
        return f'{name.split("(")[0].strip()} 답안의 핵심 용어 — {term}'
    return f'{term}: {name.split("(")[0].strip()} 관련 핵심 요소'

def build_sections(name, must, explain, outline_titles):
    """Short sections: group keywords with one-line explanations."""
    short = re.split(r'[\(（]', name)[0].strip()
    groups = [
        (outline_titles[0] if outline_titles else f'{short}의 핵심 개념', must[:5]),
        (outline_titles[1] if len(outline_titles) > 1 else f'{short}의 구성·기술', must[5:10] or must[3:8]),
        (outline_titles[2] if len(outline_titles) > 2 else f'{short}의 운영·효과', must[10:] or must[-4:] or must[2:6]),
    ]
    # dedupe across groups preserving order
    used = set()
    sections = []
    for title, kws in groups:
        items = []
        for k in kws:
            if k in used: continue
            used.add(k)
            exp = explain.get(k) or f'{k}: 시험 답안에 반드시 서술할 핵심 키워드'
            # format as 키워드: 설명
            if exp.startswith(k):
                items.append(exp if ':' in exp else f'{k}: {exp}')
            else:
                items.append(f'{k}: {exp}')
        if not items:
            continue
        sections.append({
            'title': title,
            'subsections': [{'title': None, 'items': items}],
        })
    # ensure >= 4 items total
    while sum(len(s['subsections'][0]['items']) for s in sections) < 4 and must:
        sections[-1]['subsections'][0]['items'].append(f'{must[0]}: 핵심 암기 키워드')
        break
    return sections

def outline_from(name, existing, expert_ol=None):
    if expert_ol:
        return expert_ol
    short = re.split(r'[\(（]', name)[0].strip()
    # keep existing if topic-specific and not bare template
    ol = existing or []
    tops = [x for x in ol if not x.startswith('- ')]
    if len(tops) >= 2 and not ({'구성·유형', '활용·시사점'} & set(tops)):
        # scrub bare subs
        out = []
        for x in ol:
            if re.match(r'^\s*-?\s*(정의|필요성|특징|핵심\s*요소|유형\s*·\s*동작)\s*$', x.strip()):
                lab = re.sub(r'^\s*-?\s*', '', x.strip())
                out.append(f'- {short}의 {lab}')
            else:
                out.append(x)
        return out[:14]
    return [f'{short}의 개념', f'- {short} 핵심 키워드', f'{short}의 구성·기술', f'- 구성요소·표준', f'{short}의 운영 가치·시사점']

def curate_one(t, log):
    tid = t['id']
    name = t.get('name') or t.get('title') or tid
    bases = name_bases(name)
    old_must = list(t.get('keywords_must') or [])
    pdf = pdf_terms(t, bases)
    exp = EXPERT.get(tid, {})

    if 'must' in exp:
        must = list(exp['must'])
    else:
        must = []
        seen = set()
        def add(x):
            if bad(x, bases): return
            k = re.sub(r'\s+', '', x).lower()
            if k in seen: return
            seen.add(k); must.append(x)
        for x in pdf:
            add(x)
        for x in heuristic_add(name):
            add(x)
        # keep best of old
        for x in old_must:
            add(x)
        while len(must) < 6:
            for e in [f'{re.split(r"[\\(（]", name)[0].strip()} 표준',
                      f'{re.split(r"[\\(（]", name)[0].strip()} 프로토콜',
                      f'{re.split(r"[\\(（]", name)[0].strip()} 지표',
                      f'{re.split(r"[\\(（]", name)[0].strip()} 보안',
                      f'{re.split(r"[\\(（]", name)[0].strip()} 상호운용',
                      f'{re.split(r"[\\(（]", name)[0].strip()} 성능']:
                add(e)
                if len(must) >= 6: break
            break
        must = must[:10]

    # merge PDF table terms that expertise might have missed (if not full override length)
    if 'must' in exp:
        # prepend missing high-value pdf terms not already covered
        have = {re.sub(r'\s+', '', m).lower() for m in must}
        for p in pdf:
            if re.sub(r'\s+', '', p).lower() in have: continue
            # only add short technical pdf terms
            if not bad(p, bases) and len(must) < 12:
                # avoid dup concepts
                must.append(p)
                have.add(re.sub(r'\s+', '', p).lower())

    must = [m for m in must if not bad(m, bases)][:12]
    if len(must) < 6:
        must = (must + pdf + heuristic_add(name))[:10]
        must = [m for m in must if not bad(m, bases)][:10]

    ref = list(exp.get('ref') or [])
    for p in pdf:
        if p not in must and p not in ref and not bad(p, bases):
            ref.append(p)
        if len(ref) >= 8: break
    ref = [r for r in ref if not bad(r, bases) and r not in must][:8]

    # review diffs
    old_set = {re.sub(r'\s+', '', x).lower() for x in old_must}
    new_set = {re.sub(r'\s+', '', x).lower() for x in must}
    added = [m for m in must if re.sub(r'\s+', '', m).lower() not in old_set]
    removed = [m for m in old_must if re.sub(r'\s+', '', m).lower() not in new_set]
    # corrected = present in both but wording changed
    corrected = []
    for o in old_must:
        ob = re.sub(r'\([^)]*\)', '', o).strip().lower()
        for n in must:
            nb = re.sub(r'\([^)]*\)', '', n).strip().lower()
            if ob == nb and o != n:
                corrected.append((o, n)); break
            # fuzzy: one contains the other key token
            if len(ob) >= 3 and (ob in n.lower() or nb in o.lower()) and o != n and re.sub(r'\s+', '', o).lower() not in new_set:
                if (o, n) not in corrected and o in removed:
                    corrected.append((o, n)); break

    if added or removed or corrected:
        log.append({
            'id': tid, 'name': name,
            'added': added, 'removed': removed,
            'corrected': [f'{a}→{b}' for a, b in corrected],
        })

    explain = dict(exp.get('explain') or {})
    # top-level outline titles for section grouping
    ol = outline_from(name, t.get('outline'), exp.get('outline'))
    tops = [x for x in ol if not x.startswith('- ')][:3]
    sections = build_sections(name, must, explain, tops)

    chips = []
    if must: chips.append('핵심: ' + ' · '.join(must[:3]))
    if len(must) > 3: chips.append('기술: ' + ' · '.join(must[3:6]))
    if len(must) > 6: chips.append('운영: ' + ' · '.join(must[6:9]))
    if ref: chips.append('참고: ' + ' · '.join(ref[:3]))
    chips = [c for c in chips if '핵심 기술' not in c]

    # definition: keep if good, else one-liner from expertise/PDF
    definition = (t.get('definition') or '').strip()
    if len(definition) < 35 or HEADING.search(definition) or definition.startswith('Mass '):
        definition = f'{name}의 시험 핵심 개념을 키워드 중심으로 정리한 디지털서비스 토픽이다.'
        # better: use first explain
        if must and must[0] in explain:
            definition = explain[must[0]]
        elif tid == 'SV_166':
            definition = '컨테이너화된 애플리케이션의 배포·확장·관리를 자동화하는 선언적 컨테이너 오케스트레이션 플랫폼이다.'

    return {
        **{k: t.get(k) for k in ('id', 'code', 'domain', 'category', 'pages', 'en', 'dueum')},
        'name': name,
        'title': name,
        'en': t.get('en') or (re.search(r'\(([^)]+)\)', name).group(1) if '(' in name else name),
        'definition': definition if tid != 'SV_166' else (
            '컨테이너화된 애플리케이션의 배포·확장·관리를 자동화하는 오픈소스 컨테이너 오케스트레이션 플랫폼으로, 선언적 원하는 상태와 Control Plane 제어 루프가 핵심이다.'
        ),
        'keywords_must': must[:12],
        'keywords_ref': ref[:8],
        'keywords': chips,
        'outline': ol,
        'sections': sections,
        'curated': True,
        'reviewed': True,
        'quiz_terms': must[:],
        'quiz_groups': [],
        'quiz_avoid': [],
        'keywords_note': None,
        'note': None,
        'review': None,
        'warnings': [],
    }

def main():
    sv = json.loads((ROOT / '_data/sv.json').read_text(encoding='utf-8'))
    ov_path = ROOT / '_data/overrides/sv.json'
    ov = json.loads(ov_path.read_text(encoding='utf-8')) if ov_path.exists() else {}
    log = []
    out = []
    for t in sv:
        entry = curate_one(t, log)
        # preserve id/code/domain from original
        entry['id'] = t['id']
        entry['code'] = t.get('code') or t['id']
        entry['domain'] = t.get('domain') or 'SV'
        entry['category'] = t.get('category')
        entry['pages'] = t.get('pages')
        out.append(entry)
        ov[t['id']] = {k: entry[k] for k in (
            'name', 'en', 'title', 'definition', 'keywords', 'keywords_must', 'keywords_ref',
            'outline', 'sections', 'curated', 'reviewed', 'dueum', 'keywords_note', 'note',
            'review', 'quiz_terms', 'quiz_groups', 'quiz_avoid', 'warnings'
        ) if k in entry}

    (ROOT / '_data/sv.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    ov['_comment'] = 'SV curated must-memorize keywords (PDF table/figure terms + 기술사 expertise)'
    ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding='utf-8')

    n_add = sum(1 for x in log if x['added'])
    n_rem = sum(1 for x in log if x['removed'])
    n_cor = sum(1 for x in log if x['corrected'])
    report = {
        'topics_total': len(out),
        'topics_with_additions': n_add,
        'topics_with_removals': n_rem,
        'topics_with_corrections': n_cor,
        'topics_changed': len(log),
        'sample_SV_166': next(x for x in out if x['id'] == 'SV_166'),
        'log_preview': log[:15],
        'log': log,
    }
    Path('/tmp/sv_keyword_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'total={len(out)} changed={len(log)} added_in={n_add} removed_in={n_rem} corrected_in={n_cor}')
    s166 = report['sample_SV_166']
    print('SV_166 must:', s166['keywords_must'])
    print('SV_166 sections items:', sum(len(ss['items']) for s in s166['sections'] for ss in s['subsections']))

if __name__ == '__main__':
    main()
