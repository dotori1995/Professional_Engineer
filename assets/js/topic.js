(function () {
  const PE = window.PE, el = document.getElementById('topic');
  const id = PE.params().get('id');
  PE.load().then(all => {
    const i = all.findIndex(t => t.id === id);
    if (i < 0) { el.innerHTML = '<p class="empty">토픽을 찾을 수 없어요. <a href="' + PE.url('/') + '">목록으로</a></p>'; return; }
    const t = all[i];
    PE.glTopic = t;
    if (t.domain !== PE.cur) PE.setDomain(t.domain);
    const same = all.filter(x => x.domain === t.domain), j = same.indexOf(t), prev = same[j - 1], next = same[j + 1];
    document.title = PE.name(t) + ' · ' + document.title;
    const secs = (t.sections || []).filter(s => (s.subsections || []).some(x => x.items.length));
    const ROM = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'];
    const draw = () => {
      el.innerHTML = `
        <div class="fitbox" id="fb">
          <div class="thead"><span class="badge code">${PE.esc(t.id)}</span>${PE.isImportant(t) ? ' <span class="badge star-badge">중요</span>' : ''}</div>
          <h1>${PE.nameHtml(t)}</h1>
          <div class="lbl">정의</div><div class="def">${PE.gl(t.definition || '-')}</div>
          ${t.dueum ? `<div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
          ${(t.keywords || []).length ? `<div class="lbl">키워드</div><ul class="kw">${t.keywords.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : ''}
          ${(t.outline || []).length ? `<div class="lbl">목차</div>${PE.outlineHtml(t.outline, true)}` : ''}
          ${secs.length ? `<details class="more"><summary>자세히</summary><div class="raw">` + secs.map((s, n) => `<section class="rsec"><h3 class="rsec-t"><span class="rn">${ROM[n] || n + 1}.</span> ${PE.gl(s.title)}</h3>` + s.subsections.filter(x => x.items.length).map(x => `${x.title ? `<div class="rsub">${PE.gl(x.title)}</div>` : ''}<ul class="ritems${x.title ? '' : ' notitle'}">${x.items.map(b => `<li>${PE.gl(b)}</li>`).join('')}</ul>`).join('') + '</section>').join('') + '</div></details>' : ''}
        </div>
        <div class="tfoot">
          ${prev ? `<a class="btn ghost nav" href="${PE.topicUrl(prev.id)}" aria-label="이전 토픽">◀</a>` : '<span class="btn ghost nav" aria-hidden="true"></span>'}
          <a class="btn ghost" href="${PE.url('/cards/')}?topic=${encodeURIComponent(t.id)}">카드</a>
          ${t.curated ? `<a class="btn ghost" href="${PE.url('/quiz/')}?topic=${encodeURIComponent(t.id)}">문제</a>` : ''}
          <span class="pos">${j + 1}/${same.length}</span>
          ${next ? `<a class="btn ghost nav" href="${PE.topicUrl(next.id)}" aria-label="다음 토픽">▶</a>` : '<span class="btn ghost nav" aria-hidden="true"></span>'}
        </div>`;
      const fb = document.getElementById('fb');
      fb.querySelector('details') && fb.querySelector('details').addEventListener('toggle', e => { fb.classList.toggle('scroll', e.target.open); if (!e.target.open) PE.fit(fb); });
      PE.fit(fb);
    };
    draw();
    addEventListener('resize', () => { const fb = document.getElementById('fb'); if (fb && !fb.classList.contains('scroll')) PE.fit(fb); });
  });
})();
