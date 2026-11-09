(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const card = $('card'), front = $('front'), back = $('back');
  const params = PE.params();
  let all = [], deck = [], idx = 0, flipped = false;
  let domain = '';
  let shuffle = params.get('shuffle') === '1' || localStorage.getItem('pe-shuffle') === '1';

  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  function build(keepId) {
    const d = all.filter(t => t.domain === domain);
    deck = shuffle ? shuffled(d) : d;
    idx = keepId ? Math.max(0, deck.findIndex(t => t.id === keepId)) : 0;
    $('shuffleBtn').setAttribute('aria-pressed', String(shuffle));
    show();
  }
  function show() {
    flipped = false; back.hidden = true; front.hidden = false;
    const n = deck.length;
    $('bar').style.width = (n ? Math.round((idx + 1) / n * 100) : 0) + '%';
    $('progress').textContent = n ? `${idx + 1} / ${n}` : '0 / 0';
    ['prevBtn', 'nextBtn'].forEach(b => $(b).disabled = !n);
    if (!n) { front.innerHTML = '<div class="empty">카드가 없어요</div>'; return; }
    const t = deck[idx];
    front.innerHTML = `<div class="code">${PE.esc(t.id)}${PE.reviewFixed(t) ? ' <span class="badge fix">검토 수정</span>' : ''}</div>
      <h2>${PE.esc(PE.name(t))}</h2>
      <div class="tap">👆 탭해서 정의·키워드·목차 보기</div>`;
    back.innerHTML = `<div class="code">${PE.esc(t.id)}${PE.reviewFixed(t) ? ' <span class="badge fix">검토 수정</span>' : ''}</div><h3>${PE.esc(PE.name(t))}</h3>
      <div class="label">정의</div><p class="def">${PE.esc(t.definition || '-')}</p>
      ${t.dueum ? `<div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
      ${(t.keywords || []).length ? `<div class="label">키워드</div><ul class="kw">${t.keywords.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : ''}
      ${(t.outline || []).length ? `<div class="label">목차</div>${PE.outlineHtml(t.outline, false)}` : ''}
      <a class="more" href="${PE.topicUrl(t.id)}" onclick="event.stopPropagation()">자세히 보기 →</a>`;
    PE.fit(front);
  }
  function flip() { if (!deck.length) return; flipped = !flipped; front.hidden = flipped; back.hidden = !flipped; PE.fit(flipped ? back : front); }
  PE.flip = flip;
  function go(d) {
    if (!deck.length) return;
    let n = idx + d;
    if (n < 0) n = deck.length - 1;
    if (n >= deck.length) { n = 0; if (shuffle) deck = shuffled(deck); }
    idx = n;
    card.classList.add(d > 0 ? 'swipe-l' : 'swipe-r'); setTimeout(() => card.classList.remove('swipe-l', 'swipe-r'), 160);
    show();
  }
  card.addEventListener('click', flip);
  card.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(); } });
  document.addEventListener('keydown', e => { if (e.key === 'ArrowRight') go(1); if (e.key === 'ArrowLeft') go(-1); });
  $('prevBtn').addEventListener('click', () => go(-1));
  $('nextBtn').addEventListener('click', () => go(1));
  $('flipBtn').addEventListener('click', flip);
  $('shuffleBtn').addEventListener('click', () => { shuffle = !shuffle; localStorage.setItem('pe-shuffle', shuffle ? '1' : '0'); build(deck[idx] && deck[idx].id); });
  // 스와이프
  let sx = 0, sy = 0, moved = false;
  card.addEventListener('touchstart', e => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; moved = false; }, { passive: true });
  card.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) { moved = true; e.preventDefault(); go(dx < 0 ? 1 : -1); }
  });
  card.addEventListener('click', e => { if (moved) { e.stopImmediatePropagation(); moved = false; } }, true);
  addEventListener('resize', () => PE.fit(flipped ? back : front));
  PE.load().then(data => {
    all = data;
    const tid = params.get('topic') || params.get('id'), tt = all.find(t => t.id === tid);
    if (tt && tt.domain !== PE.cur) PE.setDomain(tt.domain);
    domain = PE.cur;
    build(tid);
  }).catch(() => { $('progress').textContent = '데이터를 불러오지 못했어요.'; });
})();
