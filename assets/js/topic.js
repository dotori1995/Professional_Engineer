(function () {
  const PE = window.PE, el = document.getElementById('topic');
  const id = PE.params().get('id');
  PE.load().then(all => {
    const i = all.findIndex(t => t.id === id);
    if (i < 0) { el.innerHTML = '<p class="empty">토픽을 찾을 수 없어요. <a href="' + PE.url('/') + '">목록으로</a></p>'; return; }
    const t = all[i], prev = all[i - 1], next = all[i + 1];
    document.title = t.title + ' · ' + document.title;
    const draw = () => {
      const st = PE.status()[t.id];
      el.innerHTML = `
        <div class="top meta"><span class="badge code">${PE.esc(t.id)}</span> ${PE.esc(t.category || t.domain)} ${PE.statusBadge(st)}</div>
        <h1>${PE.esc(t.title)}</h1>
        ${t.subtitle ? `<p class="sub">${PE.esc(t.subtitle)}</p>` : ''}
        <h2>정의</h2><div class="def">${PE.esc(t.definition || '(원문에서 정의 텍스트를 찾지 못함)')}</div>
        ${t.dueum ? `<h2>두음(원문)</h2><div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
        <h2>핵심 키워드</h2>${(t.keywords || []).length ? `<ul class="kw">${t.keywords.map(k => `<li>${PE.esc(k)}</li>`).join('')}</ul>` : '<p class="meta">원문 키워드 없음</p>'}
        ${t.keywords_note ? `<div class="note">ℹ️ ${PE.esc(t.keywords_note)}</div>` : ''}
        ${t.note ? `<div class="note">📝 ${PE.esc(t.note)}</div>` : ''}
        ${(t.sections || []).length ? `<h2>특징·구성·비교 (원문 발췌)</h2>` + t.sections.map((s, k) => `
          <details ${k === 0 ? 'open' : ''}><summary>${PE.esc(s.title)}</summary>
          <ul>${s.bullets.map(b => b.startsWith('▸ ') ? `<li class="subh">${PE.esc(b)}</li>` : `<li>${PE.esc(b)}</li>`).join('')}</ul></details>`).join('') : ''}
        <p class="meta">원문 ${t.pages ? t.pages[0] + '–' + t.pages[1] + '쪽' : ''}</p>
        <div class="card-actions">
          <button type="button" class="btn dont" data-set="dont">🤔 몰라요</button>
          <button type="button" class="btn know" data-set="know">✅ 알아요</button>
        </div>
        <div class="pager">
          ${prev ? `<a href="${PE.topicUrl(prev.id)}">◀ ${PE.esc(prev.id)}</a>` : '<span style="flex:1"></span>'}
          ${next ? `<a href="${PE.topicUrl(next.id)}">${PE.esc(next.id)} ▶</a>` : '<span style="flex:1"></span>'}
        </div>`;
      el.querySelectorAll('[data-set]').forEach(b => b.addEventListener('click', () => {
        const cur = PE.status()[t.id]; PE.setStatus(t.id, cur === b.dataset.set ? null : b.dataset.set); draw();
      }));
    };
    draw();
  });
})();
