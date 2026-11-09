# NW 단어장 사실 검토 (중간 보고, 2026-11-09)

상태: 레이아웃 작업(한 화면, 목차, 알아요/몰라요 제거)은 반영 완료. 아래 사실 오류는 **찾아만 둔 것이고 아직 `_data/overrides/nw.json`에 반영하지 않음**.
분류: A 사실 오류 / B 구버전 / C 모호·참고 / D 파싱 깨짐

## A. 사실 오류 (수정 필요)
| 토픽 | PDF 내용 | 바른 내용 | 근거 |
|---|---|---|---|
| NW_026 DNS | Domain Name **Server** | Domain Name **System** | RFC 1034/1035 |
| NW_032 Multicast | 정의 "모든 사용자에게" 전달 / 키워드 "225~239: 라우팅" | 그룹에 가입한 수신자에게만 전달(모두에게는 브로드캐스트). 224.0.0.0/24는 링크 로컬 예약(라우팅 안 됨), 239/8은 관리 범위(사설) | RFC 5771, RFC 2365 |
| NW_041 Transport | 수신측이 CRC로 오류 프레임 재전송 요청 | TCP는 **체크섬** 사용, NAK 없이 ACK·타임아웃·3 dup ACK로 재전송 (CRC는 2계층) | RFC 9293 |
| NW_043 Data Link | 흐름제어(ARQ) | ARQ는 오류제어. 흐름제어는 Stop-and-Wait·Sliding Window | Forouzan, Tanenbaum |
| NW_046 TCP | 정의 "다수 프로토콜이 모인 4계층 프로토콜 집합" | TCP 자체는 연결지향·신뢰성 전송 프로토콜 하나(집합은 TCP/IP 스위트) | RFC 9293 |
| NW_056 VLSM | "RFC 1878이 VLSM 표준" / "C급 네트워크(128.3.2.0)" | RFC 1878은 정보용 서브넷 표(VLSM 개념은 RFC 1009), 128.x는 **B 클래스** | RFC 1009, 1878 |
| NW_059 단편화 | "IPv4 MTU 최소 권고값 576" | IPv4 최소 MTU는 68바이트, 576은 모든 호스트가 받아야 하는 재조립 크기. IPv6 최소 MTU 1280 | RFC 791, RFC 8200 |
| NW_062 IGMP | 호스트가 가입할 때 "멤버십 **문의**" 전송 | 가입할 때는 **Membership Report**, Query는 라우터가 보냄 | RFC 2236, RFC 3376 |
| NW_071 QUIC | 키워드 DTLS | DTLS가 아니라 **TLS 1.3 내장** | RFC 9001 |
| NW_082·NW_119 V2X | V2N = Vehicle to Nomadic device | V2N = Vehicle-to-**Network** | 3GPP TS 22.185 |
| NW_085_02 CAN | Bosch 1985년 개발 | 1983년 개발 시작, **1986년** SAE에서 발표 | Bosch, ISO 11898 |
| NW_099 Wi-Fi 8 | 최대속도 100Gbps | 최대 속도는 Wi-Fi 7과 같음. 목표는 Wi-Fi 7 대비 처리량 25%↑(같은 SINR), 95% 지연 25%↓, MPDU 손실 25%↓ | IEEE P802.11bn PAR |
| NW_101 WPA3 | "WPA 단점 보완해 AES 적용", "EAP 도입" | AES-CCMP·EAP는 WPA2부터. WPA3는 SAE·PMF 필수·192비트 모드(GCMP-256, P-384) | Wi-Fi Alliance WPA3 Spec |
| NW_106 CoAP | 물리계층 6LoWPAN | 물리/MAC은 IEEE 802.15.4, 6LoWPAN은 적응 계층 | RFC 7252, RFC 4944 |
| NW_127 터널링 | "수신자 외에는 알아볼 수 없게" | 터널링은 **캡슐화**이며 암호화는 필수가 아님(6in4·GRE). 기밀성은 IPsec 등이 담당 | RFC 4213, RFC 2784 |
| NW_181 PS-LTE | HSS = Home Subscriber **System** / Rel-12 2015.12 freezing | Home Subscriber **Server** / Rel-12는 2015년 3월 freeze | 3GPP |
| NW_184 RAN Sharing | 2021년 7월 전국 재난망 구축 | 2021년 3월 구축 완료, **5월 14일** 개통 | 행정안전부 2021.5.14 보도자료 |
| NW_185 5G | 체감 전송속도 100~1,000Mbps | IMT-2020 요구치는 **100Mbps** | ITU-R M.2410 |
| NW_188 NSA/SA | "두 구조 모두 단말이 4G·5G 동시 지원" | NSA는 LTE 앵커+NR(EN-DC), SA는 NR+5GC 단독 | 3GPP TS 37.340 |
| NW_206 내외부라우팅 | IGP "(Multicast)", EGP "(Unicast)" 표기 | 해당 구분은 근거 없음, 삭제 | RFC 4271 |
| NW_211 OSPF | 1990년 제정 / 메트릭에 Hop·Delay·Throughput 등 | OSPFv1 RFC 1131(1989), v2 RFC 2328. 메트릭은 **Cost**(참조 대역폭/인터페이스 대역폭) | RFC 2328 |
| NW_212_01 STP | Spinning Tree | **Spanning** Tree (IEEE 802.1D) | IEEE 802.1D |
| NW_240 O-RAN | O-DU를 "분배 역할"로, RRC/PDCP를 별도 요소로 설명 | O-DU = Distributed Unit(RLC/MAC/High-PHY), RRC/PDCP는 O-CU 기능 | O-RAN Alliance WG1 |
| NW_276 IBN | IETF NMRG | NMRG는 **IRTF** 연구 그룹(RFC 9315) | RFC 9315 |

