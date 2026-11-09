(function () {
  const PE = window.PE, el = document.getElementById('topic');
  const id = PE.params().get('id');
  const LBL = { A: '오류 수정', B: '최신화', C: '참고', D: '텍스트 정리' };
  PE.load().then(all => {
    const i = all.findIndex(t => t.id === id);
    if (i < 0) { el.innerHTML = '<p class="empty">토픽을 찾을 수 없어요. <a href="' + PE.url('/') + '">목록으로</a></p>'; return; }
    const t = all[i], prev = all[i - 1], next = all[i + 1];
    document.title = t.title + ' · ' + document.title;
    const rv = t.review || [];
    const notes = [t.keywords_note, t.note].filter(Boolean);
    const secs = (t.sections || []).filter(s => (s.subsections || []).some(x => x.items.length));
    const hasRaw = secs.length > 0;
    const sub = t.subtitle && t.subtitle.replace(/\s/g, '') !== t.title.replace(/\s/g, '') ? t.subtitle : '';
    const draw = () => {
      el.innerHTML = `
        <div class="fitbox" id="fb">
          <div class="thead"><span class="badge code">${PE.esc(t.id)}</span>${PE.reviewFixed(t) ? '<span class="badge fix">검토 수정</span>' : ''}</div>
          <h1>${PE.esc(t.title)}</h1>${sub ? `<div class="sub">${PE.esc(sub)}</div>` : ''}
          <div class="lbl">정의</div><div class="def">${PE.esc(t.definition || '(원문에서 정의 텍스트를 찾지 못함)')}</div>
          ${t.dueum ? `<div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
          ${(t.keywords || []).length ? `<div class="lbl">키워드</div><ul class="kw">${t.keywords.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : ''}
          ${(t.outline || []).length ? `<div class="lbl">목차</div>${PE.outlineHtml(t.outline, true)}` : ''}
          ${rv.length || notes.length || hasRaw ? `<details class="more"><summary>자세히</summary>
            ${notes.map(n => `<div class="note">📝 ${PE.esc(n)}</div>`).join('')}
            ${rv.length ? `<ul class="review">${rv.map(r => { const m = r.match(/^\[([ABCD])\]\s*/); return `<li>${m ? `<span class="rv rv-${m[1]}">${LBL[m[1]]}</span> ` : ''}${PE.esc(m ? r.slice(m[0].length) : r)}</li>`; }).join('')}</ul>` : ''}
            ${hasRaw ? `<div class="raw"><div class="raw-h">원문 발췌 (자동 추출·미검수, 원문 ${t.pages ? t.pages[0] + '–' + t.pages[1] + '쪽' : ''})</div>` + secs.map((s, n) => `<section class="rsec"><h3 class="rsec-t"><span class="rn">${['I','II','III','IV','V','VI'][n] || n + 1}.</span> ${PE.gl(s.title)}</h3>` + s.subsections.filter(x => x.items.length).map(x => `${x.title ? `<div class="rsub">${PE.gl(x.title)}</div>` : ''}<ul class="ritems${x.title ? '' : ' notitle'}">${x.items.map(b => `<li>${PE.esc(b)}</li>`).join('')}</ul>`).join('') + '</section>').join('') + '</div>' : ''}
          </details>` : ''}
        </div>
        <div class="tfoot">
          ${prev ? `<a class="btn ghost nav" href="${PE.topicUrl(prev.id)}" aria-label="이전 토픽">◀</a>` : '<span class="btn ghost nav" aria-hidden="true"></span>'}
          <a class="btn ghost" href="${PE.url('/cards/')}?id=${encodeURIComponent(t.id)}">🃏 카드로 보기</a>
          <span class="pos">${i + 1} / ${all.length}</span>
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
