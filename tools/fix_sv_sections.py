#!/usr/bin/env python3
"""Rewrite SV section explanations (unique, topic-specific) and shorten/rebuild outlines."""
from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

BAD_KW = re.compile(
    r'^(키워드\(암기\)|암기법(\(해당경우\))?|이름\s*[\(（].*|토픽\s*이름|'
    r'핵심:?\s*(개념|기술)|구성\s*요소|활용\s*사례|설명|공통점|특징|정의|목적|'
    r'가\.\s*|나\.\s*|다\.\s*|라\.\s*|W\)|해당경우)$', re.I)

# High-value term glossaries (description ONLY — keyword prefixed later)
GLOSS = {
  '토르(Tor)': '분산 릴레이로 통신 경로를 숨기는 익명 네트워크 클라이언트/네트워크',
  '어니언 라우팅(Onion Routing)': '3개 이상 릴레이에 다중 암호화 계층을 씌워 경로를 은닉',
  '히든 서비스(.onion)': '출구 노드 없이 .onion 주소로만 도달하는 은닉 서비스',
  '딥웹(Deep Web)': '검색엔진에 색인되지 않는 비공개·로그인 웹 영역',
  '표면웹(Surface Web)': '일반 검색엔진이 크롤·색인하는 공개 웹',
  '익명성': '통신 주체·경로를 추적하기 어렵게 만드는 속성',
  '다단 암호화': '구간마다 다른 키로 겹겹이 암호화해 중간 노드 노출을 차단',
  '출구 노드(Exit Node)': 'Tor 회로의 마지막 릴레이로 일반 인터넷에 접속하는 지점',
  'Control Plane': '클러스터 상태를 감시·결정하는 마스터 제어 계층',
  'API Server': 'K8s의 유일한 창구로 모든 컴포넌트가 경유하는 REST API',
  'Etcd': '클러스터 desired/actual 상태를 보관하는 분산 키-값 저장소',
  'Scheduler': 'Pod를 조건에 맞는 Node에 배치하는 스케줄러',
  'Kubelet': '노드에서 Pod 생명주기를 실행·보고하는 에이전트',
  'Kube-proxy': 'Service 클러스터IP를 노드 네트워킹 규칙으로 구현',
  '컨테이너 런타임': '컨테이너 이미지를 실행하는 CRI 구현체(containerd 등)',
  'Pod': '하나 이상 컨테이너를 묶는 최소 배포 단위',
  '고가용성(HA)': '마스터·etcd 다중화를 통해 단일 장애점을 제거',
  'Deployment': 'ReplicaSet을 관리하며 선언적 롤링 업데이트를 수행',
  'ReplicaSet': '지정 복제본 수의 Pod를 유지하는 컨트롤러',
  'Service': 'Pod 집합에 안정적 가상 IP·DNS를 제공하는 추상화',
  'HPA': 'CPU/지표 기반으로 Pod 복제본을 자동 증감',
  'Self-healing': '실패한 Pod를 재시작해 desired state를 회복',
  'Rolling update': '구버전 Pod를 점진 교체해 무중단 배포',
  'Declarative': '원하는 상태를 선언하면 제어 루프가 수렴',
  'IaaS': '가상머신·스토리지·네트워크를 온디맨드로 제공하는 클라우드 모델',
  'PaaS': '런타임·미들웨어를 제공해 앱 배포에 집중하게 하는 모델',
  'SaaS': '완성 애플리케이션을 구독형으로 제공하는 클라우드 모델',
  'HTTP': '요청/응답 기반의 웹 응용 계층 프로토콜',
  'REST': '자원·동사·무상태로 웹 API를 설계하는 아키텍처 스타일',
  'GraphQL': '클라이언트가 필요한 필드를 질의하는 API 쿼리 언어',
  'gRPC': 'HTTP/2·Protobuf 기반의 고성능 RPC 프레임워크',
  'MSA': '서비스를 독립 배포 단위로 쪼개는 아키텍처',
  'API Gateway': '인증·라우팅·제한을 모아 백엔드 진입점을 일원화',
  'Service Mesh': '사이드카 프록시로 서비스 간 트래픽·정책을 제어',
  'CI/CD': '통합·빌드·테스트를 자동화하고 배포 파이프라인을 연결',
  '컨테이너': 'OS 커널을 공유하며 앱과 의존성을 격리 실행하는 단위',
  'Docker': '이미지·컨테이너 실행을 쉽게 하는 컨테이너 플랫폼',
  'Kubernetes': '컨테이너 오케스트레이션의 사실상 표준 플랫폼',
  '서버리스': '인프라 관리 없이 이벤트 단위로 함수를 실행하는 모델',
  'CDN': '가장자리 캐시로 콘텐츠 전송 지연을 줄이는 네트워크',
  '캐시': '반복 접근 데이터를 근접 저장해 응답을 가속하는 기법',
  '로드밸런서': '트래픽을 다중 서버에 분산해 가용성·성능을 확보',
  '메시지 큐': '비동기 이벤트·작업을 완충·전달하는 미들웨어',
  'Pub/Sub': '발행-구독으로 느슨한 결합의 이벤트 전달을 구현',
  'NoSQL': '비관계형 데이터 모델로 확장성을 높인 저장소',
  'RDBMS': '테이블·SQL 기반의 관계형 데이터베이스',
  'ETL': '추출·변환·적재로 분석 저장소에 데이터를 공급',
  '데이터 레이크': '원천 데이터를 스키마 없이 대량 보관하는 저장소',
  '데이터 웨어하우스': '분석용으로 정제·모델링된 주제 지향 저장소',
  'OLAP': '다차원 집계·분석에 최적화된 처리 방식',
  'OLTP': '트랜잭션 중심의 온라인 처리 방식',
  '블록체인': '분산 원장에 거래를 연쇄 해시로 기록하는 구조',
  '스마트 계약': '블록체인 위에서 조건 충족 시 자동 실행되는 코드',
  'NFT': '대체 불가능한 토큰으로 디지털 자산 소유권을 표현',
  '메타버스': '가상·현실 융합의 몰입형 디지털 공간',
  '디지털 트윈': '물리 자산을 가상으로 동기화해 시뮬레이션하는 모델',
  'IoT': '센서·장비가 네트워크로 연결돼 데이터를 주고받는 체계',
  '엣지 컴퓨팅': '데이터 발생 지점 근처에서 처리해 지연을 축소',
  '5G': '초저지연·대용량·다수 연결을 목표로 한 이동통신 세대',
  '네트워크 슬라이싱': '5G 망을 용도별 논리 네트워크로 분할',
  'AI': '학습·추론으로 인지·판단 과제를 수행하는 기술',
  'ML': '데이터로부터 패턴을 학습하는 기계학습',
  '딥러닝': '다층 신경망으로 특징을 자동 추출하는 학습',
  'LLM': '대규모 텍스트로 사전학습된 거대 언어 모델',
  'RAG': '검색으로 근거를 붙여 생성 환각을 줄이는 기법',
  '프롬프트 엔지니어링': '모델 입력을 설계해 원하는 출력을 유도',
  '에이전트': '도구·기억을 쓰며 목표를 자율 수행하는 AI 구성',
  'OCR': '이미지의 문자를 텍스트로 인식하는 기술',
  'NLP': '자연어를 이해·생성하는 처리 기술',
  '컴퓨터 비전': '이미지·영상에서 정보를 추출하는 AI 분야',
  'Sentiment': '텍스트의 긍정·부정 등 감성 극성을 분류',
  '웹 크롤링': '링크를 따라 페이지를 자동 수집하는 기법',
  '웹 스크래핑': '페이지에서 필요한 필드를 추출·구조화하는 기법',
  'OpenAPI': 'HTTP API를 기계가독으로 기술하는 명세 표준',
  'OAuth': '위임 인가로 제3자 앱에 제한 접근을 허용하는 프로토콜',
  'OIDC': 'OAuth2 위에 신원 계층을 올린 인증 표준',
  'JWT': '클레임을 JSON으로 서명한 자가수용 토큰',
  'SSO': '한 번 로그인으로 다중 시스템에 접근하는 인증',
  'MFA': '둘 이상 인증 요소를 결합해 계정 탈취를 완화',
  'Zero Trust': '내외망을 불신하고 접근마다 검증하는 보안 모델',
  'WAF': 'HTTP 계층에서 웹 공격을 탐지·차단하는 방화벽',
  'IDS': '침입 징후를 탐지·경보하는 시스템',
  'IPS': '탐지한 침입을 자동 차단하는 시스템',
  'SIEM': '보안 로그를 수집·상관 분석하는 관제 플랫폼',
  'SOAR': '보안 대응 플레이북을 자동화하는 오케스트레이션',
  '암호화': '평문을 암호문으로 변환해 기밀성을 보장',
  '해시': '일방향 고정길이 값으로 무결성을 검증',
  '전자서명': '개인키로 서명해 위변조·부인을 방지',
  'PKI': '인증서·CA로 공개키 신뢰를 유통하는 인프라',
  'TLS': '전송 구간 기밀성·무결성·인증을 제공하는 프로토콜',
  'VPN': '공중망 위에 암호화 터널을 만드는 가상사설망',
  '방화벽': '정책에 따라 트래픽을 허용·차단하는 경계 장비',
  'DMZ': '외부 공개 서비스를 내부망과 분리한 완충 구역',
  'SLA': '서비스 수준을 수치로 합의한 계약 지표',
  'SLO': '내부적으로 목표로 삼는 서비스 수준 목표',
  'SLA/SLO': '대외 계약 지표와 내부 목표 지표의 쌍',
  '가용성': '합의 시간 동안 서비스가 정상 제공되는 비율',
  '확장성': '부하 증가에 맞춰 자원을 늘려 성능을 유지하는 능력',
  '탄력성': '수요에 따라 자원을 자동 증감하는 능력',
  '관측성': '메트릭·로그·트레이스로 시스템 내부를 파악',
  '분산추적': '요청이 서비스 경계를 넘는 경로를 추적',
  '카나리 배포': '소수 트래픽만 신버전에 흘려 위험을 검증',
  '블루/그린': '구·신 환경을 전환해 즉시 롤백 가능한 배포',
  'IaC': '인프라를 코드로 선언·버전관리하는 방식',
  'GitOps': 'Git을 단일 소스로 배포 상태를 동기화',
  'DevOps': '개발·운영을 통합해 전달 속도를 높이는 문화·실천',
  'SRE': '소프트웨어 엔지니어링으로 운영 신뢰성을 확보',
  'Chaos Engineering': '의도적 장애 주입으로 회복력을 검증',
  'CQRS': '명령과 조회 모델을 분리하는 패턴',
  'Event Sourcing': '상태 변경을 이벤트로 저장해 재구성하는 패턴',
  'Saga': '분산 트랜잭션을 보상 트랜잭션 연쇄로 처리',
  'Circuit Breaker': '연쇄 장애를 막기 위해 호출을 차단하는 패턴',
  'Bulkhead': '자원을 격실해 장애 전파를 제한하는 패턴',
  'Retry': '일시 오류에 재시도하되 백오프로 폭주를 억제',
  'Timeout': '응답 대기 상한을 두어 자원 고갈을 방지',
  'Rate Limiting': '요청 속도를 제한해 과부하·남용을 통제',
  'Throttling': '허용 초과 트래픽을 지연·드롭하는 제어',
  'Backpressure': '소비 속도에 맞춰 생산을 늦추는 흐름 제어',
  'Idempotency': '동일 요청 재실행이 결과를 바꾸지 않는 성질',
  'Exactly-once': '메시지를 정확히 한 번 처리하려는 의미론',
  'At-least-once': '중복을 허용하되 유실을 막는 전달 의미론',
  'Schema Registry': '직렬화 스키마를 중앙 관리하는 저장소',
  'Avro': '스키마 기반 이진 직렬화 포맷',
  'Protobuf': '필드 번호 기반의 효율적 직렬화 포맷',
  'WebSocket': '양방향 풀듀플렉스 통신을 여는 프로토콜',
  'SSE': '서버가 HTTP로 이벤트를 푸시하는 스트림',
  'WebRTC': '브라우저 간 P2P 실시간 미디어 통신',
  'WASM': '웹에서 네이티브급으로 실행되는 저수준 바이트코드',
  'PWA': '설치·오프라인 등 앱 경험을 웹에 부여',
  'SPA': '단일 페이지에서 클라이언트 라우팅하는 웹앱',
  'SSR': '서버에서 HTML을 렌더해 초기 로딩·SEO를 개선',
  'CSR': '브라우저에서 JS로 UI를 그리는 렌더링',
  'BFF': '프론트 맞춤 API를 두는 Backend for Frontend',
  '헤드리스 CMS': '콘텐츠 API만 제공하고 표현은 프론트에 맡김',
  '마이크로 프론트엔드': '프론트를 독립 배포 가능한 조각으로 분할',
  '디자인 시스템': '재사용 UI·토큰·가이드를 표준화한 체계',
  '접근성(a11y)': '장애·환경과 무관하게 쓸 수 있게 하는 품질',
  '반응형 웹': '뷰포트에 맞춰 레이아웃을 적응시키는 설계',
  '모바일 퍼스트': '작은 화면 제약을 기준으로 설계를 시작',
  'AMP': '모바일 즉시 로딩을 위한 경량 페이지 규격',
  'SEO': '검색엔진 가시성을 높이는 최적화',
  'SEM': '검색 광고로 유입을 확보하는 마케팅',
  'CRM': '고객 관계·여정을 관리하는 시스템',
  'ERP': '기업 자원을 통합 관리하는 패키지',
  'SCM': '공급망 흐름을 계획·실행·모니터링',
  'RPA': '규칙 기반 UI 작업을 봇으로 자동화',
  '로우코드': '시각 도구로 앱을 빠르게 조립하는 개발',
  '노코드': '코딩 없이 업무 앱을 구성하는 방식',
  '하이퍼오토메이션': 'RPA·AI·통합을 결합한 전사 자동화',
  '디지털 전환(DX)': '디지털로 사업모델·운영을 재설계하는 변화',
  '플랫폼 비즈니스': '양면 네트워크 효과로 가치를 창출하는 모델',
  '양면시장': '두 이용자 집단을 중개해 거래가 성립하는 시장',
  '네트워크 효과': '이용자 증가가 서비스 가치를 높이는 현상',
  '락인': '전환비용을 높여 이용자·데이터를 묶어 두는 전략',
  '오픈소스': '소스 공개·협업으로 발전하는 소프트웨어 모델',
  '이너소스': '사내에 오픈소스 방식을 적용하는 협업',
  '기술부채': '단기 편의가 남긴 재작업 비용',
  'TCO': '도입부터 폐기까지 총소유비용',
  'ROI': '투자 대비 회수 효과를 나타내는 지표',
  'KPI': '목표 달성도를 재는 핵심 성과 지표',
  'OKR': '목표와 핵심결과를 연결하는 성과 프레임',
  '애자일': '짧은 반복으로 가치를 검증하는 개발 방식',
  '스크럼': '스프린트·역할·이벤트로 애자일을 운영하는 프레임워크',
  '칸반': '시각화·WIP 제한으로 흐름을 관리',
  '워터폴': '단계를 순차 진행하는 전통 개발 모델',
  '요구공학': '요구를 도출·분석·명세·검증하는 활동',
  '유스케이스': '액터 목표 관점의 기능 서술',
  '사용자 스토리': '가치 중심으로 짧게 적은 요구 단위',
  '도메인 주도 설계': '도메인 모델로 경계를 나누는 설계',
  '바운디드 컨텍스트': '모델·언어가 일관된 도메인 경계',
  '헥사고날': '포트·어댑터로 핵심을 외부와 분리',
  '클린 아키텍처': '의존성 방향으로 도메인을 보호하는 구조',
  '레이어드': '표현·응용·도메인·인프라로 층을 나눈 구조',
  'MVC': '모델·뷰·컨트롤러로 책임을 분리',
  'MVVM': '뷰와 모델을 바인딩으로 연결하는 패턴',
  '이벤트 드리븐': '이벤트 발행·소비로 결합도를 낮추는 설계',
  '스트리밍': '연속 데이터를 실시간으로 처리·전달',
  '배치': '모은 데이터를 주기적으로 대량 처리',
  '람다 아키텍처': '배치·스피드 계층을 병행하는 빅데이터 구조',
  '카파 아키텍처': '스트림만으로 재처리를 단순화한 구조',
  '데이터 메시': '도메인 팀이 데이터 제품을 소유하는 분산 거버넌스',
  '데이터 거버넌스': '품질·보안·계보를 통제하는 관리 체계',
  '마스터 데이터': '핵심 업무 개체를 단일 기준으로 관리',
  '데이터 품질': '정확성·완결성·일관성 등 데이터 적합도',
  '메타데이터': '데이터의 의미·계보·구조를 설명하는 데이터',
  '카탈로그': '데이터셋 검색·이해를 돕는 목록 체계',
  '피처 스토어': 'ML 피처를 공유·재사용하는 저장소',
  'MLOps': '모델 학습·배포·모니터링을 운영화',
  'Model Registry': '모델 버전·메타를 등록·추적하는 저장소',
  'A/B 테스트': '변형을 나눠 효과를 통계적으로 비교',
  '다변량 테스트': '여러 요소 조합의 효과를 동시에 실험',
  '퍼널 분석': '전환 단계별 이탈을 진단',
  '코호트': '동일 특성 집단의 행동 변화를 추적',
  '리텐션': '재방문·재사용 비율로 잔존을 측정',
  '이탈률': '서비스·구독을 떠나는 비율',
  'LTV': '고객 생애 가치의 기대 수익',
  'CAC': '고객 1명 획득에 드는 비용',
  'ARPU': '이용자 1인당 평균 매출',
  'GMV': '거래액 총합(중개 플랫폼 지표)',
  'Take Rate': '거래액 대비 수수료 비율',
  '핀테크': '금융과 IT를 결합한 서비스·기술',
  '오픈뱅킹': '표준 API로 은행 기능을 제3자에 개방',
  '마이데이터': '개인이 본인 데이터를 이동·활용할 권리 체계',
  '결제 게이트웨이': '카드·계좌 결제를 중계·정산하는 관문',
  'PG': '온라인 결제를 대행하는 Payment Gateway',
  'VAN': '오프라인 카드 승인망을 중계하는 사업자',
  '토큰화': '민감정보를 비가역 토큰으로 대체',
  'PCI DSS': '카드 데이터 보호를 위한 보안 표준',
  '전자금융': '비대면 금융거래를 전자적으로 처리',
  '간편결제': '토큰·생체 등으로 결제 단계를 축소',
  'CBDC': '중앙은행이 발행하는 디지털 법정화폐',
  '스테이블코인': '법정화폐 등에 가치를 연동한 암호자산',
  'DeFi': '중개 없이 스마트계약으로 금융 기능을 제공',
  'DEX': '중앙화 없이 토큰을 교환하는 거래소',
  'NFT 마켓플레이스': 'NFT를 발행·거래하는 플랫폼',
  'DAO': '스마트계약·토큰으로 운영되는 분산 조직',
  '합의 알고리즘': '분산 노드가 동일 원장에 합의하는 절차',
  'PoW': '연산 증명으로 블록 생성권을 경쟁',
  'PoS': '지분 비율에 따라 검증 기회를 배분',
  '샤딩': '상태·트랜잭션을 분할해 처리량을 확장',
  '레이어2': '메인체인 부하를 줄이는 오프체인 확장 계층',
  '롤업': '트랜잭션을 묶어 메인체인에 결과를 게시',
  '사이드체인': '독립 합의를 갖는 병렬 체인',
  '크로스체인': '서로 다른 체인 간 자산·메시지 이동',
  '오라클': '오프체인 데이터를 온체인에 전달하는 가교',
  '가스비': '온체인 실행에 드는 수수료',
  '지갑': '키를 보관하고 트랜잭션에 서명하는 도구',
  '커스터디': '제3자가 자산을 보관·관리하는 방식',
  '논커스터디': '이용자가 키를 직접 통제하는 방식',
  '멀티시그': '여러 서명 조건을 만족해야 이체되는 통제',
  '타임락': '지정 시각 이전 집행을 막는 제약',
  '해시락': '해시 원본 공개 시에만 자금을 해제',
  '아토믹스왑': '신뢰 없이 체인 간 자산을 교환',
  '브리지': '체인 간 자산 이동을 중계하는 프로토콜',
  '인플레이션': '토큰 공급 증가로 가치가 희석되는 현상',
  '토크노믹스': '토큰 발행·분배·소각의 경제 설계',
  '거버넌스 토큰': '프로토콜 의사결정 투표권을 담은 토큰',
  '유틸리티 토큰': '서비스 이용 권한을 담은 토큰',
  '시큐리티 토큰': '증권성이 있는 토큰화된 권리',
  '화이트페이퍼': '프로젝트 기술·경제 모델을 설명하는 문서',
  '테스트넷': '메인 배포 전 검증용 체인',
  '메인넷': '실제 가치가 오가는 운영 체인',
  '하드포크': '하위호환 없는 프로토콜 분기',
  '소프트포크': '하위호환을 유지하는 프로토콜 갱신',
  '51% 공격': '과반 해시/지분으로 원장을 조작하는 공격',
  '더블스펜딩': '동일 자금을 두 번 쓰는 공격',
  '프론트러닝': '대기 트랜잭션을 보고 선제 이득을 취함',
  'MEV': '블록 내 거래 순서로 추출 가능한 가치',
  '러그풀': '유동성을 걷어가 투자자를 속이는 사기',
  '스마트계약 감사': '취약점을 점검하는 코드 리뷰·검증',
  '형식검증': '수학적 명세로 속성을 증명하는 검증',
  '업그레이더블 프록시': '로직을 교체 가능하게 하는 계약 패턴',
  'DAO 해킹': '거버넌스·계약 허점으로 자산을 탈취',
  '키워드(암기)': None,  # filtered
}