## B. 구버전 (최신화 필요)
- NW_049: RTO = 2×RTT, 단순 EWMA → 현재는 RTO = SRTT + 4·RTTVAR, 최소 1초 (RFC 6298)
- NW_064 SCTP: RFC 4960 → **RFC 9260** (2022), 키워드 "HEATBEAT" 오타(D)
- NW_066 RARP: 현재는 DHCP로 대체 (RFC 903, 사실상 폐기)
- NW_069 DHCP: RFC 1541 → **RFC 2131** (1997)
- NW_071 QUIC: "IETF 표준 제안 계획" → **RFC 9000**(2021) 표준화, HTTP/3은 RFC 9114. 이제 QUIC은 약어가 아님
- NW_073 MPTCP: RFC 8684 (MPTCP v1)
- NW_082·NW_084·NW_119 V2X/WAVE: 국내 C-ITS는 2023년 12월 12일 **LTE-V2X 단일 방식**으로 결정됨(과기정통부·국토부). 미국 FCC는 2020년에 5.9GHz 상위 30MHz를 C-V2X에 배정. 후속 표준은 802.11bd(NGV)와 NR-V2X(Rel-16)
- NW_088 WLAN: WEP는 폐기 → WPA2/WPA3. 정의의 "OFMD"는 OFDM 오타(D)
- NW_107 MQTT: MQTT 5.0(OASIS 2019), ISO/IEC 20922
- NW_108 XMPP: RFC 3920/3921 → **RFC 6120/6121**
- NW_136/137 혼잡제어: AQM은 CoDel·PIE(RFC 7567), 리눅스 기본 CUBIC(RFC 9438), BBR
- NW_140 MPLS: CR-LDP 폐기(RFC 3468) → RSVP-TE. "ERP"는 ERO 오타(D)
- NW_142 QoE: PESQ → POLQA (ITU-T P.863)
- NW_147 Bluetooth: 최신은 6.0(2024, Channel Sounding). Mesh는 5.0이 아닌 별도 Mesh Profile. "기존 장비와 호환 불가"는 틀림(하위 호환, 신기능만 못 씀)
- NW_167 CA: Rel-10은 CC 최대 5개, Rel-13부터 **32개**까지 확장. "Infra-band"는 Intra-band 오타(D)
- NW_188: 국내 SA 상용화는 2021년 7월(KT)부터
- NW_189 MEC: ETSI가 2017년 Multi-access Edge Computing으로 이름 바꿈
- NW_191 6G: ITU-R M.2160(IMT-2030, 2023) 6대 사용 시나리오 추가 필요
- NW_192_0/1 이음5G: 4.7GHz(100MHz) 대역은 이미 공급됨("6GHz 이하 추후 검토"는 구버전)
- NW_197 망중립성: 미국은 2017년 폐지 후 2024년 복원했으나 2025년 1월 제6순회항소법원이 무효화함
- NW_199 디지털세: 필라2(최저한세 15%) 국내 시행은 2024년. 2025년 6월 G7이 미국 기업을 IIR/UTPR에서 빼는 side-by-side에 합의했고, 필라1은 사실상 중단됨
- NW_203/206 IGRP: 단종(EIGRP로 대체)
- NW_212_01: RSTP(802.1w)와 MSTP(802.1s, 802.1Q로 통합) 추가
- NW_234 OpenFlow: Header/Counter/Action은 1.0 기준. 1.1 이후는 Match/Priority/Counters/Instructions
- NW_238 OPNFV: 2021년 **Anuket**으로 통합(LF Networking)
- NW_275 SATIN: NTN은 Rel-17(2022)에서 표준화됨

