(function () {
  const PE = window.PE;
  const $q = document.getElementById('q'), $list = document.getElementById('list'), $count = document.getElementById('count');
  let all = [], domain = sessionStorage.getItem('pe-domain') || 'ALL';
  const norm = s => String(s || '').toLowerCase().replace(/\s+/g, '');
  const hl = (text, q) => {
    const t = PE.esc(text); if (!q) return t;
    const i = norm(text).indexOf(q);
    if (i < 0) return t;
    // 공백 무시 매칭 위치를 원문 인덱스로 환산
    let n = 0, start = -1, end = -1; const raw = String(text);
    for (let k = 0; k < raw.length; k++) { if (/\s/.test(raw[k])) continue; if (n === i) start = k; n++; if (n === i + q.length) { end = k + 1; break; } }
    if (start < 0 || end < 0) return t;
    return PE.esc(raw.slice(0, start)) + '<mark>' + PE.esc(raw.slice(start, end)) + '</mark>' + PE.esc(raw.slice(end));
  };
  function render() {
    const q = norm($q.value);
    const rows = all.filter(t => {
      if (domain !== 'ALL' && t.domain !== domain) return false;
      if (!q) return true;
      return norm([t.id, t.title, t.subtitle, (t.keywords || []).join(' '), t.definition, t.dueum].join(' ')).includes(q);
    });
    $count.textContent = `${rows.length}개 토픽` + (q ? ` · "${$q.value.trim()}" 검색` : '');
    if (!rows.length) { $list.innerHTML = '<li class="empty">검색 결과가 없어요.</li>'; return; }
    $list.innerHTML = rows.map(t => {
      const kwHit = q && (t.keywords || []).find(k => norm(k).includes(q));
      const desc = kwHit && !norm(t.definition).includes(q) ? '🔑 ' + hl(kwHit, q) : hl(t.definition || (t.keywords || []).join(', '), q);
      return `<li class="item"><a href="${PE.topicUrl(t.id)}">
        <div class="top"><span class="badge code">${PE.esc(t.id)}</span>${t.dueum ? '<span class="badge dueum">두음</span>' : ''}${PE.reviewFixed(t) ? '<span class="badge fix">검토 수정</span>' : ''}</div>
        <h3>${hl(t.title, q)}</h3><p>${desc}</p></a></li>`;
    }).join('');
  }
  PE.load().then(data => {
    all = data;
    if (domain !== 'ALL' && !PE.domains(all).includes(domain)) domain = 'ALL';
    PE.domainChips(document.getElementById('domainChips'), all, domain, d => { domain = d; sessionStorage.setItem('pe-domain', d); render(); });
    const q0 = PE.params().get('q'); if (q0) $q.value = q0;
    render();
  }).catch(() => { $count.textContent = '데이터를 불러오지 못했어요.'; });
  let timer; $q.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 120); });
})();