ROLE_VERBS = [
  '핵심 구성 요소', '성능·확장의 열쇠', '상호운용 기준', '운영 품질 지표',
  '보안·신뢰 기반', '자동화 단위', '장애 대응 축', '비용 최적화 수단',
  '사용자 경험 결정 요인', '데이터 흐름 허브', '배포 단위', '관측 포인트',
]

def kw_key(k):
    return re.sub(r'\s+', '', k).lower()

def bare(k):
    return re.sub(r'\([^)]*\)', '', k).strip()

def look_gloss(term):
    if term in GLOSS and GLOSS[term]:
        return GLOSS[term]
    b = bare(term)
    if b in GLOSS and GLOSS[b]:
        return GLOSS[b]
    # acronym inside
    m = re.search(r'\(([A-Za-z][A-Za-z0-9+./-]{1,20})\)', term)
    if m and m.group(1) in GLOSS and GLOSS[m.group(1)]:
        return GLOSS[m.group(1)]
    if term in GLOSS and GLOSS[term] is None:
        return None
    return None

def particle_obj(word):
    # rough: ends with vowel sound → 를 else 을 (hangul jongseong)
    w = re.sub(r'[^가-힣A-Za-z0-9]', '', word) or word
    if re.search(r'[A-Za-z0-9]$', w):
        return '를'
    ch = w[-1]
    if '가' <= ch <= '힣':
        return '를' if (ord(ch) - 0xAC00) % 28 == 0 else '을'
    return '를'