## C. 모호·참고 (메모만)
NW_001 cross-entropy 표현 부정확 / NW_004_01 비교표 문장 뒤섞임(D 성격) / NW_012 "K>15"는 교재 예시(802.11은 retry limit 사용) / NW_031_02 NOMA는 5G NR 표준에 미채택 / NW_042 ISO/IEC 8208(X.25) 키워드 부적절 / NW_065 ARP 계층 논란(2.5계층) / NW_079 "스스로 차로 변경"은 V2V 기능 아님 / NW_083 국내 DSRC(5.8GHz 하이패스)와 미국 DSRC(5.9GHz) 구분 / NW_133 WFQ 확장성 문제의 원인은 플로우별 상태 / NW_150 NFC "해킹 원천 차단"은 과장(릴레이 공격) / NW_178 LTE-M(해상)과 LTE-M(Cat-M1 IoT) 명칭 혼동 주의 / NW_192_1 "표준 보안 취약점에 노출 안 됨"은 틀림(3GPP 5G 그대로 씀) / NW_198 대상 사업자 수는 연도별로 다름 / NW_201 Push/Pull 설명이 뒤섞임 / NW_212_00 EIGRP는 MTU를 메트릭 계산에 쓰지 않음 / NW_213과 NW_222 중복

## D. 파싱 깨짐·오타
NW_023_00(HTTP/PDA 문장 섞임), NW_073 제목 MTCP→MPTCP, NW_072 VRRS/HSRP 명칭, NW_132 QoS 요소 표, NW_150 동작방식 표, NW_187 "NR-MINO"→NR-MIMO, NW_190_00 "3Lt", NW_191 "1Tbs", 이 밖에 원문 발췌 bullet 다수(이제 기본 화면에서는 숨기고 "원문 발췌 보기"에서만 보임)

## ST(통계) 검토 메모
- ST_005: 원문 Precision(정확도) → 정밀도로 정정(정확도=Accuracy 구분)
- ST_014: probability "destiny" function → density로 정정
- ST_030/ST_031_00 가설검정 중복 토픽을 ST_030으로 통합
- ST_019_02: 중심극한정리로 정리(t/z 검정 비교는 ST_019에 서술)
- ST 리뷰: PDF 표·그림 키워드 반영(필수/참고 추가 23토픽·제거 23토픽·사실/표현 정정 14토픽). ST_043 원문의 VIF=1/(1−r), "결정계수 높아 과적합" → VIF=1/(1−Rj²), 계수 분산 증가로 정정. ST_042_01 이상치 유형을 원문 4유형(점·구간·패턴·추세)으로 정리

## SW 키워드 사실 검수 (2026-11-10)
- SW_261 임치제도: 사용자(수치인) → 사용자(이용자), 수치인=임치기관(협력재단·한국저작권위원회)
- SW_199 12207(1995): 224개 작업 → 232개 작업
- SW_212 McCabe: V(G)=영역 수+1 → 닫힌 영역 수+1
- SW_160 스모크: 회귀 테스트 부분집합 → 인수 테스트 부분집합(새니티가 회귀 부분집합)
- SW_153_1 알파·베타: 근거 없는 완료율(70~90%·90~95%) 삭제 → 통제/비통제 환경
- SW_194 25010 두음: 원문 두음(기신사효유이 + 보호)으로 복원
- SW_037/038/040: 불확실한 조문 번호(구 SW산업진흥법 제20조, 국가계약법 시행규칙 제84조, 진흥법 제50조-원격지) 제거
- SW_100/101/124_1/169_02/183/234/278: 사소한 예시·중복·부정확 키워드 교체(PageMaker·토핑, 글렌포드 마이어스, 역공학 중복, SWEBOK KA 정리 등)
- 약어 문맥 풀이: 41토픽 gloss 추가(ADR·ISP·LSP·MVC·MVP·OSS·PIM·PSM·TPS·SAM·PPP·EDM 등), 다의 약어 glossary 목록화
