(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const card = $('card'), front = $('front'), back = $('back');
  const params = PE.params();
  let all = [], deck = [], idx = 0, flipped = false;
  let mode = params.get('mode') || localStorage.getItem('pe-card-mode') || 'all';
  let domain = sessionStorage.getItem('pe-domain') || 'ALL';
  let shuffle = localStorage.getItem('pe-shuffle') === '1';

  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  function build(keepId) {
    const st = PE.status();
    let d = all.filter(t => domain === 'ALL' || t.domain === domain);
    if (mode === 'dont') d = d.filter(t => st[t.id] === 'dont');
    if (mode === 'new') d = d.filter(t => !st[t.id]);
    deck = shuffle ? shuffled(d) : d;
    idx = keepId ? Math.max(0, deck.findIndex(t => t.id === keepId)) : 0;
    document.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('on', b.dataset.mode === mode));
    $('shuffleBtn').setAttribute('aria-pressed', String(shuffle));
    show();
  }
  function stats() {
    const st = PE.status(); const scope = all.filter(t => domain === 'ALL' || t.domain === domain);
    const know = scope.filter(t => st[t.id] === 'know').length, dont = scope.filter(t => st[t.id] === 'dont').length;
    return { total: scope.length, know, dont };
  }
  function show() {
    flipped = false; back.hidden = true; front.hidden = false;
    const s = stats();
    $('bar').style.width = (s.total ? Math.round(s.know / s.total * 100) : 0) + '%';
    if (!deck.length) {
      front.innerHTML = `<div class="empty">${mode === 'dont' ? '몰라요로 표시한 카드가 없어요 👏' : '카드가 없어요'}</div>`;
      $('progress').textContent = `0장 · 알아요 ${s.know} / 몰라요 ${s.dont} / 전체 ${s.total}`;
      ['prevBtn', 'nextBtn', 'knowBtn', 'dontBtn'].forEach(b => $(b).disabled = true);
      return;
    }
    ['prevBtn', 'nextBtn', 'knowBtn', 'dontBtn'].forEach(b => $(b).disabled = false);
    $('prevBtn').disabled = idx === 0;
    const t = deck[idx], cur = PE.status()[t.id];
    $('progress').textContent = `${idx + 1} / ${deck.length}장 · 알아요 ${s.know} · 몰라요 ${s.dont} · 전체 ${s.total}`;
    front.innerHTML = `<div class="code">${PE.esc(t.id)} ${PE.statusBadge(cur)}</div>
      <h2>${PE.esc(t.title)}</h2>${t.subtitle ? `<div class="sub">${PE.esc(t.subtitle)}</div>` : ''}
      <div class="tap">👆 탭해서 정의·키워드 보기</div>`;
    back.innerHTML = `<h3>${PE.esc(t.title)}</h3>
      <div class="label">정의</div><p class="def">${PE.esc(t.definition || '-')}</p>
      ${(t.keywords || []).length ? `<div class="label">핵심 키워드</div><ul class="kw">${t.keywords.map(k => `<li>${PE.esc(k)}</li>`).join('')}</ul>` : ''}
      ${t.dueum ? `<div class="dueum-box">💡 두음: ${PE.esc(t.dueum)}</div>` : ''}
      <a class="more" href="${PE.topicUrl(t.id)}" onclick="event.stopPropagation()">자세히 보기 →</a>`;
  }
  function flip() { if (!deck.length) return; flipped = !flipped; front.hidden = flipped; back.hidden = !flipped; }
  function go(d) {
    if (!deck.length) return;
    const n = idx + d; if (n < 0) return;
    if (n >= deck.length) { idx = 0; if (shuffle) deck = shuffled(deck); } else idx = n;
    card.classList.add(d > 0 ? 'swipe-l' : 'swipe-r'); setTimeout(() => card.classList.remove('swipe-l', 'swipe-r'), 160);
    show();
  }
  function mark(v) {
    if (!deck.length) return; const t = deck[idx];
    PE.setStatus(t.id, v);
    if (mode !== 'all') { // 범위에서 빠지는 카드는 덱에서 제거
      const st = PE.status();
      if ((mode === 'dont' && st[t.id] !== 'dont') || (mode === 'new' && st[t.id])) { deck.splice(idx, 1); if (idx >= deck.length) idx = 0; show(); return; }
    }
    go(1);
  }
  card.addEventListener('click', flip);
  card.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(); } });
  document.addEventListener('keydown', e => { if (e.key === 'ArrowRight') go(1); if (e.key === 'ArrowLeft') go(-1); });
  $('prevBtn').addEventListener('click', () => go(-1));
  $('nextBtn').addEventListener('click', () => go(1));
  $('knowBtn').addEventListener('click', () => mark('know'));
  $('dontBtn').addEventListener('click', () => mark('dont'));
  $('shuffleBtn').addEventListener('click', () => { shuffle = !shuffle; localStorage.setItem('pe-shuffle', shuffle ? '1' : '0'); build(deck[idx] && deck[idx].id); });
  document.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.mode; localStorage.setItem('pe-card-mode', mode); build(); }));
  $('resetBtn').addEventListener('click', () => {
    if (!confirm('현재 도메인 범위의 알아요/몰라요 기록을 지울까요?')) return;
    all.filter(t => domain === 'ALL' || t.domain === domain).forEach(t => PE.setStatus(t.id, null)); build();
  });
  // 스와이프
  let sx = 0, sy = 0, moved = false;
  card.addEventListener('touchstart', e => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; moved = false; }, { passive: true });
  card.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) { moved = true; e.preventDefault(); go(dx < 0 ? 1 : -1); }
  });
  card.addEventListener('click', e => { if (moved) { e.stopImmediatePropagation(); moved = false; } }, true);
  PE.load().then(data => {
    all = data;
    if (domain !== 'ALL' && !PE.domains(all).includes(domain)) domain = 'ALL';
    PE.domainChips($('domainChips'), all, domain, d => { domain = d; sessionStorage.setItem('pe-domain', d); build(); });
    build();
  }).catch(() => { $('progress').textContent = '데이터를 불러오지 못했어요.'; });
})();
