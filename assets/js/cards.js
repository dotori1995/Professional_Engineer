(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const card = $('card'), front = $('front'), back = $('back');
  const params = PE.params();
  let all = [], deck = [], idx = 0, flipped = false;
  let domain = sessionStorage.getItem('pe-domain') || 'ALL';
  let shuffle = params.get('shuffle') === '1' || localStorage.getItem('pe-shuffle') === '1';

  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  function build(keepId) {
    const d = all.filter(t => domain === 'ALL' || t.domain === domain);
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
      <h2>${PE.esc(t.title)}</h2>${t.subtitle && t.subtitle.replace(/\s/g, '') !== t.title.replace(/\s/g, '') ? `<div class="sub">${PE.esc(t.subtitle)}</div>` : ''}
      <div class="tap">👆 탭해서 정의·키워드·목차 보기</div>`;
    back.innerHTML = `<div class="code">${PE.esc(t.id)}${PE.reviewFixed(t) ? ' <span class="badge fix">검토 수정</span>' : ''}</div><h3>${PE.esc(t.title)}</h3>
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
  addEventListener('resize', () => PE.fit(view === 'quiz' ? quiz : (flipped ? back : front)));
  // ===== 객관식 =====
  const quiz = $('quiz');
  let view = localStorage.getItem('pe-card-view') === 'quiz' ? 'quiz' : 'flash';
  let score = { ok: 0, n: 0 }, q = null;
  const pick = (arr, k) => shuffled(arr).slice(0, k);
  const kwSet = t => (t.keywords || []).slice(0, 3).join(' · ');
  const norm = s => String(s || '').replace(/\s|\(.*?\)/g, '').toLowerCase();
  function makeQuestion() {
    const pool = all.filter(t => domain === 'ALL' || t.domain === domain);
    const types = [];
    const defPool = pool.filter(t => (t.definition || '').length > 15);
    const kwPool = pool.filter(t => (t.keywords || []).length >= 2);
    if (defPool.length >= 4) types.push('def');
    if (kwPool.length >= 4) types.push('kw');
    if (!types.length) return null;
    const type = types[Math.floor(Math.random() * types.length)];
    const src = type === 'def' ? defPool : kwPool;
    const ans = src[Math.floor(Math.random() * src.length)];
    const label = type === 'def' ? (t => t.title) : kwSet;
    const used = new Set([norm(ans.title), norm(label(ans))]);
    const others = shuffled(src.filter(t => t.id !== ans.id)).filter(t => {
      const k1 = norm(t.title), k2 = norm(label(t));
      if (used.has(k1) || used.has(k2)) return false; used.add(k1); used.add(k2); return true;
    }).slice(0, 3);
    const opts = shuffled([ans].concat(others));
    return { type, ans, opts, label, answered: -1 };
  }
  // 정의 문제에서 정답 토픽명이 그대로 보이지 않게 가림
  function mask(t) {
    const terms = new Set();
    [t.title, t.subtitle].filter(Boolean).forEach(x => {
      terms.add(x.trim());
      x.split(/[()\[\]_,/·:]+/).map(y => y.trim()).filter(y => y.length >= 2).forEach(y => terms.add(y));
    });
    let html = PE.esc(t.definition || '');
    [...terms].sort((a, b) => b.length - a.length).forEach(w => {
      const e = PE.esc(w).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      html = html.replace(new RegExp(e, 'gi'), '<span class="mask">○○</span>');
    });
    return html;
  }
  function renderQuiz() {
    if (!q) { quiz.innerHTML = '<div class="empty">문제를 만들 데이터가 부족해요</div>'; return; }
    const head = q.type === 'def'
      ? `<div class="qtype">정의 → 토픽</div><div class="qtext">${mask(q.ans)}</div><div class="qask">이 정의에 해당하는 토픽은?</div>`
      : `<div class="qtype">토픽 → 키워드</div><div class="qtitle">${PE.esc(q.ans.title)}</div><div class="qask">이 토픽의 키워드는?</div>`;
    const done = q.answered >= 0;
    quiz.innerHTML = `<div class="qscore">점수 ${score.ok} / ${score.n}</div>${head}
      <div class="qopts">${q.opts.map((t, i) => {
        let cls = 'qopt'; if (done) { if (t.id === q.ans.id) cls += ' right'; else if (i === q.answered) cls += ' wrong'; }
        return `<button type="button" class="${cls}" data-i="${i}" ${done ? 'disabled' : ''}><span class="qn">${'ABCD'[i]}</span><span>${q.type === 'def' ? PE.esc(t.title) : PE.gl(q.label(t))}</span></button>`;
      }).join('')}</div>
      ${done ? `<div class="qfb ${q.opts[q.answered].id === q.ans.id ? 'ok' : 'ng'}">${q.opts[q.answered].id === q.ans.id ? '⭕ 정답!' : '❌ 오답'} <b>${PE.esc(q.ans.title)}</b>
        <div class="qdef">${PE.esc(q.ans.definition || '')}</div>
        <a href="${PE.topicUrl(q.ans.id)}">자세히 →</a></div>` : ''}`;
    quiz.querySelectorAll('.qopt').forEach(b => b.addEventListener('click', () => {
      if (q.answered >= 0) return; q.answered = +b.dataset.i; score.n++; if (q.opts[q.answered].id === q.ans.id) score.ok++;
      $('quizNext').disabled = false; renderQuiz();
    }));
    $('quizNext').disabled = !done;
    PE.fit(quiz);
  }
  function nextQuestion() { q = makeQuestion(); renderQuiz(); }
  function setView(v) {
    view = v; localStorage.setItem('pe-card-view', v);
    document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === v));
    const qz = v === 'quiz';
    card.hidden = qz; quiz.hidden = !qz; $('flashActions').hidden = qz; $('quizActions').hidden = !qz;
    $('shuffleBtn').hidden = qz; document.querySelector('.progress').style.display = qz ? 'none' : '';
    $('progress').parentElement.style.display = qz ? 'none' : '';
    if (qz) { if (!q) nextQuestion(); else renderQuiz(); } else show();
  }
  document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  $('quizNext').addEventListener('click', nextQuestion);
  $('quizReset').addEventListener('click', () => { score = { ok: 0, n: 0 }; nextQuestion(); });
  PE.quizNext = nextQuestion;
  PE.load().then(data => {
    all = data;
    if (domain !== 'ALL' && !PE.domains(all).includes(domain)) domain = 'ALL';
    PE.domainChips($('domainChips'), all, domain, d => { domain = d; sessionStorage.setItem('pe-domain', d); build(); if (view === 'quiz') nextQuestion(); });
    build(params.get('id'));
    setView(params.get('view') || view);
  }).catch(() => { $('progress').textContent = '데이터를 불러오지 못했어요.'; });
})();