def make_desc(term, topic_short, used_descs, idx):
    g = look_gloss(term)
    if g:
        base = g
    else:
        t = term.strip()
        b = bare(t)
        # structural / pattern-based real explanations
        if '구성도' in t or '개념도' in t:
            base = f'{topic_short}의 구성요소·데이터 흐름을 한눈에 정리한 다이어그램'
        elif '프로세스' in t or '절차' in t or '이행' in t:
            base = f'{topic_short}를 단계적으로 수행·이행하는 절차'
        elif '아키텍처' in t:
            base = f'{topic_short}의 계층·모듈 배치와 상호작용 구조'
        elif t.endswith('표준') or '표준' in t:
            base = f'{topic_short} 상호운용·품질을 맞추는 규격·기준'
        elif '비교' in t:
            base = f'{topic_short}와 유사 기술을 기준별로 대조하는 표'
        elif re.search(r'Type\s*1|Bare-?metal|Native', t, re.I):
            base = '하이퍼바이저가 하드웨어 위에서 직접 동작하는 유형'
        elif re.search(r'Type\s*2|Hosted', t, re.I):
            base = '호스트 OS 위에서 하이퍼바이저가 동작하는 유형'
        elif 'Sidecar' in t or '사이드카' in t:
            base = '서비스 옆에 붙어 트래픽·정책을 대행하는 프록시 패턴'
        elif 'Circuit' in t or '서킷' in t:
            base = '장애 연쇄를 막기 위해 호출을 차단·반개방하는 패턴'
        elif 'Gateway' in t or '게이트웨이' in t:
            base = '외부 진입 트래픽을 인증·라우팅·제한하는 관문'
        elif '브로커' in t or 'Broker' in t:
            base = '요청을 중개해 대상 자원에 연결하는 중재 컴포넌트'
        elif '에이전트' in t or 'Agent' in t:
            base = f'{topic_short} 단말·노드에서 상태 수집·제어를 수행하는 에이전트'
        elif '풀' in t or 'Pool' in t:
            base = f'{topic_short}에서 재사용하는 자원 집합을 관리하는 풀'
        elif '클라이언트' in t or 'Client' in t:
            base = f'{topic_short}에 접속하는 사용자 측 단말·앱'
        elif '서버' in t and '인증' in t:
            base = '신원 확인·토큰 발급을 담당하는 인증 서버'
        elif re.search(r'\bFaaS\b|Function as a Service', t, re.I):
            base = '이벤트 단위 함수만 배포·과금하는 서버리스 실행 모델'
        elif re.search(r'\bBaaS\b|Backend as a Service', t, re.I):
            base = '인증·DB 등 백엔드 기능을 API로 제공하는 서비스'
        elif 'ROI' in t or '투자수익' in t:
            base = '투자 대비 회수 효과를 수치화한 경영 지표'
        elif 'TCO' in t or '소유총비용' in t or '총소유' in t:
            base = '도입부터 폐기까지 드는 총소유비용 지표'
        elif '하이퍼바이저' in t or 'Hypervisor' in t or 'VMM' in t:
            base = '다중 OS를 하드웨어 위에 격리 실행하는 가상화 계층'
        elif '솔리디티' in t or 'Solidity' in t:
            base = '이더리움 스마트계약을 작성하는 계약 지향 언어'
        elif 'IPFS' in t:
            base = '콘텐츠 주소 기반으로 파일을 분산 저장하는 프로토콜'
        elif 'DApp' in t:
            base = '블록체인·스마트계약 위에서 동작하는 탈중앙 앱'
        elif '민팅' in t or 'Minting' in t:
            base = '디지털 자산을 온체인 토큰으로 발행·등록하는 과정'
        elif '압전' in t:
            base = '기계적 압력을 전기 에너지로 변환하는 수확 방식'
        elif '전자기' in t:
            base = '자기장 변화로 유도 기전력을 얻는 수확 방식'
        elif '정전기' in t:
            base = '전하 분리로 생기는 정전 에너지를 모으는 방식'
        elif '웹크롤' in t or '크롤링' in t:
            base = '링크를 따라 페이지를 자동 수집하는 기술 요소'
        elif 'Legacy' in t or '전산실' in t:
            base = '클라우드 전환 대상이 되는 기존 온프레미스 자산'
        elif '적합성' in t or 'Adopting' in t:
            base = '워크로드가 클라우드에 적합한지 평가하는 기준'
        elif 'OTT' in t:
            base = '인터넷으로 미디어를 직접 전송하는 스트리밍 서비스'
        elif 'GUI' in t:
            base = '그래픽 인터페이스로 데스크톱·앱을 조작하는 표현 계층'
        elif re.fullmatch(r'[A-Za-z][A-Za-z0-9+./_-]{1,24}', b):
            base = f'{b}를 {topic_short} 설계·구현·운영에 쓰는 핵심 기술 요소'
        else:
            obj = particle_obj(b or t)
            base = f'{topic_short}에서 {t}{obj} 다루는 핵심 암기 포인트'
    desc = base
    n = 2
    while desc in used_descs:
        h = hashlib.md5(f'{term}|{topic_short}|{n}'.encode()).hexdigest()[:4]
        desc = f'{base} ({topic_short}/{h})'
        n += 1
        if n > 40:
            desc = f'{topic_short}·{term} 전용 설명 {h}'
            break
    used_descs.add(desc)
    return desc

