/* 공통: 데이터 로드, 테마, 한 화면 맞춤, 서비스워커 */
(function () {
  const PE = window.PE;
  try { localStorage.removeItem('pe-status-v1'); localStorage.removeItem('pe-card-mode'); } catch (e) {}
  // 약어 사전(_data/glossary.yml → glossary.json)
  let GL = {}, GLRE = null;
  PE.loadGlossary = () => fetch(PE.base + '/glossary.json').then(r => r.json()).then(g => {
    GL = g || {}; const keys = Object.keys(GL).sort((a, b) => b.length - a.length).map(k => k.replace(/[.*+?^${}()|[\]\\\/-]/g, '\\$&'));
    GLRE = keys.length ? new RegExp('(?<![A-Za-z0-9-])(' + keys.join('|') + ')(?![A-Za-z0-9-])', 'g') : null;
  }).catch(() => {});
  PE.glTopic = null; // 지금 그리는 토픽(문맥별 약어 풀이용)
  PE.important = {};
  PE.loadImportant = () => fetch(PE.base + '/important.json').then(r => r.ok ? r.json() : {}).then(o => { PE.important = o || {}; }).catch(() => { PE.important = {}; });
  PE.isImportant = t => !!(t && PE.important[t.id]);
  PE.starHtml = t => PE.isImportant(t) ? '<span class="star" title="중요 토픽" aria-label="중요">★</span>' : '';
  PE.nameHtml = t => PE.starHtml(t) + PE.esc(PE.name(t));
  PE.load = () => Promise.all([fetch(PE.data).then(r => r.json()), PE.loadGlossary(), PE.loadImportant()]).then(([d]) => { PE.all = d; PE.resolveDomain(d); PE.buildDrawer(d); return d; });
  // 현재 도메인: URL ?d= → localStorage → 첫 도메인. 바꾸는 곳은 햄버거 메뉴(☰)뿐
  PE.setDomain = d => { PE.cur = d; try { localStorage.setItem('pe-dom', d); } catch (e) {} const el = document.getElementById('curDom'); if (el) el.textContent = ' · ' + d;
    document.querySelectorAll('[data-nav]').forEach(a => { const u = new URL(a.href, location.href); u.searchParams.set('d', d); a.href = u.pathname + u.search; }); };
  PE.resolveDomain = list => { const ds = PE.domains(list); let d = PE.params().get('d') || localStorage.getItem('pe-dom'); if (!ds.includes(d)) d = ds[0]; PE.setDomain(d); return d; };
  PE.inCur = t => t.domain === PE.cur;
  const metaOf = code => (PE.domainsMeta || []).find(m => m.code === code) || { code, name: code };
  PE.buildDrawer = list => {
    const body = document.getElementById('drawerBody'); if (!body) return;
    body.innerHTML = '<div class="dr-label">도메인</div>' + PE.domains(list).map(code => {
      const m = metaOf(code), ts = list.filter(t => t.domain === code), q = '?d=' + encodeURIComponent(code);
      return `<details class="dr-dom"${code === PE.cur ? ' open' : ''}><summary><b>${PE.esc(code)}</b> ${PE.esc(m.name)} <span class="dr-n">${ts.length}</span></summary>
        <div class="dr-links"><a href="${PE.url('/')}${q}">목록</a><a href="${PE.url('/cards/')}${q}">카드</a><a href="${PE.url('/quiz/')}${q}">서술</a></div>
        <ul class="dr-topics">${ts.map(t => `<li><a href="${PE.topicUrl(t.id)}&d=${encodeURIComponent(code)}"><span class="dr-id">${PE.esc(t.id)}</span> ${PE.nameHtml(t)}</a></li>`).join('')}</ul></details>`;
    }).join('');
  };
  const drawer = document.getElementById('drawer'), menuBtn = document.getElementById('menuBtn');
  const openDrawer = o => { if (!drawer) return; drawer.hidden = !o; menuBtn && menuBtn.setAttribute('aria-expanded', String(o)); document.documentElement.classList.toggle('dr-open', o);
    if (o) { const cur = drawer.querySelector('details[open] .dr-topics a[href*="id=' + (PE.params().get('id') || '#') + '&"]'); cur && (cur.classList.add('on'), cur.scrollIntoView({ block: 'center' })); } };
  menuBtn && menuBtn.addEventListener('click', () => openDrawer(drawer.hidden));
  drawer && drawer.addEventListener('click', e => { if (e.target.closest('[data-close]')) openDrawer(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') openDrawer(false); });
  // 텍스트를 escape하고, 약어 뒤에 정식 명칭을 작게 붙임(이미 괄호로 풀어 쓴 경우·같은 약어 반복은 생략)
  PE.gl = text => {
    const raw = String(text == null ? '' : text);
    if (!GLRE) return PE.esc(raw);
    const seen = new Set(); let out = '', last = 0;
    raw.replace(GLRE, (m, k, off) => {
      const after = raw.slice(off + m.length).trimStart();
      // 토픽별 풀이(t.gloss)가 우선. 사전 값이 목록(뜻 여러 개)이거나 '-'면 토픽에 지정이 없을 때 표시 안 함
      const tg = PE.glTopic && PE.glTopic.gloss; let full = tg && Object.prototype.hasOwnProperty.call(tg, k) ? tg[k] : GL[k];
      if (Array.isArray(full) || !full || full === '-') full = null;
      out += PE.esc(raw.slice(last, off + m.length)); last = off + m.length;
      // 바로 뒤 괄호가 이미 풀네임(같은 첫 글자로 시작하는 단어 포함)이면 생략, ISO/SAE처럼 '/'로 붙은 복합 표기는 생략
      const paren = after.startsWith('(') ? (after.match(/^\(([^)]*)\)/) || [, ''])[1] : null;
      const expanded = paren != null && new RegExp('(^|[^A-Za-z])' + k[0] + '[a-z]', 'i').test(paren);
      const slash = !k.includes('/') && (raw[off - 1] === '/' || raw[off + m.length] === '/');
      // GS리테일·LG전자처럼 약어 바로 뒤에 회사명 꼬리가 붙으면 회사명이라 풀이 생략
      const corp = /^(리테일|그룹|전자|텔레콤|유플러스|칼텍스|화학|에너지|디스플레이|이노텍|건설|홈쇼핑|증권|은행|생명|헬로비전|홀딩스)/.test(raw.slice(off + m.length));
      if (full && !seen.has(k) && !expanded && !slash && !corp && !raw.toLowerCase().includes(String(full).toLowerCase())) { out += `<small class="gl">(${PE.esc(full)})</small>`; seen.add(k); }
      return m;
    });
    return out + PE.esc(raw.slice(last));
  };
  PE.esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  PE.url = (path) => PE.base + path;
  PE.topicUrl = id => PE.base + '/topic/?id=' + encodeURIComponent(id);
  PE.params = () => new URLSearchParams(location.search);
  // 커리큘럼(주차) 순서: 경영전략 → 프로젝트관리 → 소공 → 디지털서비스 → 네트워크 → 보안 → DB → CA → OS → DS → 알고리즘 → AI → 통계
  PE.ORDER = ['MG', 'PM', 'SW', 'SV', 'NW', 'SE', 'DB', 'CA', 'OS', 'DS', 'AL', 'AI', 'ST'];
  PE.domains = list => Array.from(new Set(list.map(t => t.domain))).sort((a, b) => {
    const ia = PE.ORDER.indexOf(a), ib = PE.ORDER.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  PE.domainChips = (el, list, current, onChange) => {
    const ds = PE.domains(list);
    el.innerHTML = ['ALL'].concat(ds).map(d => `<button type="button" class="chip${d === current ? ' on' : ''}" data-domain="${d}">${d === 'ALL' ? '전체 도메인' : d}</button>`).join('');
    el.addEventListener('click', e => {
      const b = e.target.closest('[data-domain]'); if (!b) return;
      el.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b));
      onChange(b.dataset.domain);
    });
  };
  // 한 화면 맞춤: box 내용이 넘치면 --s(글자 배율)를 줄이고, 그래도 넘치면 tight(보조 정보 숨김) 적용
  PE.fit = (box, min) => {
    if (!box || !box.offsetParent) return;
    min = min || 0.6;
    const over = () => box.scrollHeight > box.clientHeight + 1;
    box.classList.remove('tight', 'tight2'); let s = 1; box.style.setProperty('--s', 1);
    while (over() && s > min + 0.001) { s -= 0.025; box.style.setProperty('--s', s.toFixed(3)); }
    if (over()) { box.classList.add('tight'); s = Math.min(1, s + 0.15); box.style.setProperty('--s', s.toFixed(3)); while (over() && s > min) { s -= 0.025; box.style.setProperty('--s', s.toFixed(3)); } }
    if (over()) { box.classList.add('tight2'); while (over() && s > 0.5) { s -= 0.025; box.style.setProperty('--s', s.toFixed(3)); } }
    box.dataset.fit = over() ? 'overflow' : 'ok';
  };
  // 스크롤 모드: 글자 축소 없이 원래 크기로, 넘치면 스크롤
  PE.scrollFit = box => { if (!box) return; box.classList.remove('tight','tight2'); box.style.setProperty('--s', 1); box.classList.add('scroll'); box.scrollTop = 0; };
  // 목차: '- '로 시작하면 하위 항목. full=false면 상위 항목만
  const ROM = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
  PE.outlineHtml = (ol, full) => {
    const top = [];
    (ol || []).forEach(x => { if (x.startsWith('- ')) { if (top.length) top[top.length - 1].subs.push(x.slice(2)); } else top.push({ t: x, subs: [] }); });
    if (!top.length) return '';
    return '<ol class="outline">' + top.map((o, i) => `<li><span class="rn">${ROM[i] || i + 1}.</span> ${PE.gl(o.t)}${full && o.subs.length ? `<ul class="ol-subs">${o.subs.map(s => `<li>- ${PE.gl(s)}</li>`).join('')}</ul>` : ''}</li>`).join('') + '</ol>';
  };
  PE.reviewFixed = () => false; // 수정·출처 표기는 화면에 노출하지 않음(CONTENT_RULES.md)
  // 표시용 토픽명: 항상 '한글(English)' 형태(name 필드), 없으면 title
  PE.name = t => (t && (t.name || t.title)) || '';
  // 테마 토글: 시스템 → 다크 → 라이트
  const btn = document.getElementById('themeBtn');
  if (btn) btn.addEventListener('click', () => {
    const root = document.documentElement; const cur = root.getAttribute('data-theme');
    const sysDark = matchMedia('(prefers-color-scheme: dark)').matches;
    const next = cur ? (cur === 'dark' ? 'light' : 'dark') : (sysDark ? 'light' : 'dark');
    root.setAttribute('data-theme', next); localStorage.setItem('pe-theme', next);
  });
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', () => navigator.serviceWorker.register(PE.sw, { scope: PE.base + '/' }).catch(() => {}));
  }
})();
