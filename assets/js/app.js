/* 공통: 데이터 로드, 테마, 한 화면 맞춤, 서비스워커 */
(function () {
  const PE = window.PE;
  try { localStorage.removeItem('pe-status-v1'); localStorage.removeItem('pe-card-mode'); } catch (e) {}
  // 약어 사전(_data/glossary.yml → glossary.json)
  let GL = {}, GLRE = null;
  PE.loadGlossary = () => fetch(PE.base + '/glossary.json').then(r => r.json()).then(g => {
    GL = g || {}; const keys = Object.keys(GL).sort((a, b) => b.length - a.length).map(k => k.replace(/[.*+?^${}()|[\]\\\/-]/g, '\\$&'));
    GLRE = keys.length ? new RegExp('(?<![A-Za-z0-9])(' + keys.join('|') + ')(?![A-Za-z0-9])', 'g') : null;
  }).catch(() => {});
  PE.load = () => Promise.all([fetch(PE.data).then(r => r.json()), PE.loadGlossary()]).then(([d]) => d);
  // 텍스트를 escape하고, 약어 뒤에 정식 명칭을 작게 붙임(이미 괄호로 풀어 쓴 경우·같은 약어 반복은 생략)
  PE.gl = text => {
    const raw = String(text == null ? '' : text);
    if (!GLRE) return PE.esc(raw);
    const seen = new Set(); let out = '', last = 0;
    raw.replace(GLRE, (m, k, off) => {
      const after = raw.slice(off + m.length).trimStart();
      const full = GL[k];
      out += PE.esc(raw.slice(last, off + m.length)); last = off + m.length;
      if (!seen.has(k) && !after.startsWith('(') && !raw.toLowerCase().includes(String(full).toLowerCase())) { out += `<small class="gl">(${PE.esc(full)})</small>`; seen.add(k); }
      return m;
    });
    return out + PE.esc(raw.slice(last));
  };
  PE.esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  PE.url = (path) => PE.base + path;
  PE.topicUrl = id => PE.base + '/topic/?id=' + encodeURIComponent(id);
  PE.params = () => new URLSearchParams(location.search);
  PE.domains = list => Array.from(new Set(list.map(t => t.domain)));
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
  // 목차: '- '로 시작하면 하위 항목. full=false면 상위 항목만
  const ROM = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
  PE.outlineHtml = (ol, full) => {
    const top = [];
    (ol || []).forEach(x => { if (x.startsWith('- ')) { if (top.length) top[top.length - 1].subs.push(x.slice(2)); } else top.push({ t: x, subs: [] }); });
    if (!top.length) return '';
    return '<ol class="outline">' + top.map((o, i) => `<li><span class="rn">${ROM[i] || i + 1}.</span> ${PE.gl(o.t)}${full && o.subs.length ? `<span class="subs">${o.subs.map(PE.gl).join(' · ')}</span>` : ''}</li>`).join('') + '</ol>';
  };
  PE.reviewFixed = t => (t.review || []).some(r => /^\[[ABD]\]/.test(r));
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