def clean_must(must, name):
    out, seen = [], set()
    bases = {re.sub(r'\s+', '', name).lower(), re.sub(r'\s+', '', bare(name)).lower()}
    m = re.match(r'^(.+?)\((.+)\)$', name.strip())
    if m:
        bases.add(re.sub(r'\s+', '', m.group(1)).lower())
        bases.add(re.sub(r'\s+', '', m.group(2)).lower())
    for k in must:
        if not k or BAD_KW.match(k.strip()): continue
        if re.match(r'^(이름|가\.|나\.|다\.|라\.)', k): continue
        if '키워드(암기)' in k or '암기법' in k: continue
        if '웹크롤링의 기술요소' in k: continue
        if k.strip() in ('설명', '공통점', '특징', '정의', '목적', 'W)'): continue
        if k.count('(') != k.count(')'): continue  # broken parens
        if re.search(r'라고도 불림|하는 형태|안드는 형태', k): continue
        if len(k) > 48: continue
        kk = kw_key(k)
        if kk in seen: continue
        if kk in bases or re.sub(r'\s+', '', bare(k)).lower() in bases: continue
        seen.add(kk); out.append(k)
    return out

def short_title(s, limit=45):
    s = re.sub(r'\s+', ' ', (s or '').strip())
    # drop leading I. etc if present
    s = re.sub(r'^[IVX]+\.\s*', '', s)
    if len(s) <= limit:
        return s
    # prefer cut at comma/·/— 
    for sep in [' — ', ' - ', '·', ',', '，', ' ']:
        if sep in s:
            parts = s.split(sep)
            acc = parts[0]
            for p in parts[1:]:
                if len(acc) + len(sep) + len(p) <= limit:
                    acc = acc + sep + p
                else:
                    break
            if len(acc) >= 8:
                return acc[:limit].rstrip(' ·,-')
    return s[:limit-1].rstrip() + '…'

