/* 공통: 데이터 로드, 학습 상태(localStorage), 테마, 서비스워커 */
(function () {
  const KEY = 'pe-status-v1';
  const PE = window.PE;
  PE.status = () => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } };
  PE.setStatus = (id, v) => { const s = PE.status(); if (v) s[id] = v; else delete s[id]; localStorage.setItem(KEY, JSON.stringify(s)); };
  PE.load = () => fetch(PE.data).then(r => r.json());
  PE.esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  PE.url = (path) => PE.base + path;
  PE.topicUrl = id => PE.base + '/topic/?id=' + encodeURIComponent(id);
  PE.params = () => new URLSearchParams(location.search);
  PE.domains = list => Array.from(new Set(list.map(t => t.domain)));
  PE.statusBadge = st => st === 'know' ? '<span class="badge know">알아요</span>' : st === 'dont' ? '<span class="badge dont">몰라요</span>' : '';
  PE.domainChips = (el, list, current, onChange) => {
    const ds = PE.domains(list);
    el.innerHTML = ['ALL'].concat(ds).map(d => `<button type="button" class="chip${d === current ? ' on' : ''}" data-domain="${d}">${d === 'ALL' ? '전체 도메인' : d}</button>`).join('');
    el.addEventListener('click', e => {
      const b = e.target.closest('[data-domain]'); if (!b) return;
      el.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b));
      onChange(b.dataset.domain);
    });
  };
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
