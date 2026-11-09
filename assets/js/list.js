(function () {
  const PE = window.PE;
  const $q = document.getElementById('q'), $list = document.getElementById('list'), $count = document.getElementById('count');
  const $imp = document.getElementById('impOnly');
  let all = [];
  let impOnly = false;
  try { impOnly = localStorage.getItem('pe-imp-only') === '1'; } catch (e) {}
  const norm = s => String(s || '').toLowerCase().replace(/\s+/g, '');
  const hl = (text, q) => {
    const t = PE.esc(text); if (!q) return t;
    const i = norm(text).indexOf(q);
    if (i < 0) return t;
    let n = 0, start = -1, end = -1; const raw = String(text);
    for (let k = 0; k < raw.length; k++) { if (/\s/.test(raw[k])) continue; if (n === i) start = k; n++; if (n === i + q.length) { end = k + 1; break; } }
    if (start < 0 || end < 0) return t;
    return PE.esc(raw.slice(0, start)) + '<mark>' + PE.esc(raw.slice(start, end)) + '</mark>' + PE.esc(raw.slice(end));
  };
  function syncImpBtn() {
    if (!$imp) return;
    $imp.setAttribute('aria-pressed', String(impOnly));
    $imp.classList.toggle('on', impOnly);
  }
  function render() {
    const q = norm($q.value);
    const rows = all.filter(t => {
      if (!PE.inCur(t)) return false;
      if (impOnly && !PE.isImportant(t)) return false;
      if (!q) return true;
      return norm([t.id, t.title, t.name, t.en, t.subtitle, (t.keywords || []).join(' '), t.definition, t.dueum].join(' ')).includes(q);
    });
    $count.textContent = `${rows.length}개 토픽` + (impOnly ? ' · 중요만' : '') + (q ? ` · "${$q.value.trim()}" 검색` : '');
    if (!rows.length) { $list.innerHTML = '<li class="empty">검색 결과가 없어요.</li>'; return; }
    $list.innerHTML = rows.map(t => {
      const kwHit = q && (t.keywords || []).find(k => norm(k).includes(q));
      const desc = kwHit && !norm(t.definition).includes(q) ? '🔑 ' + hl(kwHit, q) : hl(t.definition || (t.keywords || []).join(', '), q);
      return `<li class="item"><a href="${PE.topicUrl(t.id)}">
        <div class="top"><span class="badge code">${PE.esc(t.id)}</span>${PE.isImportant(t) ? '<span class="badge star-badge">중요</span>' : ''}${t.dueum ? '<span class="badge dueum">두음</span>' : ''}${PE.reviewFixed(t) ? '<span class="badge fix">검토 수정</span>' : ''}</div>
        <h3>${PE.starHtml(t)}${hl(PE.name(t), q)}</h3><p>${desc}</p></a></li>`;
    }).join('');
  }
  PE.load().then(data => {
    all = data;
    const q0 = PE.params().get('q'); if (q0) $q.value = q0;
    syncImpBtn();
    render();
  }).catch(() => { $count.textContent = '데이터를 불러오지 못했어요.'; });
  let timer; $q.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 120); });
  $imp && $imp.addEventListener('click', () => {
    impOnly = !impOnly;
    try { localStorage.setItem('pe-imp-only', impOnly ? '1' : '0'); } catch (e) {}
    syncImpBtn(); render();
  });
})();