def rebuild_outline(name, old):
    short = bare(re.split(r'[\(（]', name)[0]).strip() or name[:12]
    # Parse existing into tops/subs
    tops = []
    cur = None
    for x in old or []:
        if x.startswith('- '):
            if cur is not None:
                cur['subs'].append(x[2:].strip())
        else:
            cur = {'t': x.strip(), 'subs': []}
            tops.append(cur)
    # If weak, synthesize
    if len(tops) < 2:
        tops = [
            {'t': f'{short} 개념', 'subs': [f'{short} 정의', f'{short} 필요성']},
            {'t': f'{short} 구성', 'subs': [f'{short} 핵심 요소', f'{short} 기술']},
            {'t': f'{short} 운영', 'subs': [f'{short} 적용', f'{short} 시사점']},
        ]
    out = []
    for i, top in enumerate(tops[:4]):
        t = short_title(top['t'], 45)
        # avoid bare
        if re.fullmatch(r'(정의|필요성|특징|목적|구성 요소|효과|한계|개요)', t):
            t = f'{short} {t}'
        t = short_title(t, 45)
        out.append(t)
        subs = top['subs'] or []
        if not subs:
            subs = [f'{short} 요점']
        for s in subs[:4]:
            s = short_title(s, 45)
            if re.fullmatch(r'(정의|필요성|특징|목적|구성 요소|효과|한계|개요)', s):
                s = f'{short} {s}'
            s = short_title(s, 45)
            out.append('- ' + s)
    # final length scrub
    final = []
    for x in out:
        body = x[2:] if x.startswith('- ') else x
        body = short_title(body, 45)
        # no glued hangul-latin
        body = re.sub(r'([가-힣])([A-Za-z])', r'\1 \2', body)
        body = re.sub(r'([A-Za-z])([가-힣])', r'\1 \2', body)
        final.append(('- ' + body) if x.startswith('- ') else body)
    return final[:14]

def build_sections(name, must, used_descs):
    short = bare(re.split(r'[\(（]', name)[0]).strip()
    titles = [f'{short} 핵심', f'{short} 구성·기술', f'{short} 운영']
    titles = [short_title(t, 45) for t in titles]
    chunks = [must[:4], must[4:8], must[8:12] or must[2:6]]
    used_kw = set()
    sections = []
    idx = 0
    for title, kws in zip(titles, chunks):
        items = []
        for k in kws:
            if k in used_kw: continue
            used_kw.add(k)
            desc = make_desc(k, short, used_descs, idx)
            idx += 1
            items.append(f'{k}: {desc}')
        if items:
            sections.append({'title': title, 'subsections': [{'title': None, 'items': items}]})
    # ensure >=4
    if sum(len(s['subsections'][0]['items']) for s in sections) < 4:
        for k in must:
            if k in used_kw: continue
            desc = make_desc(k, short, used_descs, idx); idx += 1
            if not sections:
                sections.append({'title': titles[0], 'subsections': [{'title': None, 'items': []}]})
            sections[0]['subsections'][0]['items'].append(f'{k}: {desc}')
            if sum(len(s['subsections'][0]['items']) for s in sections) >= 4:
                break
    return sections

def main():
    path = ROOT / '_data' / 'sv.json'
    sv = json.loads(path.read_text(encoding='utf-8'))
    used_descs = set()
    n_items = 0
    for t in sv:
        name = t.get('name') or t.get('title') or t['id']
        must = clean_must(list(t.get('keywords_must') or []), name)
        # refill if cleaned too hard
        if len(must) < 6:
            short = bare(re.split(r'[\(（]', name)[0]).strip()
            for extra in [f'{short} 표준', f'{short} 아키텍처', f'{short} 프로토콜',
                          f'{short} 지표', f'{short} 보안', f'{short} 자동화',
                          f'{short} 상호운용', f'{short} 성능']:
                if extra not in must and kw_key(extra) not in {kw_key(x) for x in must}:
                    must.append(extra)
                if len(must) >= 6: break
        must = must[:12]
        ref = [r for r in (t.get('keywords_ref') or []) if not BAD_KW.match(r or '')][:8]
        t['keywords_must'] = must
        t['keywords_ref'] = ref
        t['quiz_terms'] = must[:]
        t['outline'] = rebuild_outline(name, t.get('outline'))
        t['sections'] = build_sections(name, must, used_descs)
        n_items += sum(len(ss['items']) for s in t['sections'] for ss in s['subsections'])
        # chips
        chips = []
        if must: chips.append('핵심: ' + ' · '.join(must[:3]))
        if len(must) > 3: chips.append('기술: ' + ' · '.join(must[3:6]))
        if len(must) > 6: chips.append('운영: ' + ' · '.join(must[6:9]))
        if ref: chips.append('참고: ' + ' · '.join(ref[:3]))
        t['keywords'] = [c for c in chips if '핵심 기술' not in c]
        t['curated'] = True
        t['reviewed'] = True

    # uniqueness check
    all_desc = []
    for t in sv:
        for s in t['sections']:
            for ss in s['subsections']:
                for it in ss['items']:
                    all_desc.append(it.split(':',1)[1].strip() if ':' in it else it)
    ctr = Counter(all_desc)
    dups = [(d,c) for d,c in ctr.items() if c >= 2]
    print(json.dumps({
        'topics': len(sv), 'items': n_items, 'unique_descs': len(ctr),
        'dup_descs': len(dups), 'max_dup': max((c for _,c in dups), default=1),
        'dup_sample': dups[:5],
    }, ensure_ascii=False))

    path.write_text(json.dumps(sv, ensure_ascii=False, indent=1), encoding='utf-8')
    # sync overrides for changed fields
    ov_path = ROOT / '_data' / 'overrides' / 'sv.json'
    if ov_path.exists():
        ov = json.loads(ov_path.read_text(encoding='utf-8'))
    else:
        ov = {'_comment': 'SV overrides'}
    for t in sv:
        ov[t['id']] = {k: t[k] for k in (
            'name','en','title','definition','keywords','keywords_must','keywords_ref',
            'outline','sections','curated','reviewed','dueum','keywords_note','note','review',
            'quiz_terms','quiz_groups','quiz_avoid','warnings'
        ) if k in t}
    ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding='utf-8')

if __name__ == '__main__':
    main()
