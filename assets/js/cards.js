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
  addEventListener('resize', () => PE.fit(view === 'quiz' ? quiz : (flipped ? back : front)));
  // ===== 객관식 =====
  // 문제 유형: bank(검수한 문제은행 _data/quiz) · kwOf(토픽의 키워드 찾기) · notKwOf(키워드가 아닌 것) · def(정의→토픽) · kw(토픽→키워드)
  const quiz = $('quiz');
  let view = localStorage.getItem('pe-card-view') === 'quiz' ? 'quiz' : 'flash';
  let score = { ok: 0, n: 0 }, q = null, bank = [], bankQueue = [], topicOnly = params.get('topic') || '', topicSeq = 0;
  const pick = (arr, k) => shuffled(arr).slice(0, k);
  const kwSet = t => (t.keywords || []).slice(0, 3).join(' · ');
  const norm = s => String(s || '').replace(/\s|\(.*?\)/g, '').toLowerCase();
  const byId = id => all.find(t => t.id === id);
  const inDomain = t => domain === 'ALL' || t.domain === domain;
  const topicText = t => norm([t.title, t.name, t.definition, (t.keywords || []).join(' '), JSON.stringify(t.sections || [])].join(' '));
  // 다른 토픽 키워드가 이 토픽에도 해당될 수 있으면 오답 보기로 쓰지 않음(quiz_avoid 양방향 + 본문 포함 여부 검사)
  function foreignTerms(t) {
    const txt = topicText(t), own = new Set((t.quiz_terms || []).map(norm));
    const out = [];
    all.filter(o => o.id !== t.id && (o.quiz_terms || []).length && inDomain(o)
      && !(t.quiz_avoid || []).includes(o.id) && !(o.quiz_avoid || []).includes(t.id))
      .forEach(o => o.quiz_terms.forEach(x => { const k = norm(x); if (k && !own.has(k) && !txt.includes(k)) out.push({ term: x, from: o }); }));
    return out;
  }
  const mk = (type, t, label, stem, ask, opts, answer, extra) => {
    const order = shuffled([0, 1, 2, 3]);
    return Object.assign({ type, t, label, stem, ask, opts: order.map(i => opts[i]), answer: order.indexOf(answer), answered: -1 }, extra || {});
  };
  function qBank(b) {
    const t = byId(b.topic);
    return mk('bank', t, `${PE.name(t)} · 키워드 문제`, `<div class="qtext">${PE.gl(b.question)}</div>`, '', b.options.map(PE.gl), b.answer, { explain: b.explain });
  }
  function qKwOf(t, neg) {
    const own = shuffled(t.quiz_terms || []), foreign = shuffled(foreignTerms(t));
    if (neg ? own.length < 3 || foreign.length < 1 : own.length < 1 || foreign.length < 3) return null;
    const opts = neg ? own.slice(0, 3).concat([foreign[0].term]) : [own[0]].concat(foreign.slice(0, 3).map(f => f.term));
    const extra = neg ? { raw: true, explain: `${foreign[0].term} → ${PE.name(foreign[0].from)}의 키워드예요.` } : { raw: true, explain: '나머지는 ' + foreign.slice(0, 3).map(f => `${f.term} → ${PE.name(f.from)}`).join(', ') };
    return mk(neg ? 'notKwOf' : 'kwOf', t, neg ? '토픽의 키워드 아닌 것 찾기' : '토픽의 키워드 찾기',
      `<div class="qtitle">${PE.esc(PE.name(t))}</div>`, neg ? '이 토픽의 키워드가 <b>아닌</b> 것은?' : '이 토픽의 키워드는?', opts.map(PE.gl), neg ? 3 : 0, extra);
  }
  function qAuto(type) {
    const pool = all.filter(inDomain);
    const src = type === 'def' ? pool.filter(t => (t.definition || '').length > 15) : pool.filter(t => (t.keywords || []).length >= 2);
    if (src.length < 4) return null;
    const ans = src[Math.floor(Math.random() * src.length)];
    const label = type === 'def' ? PE.name : kwSet;
    const used = new Set([norm(ans.title), norm(label(ans))]);
    const others = shuffled(src.filter(t => t.id !== ans.id)).filter(t => {
      const k1 = norm(t.title), k2 = norm(label(t));
      if (used.has(k1) || used.has(k2)) return false; used.add(k1); used.add(k2); return true;
    }).slice(0, 3);
    const opts = [ans].concat(others).map(t => type === 'def' ? PE.esc(PE.name(t)) : PE.gl(kwSet(t)));
    return type === 'def'
      ? mk('def', ans, '정의 → 토픽', `<div class="qtext">${mask(ans)}</div>`, '이 정의에 해당하는 토픽은?', opts, 0)
      : mk('kw', ans, '토픽 → 키워드', `<div class="qtitle">${PE.esc(PE.name(ans))}</div>`, '이 토픽의 키워드는?', opts, 0);
  }
  function nextBank(filter) {
    if (!bankQueue.length) bankQueue = shuffled(bank.filter(filter));
    return bankQueue.length ? qBank(bankQueue.shift()) : null;
  }
  function makeQuestion() {
    if (topicOnly) {
      const t = byId(topicOnly); if (!t) { topicOnly = ''; return makeQuestion(); }
      topicSeq++;
      // 문제은행 문제 3개마다 키워드 찾기/아닌 것 찾기 1개
      if (topicSeq % 4 === 0) { const r = qKwOf(t, topicSeq % 8 === 0); if (r) return r; }
      return nextBank(b => b.topic === topicOnly) || qKwOf(t, false) || qAuto('def');
    }
    const curated = all.filter(t => inDomain(t) && (t.quiz_terms || []).length);
    const r = Math.random();
    let out = null;
    if (r < 0.5) out = nextBank(b => { const t = byId(b.topic); return t && inDomain(t); });
    else if (r < 0.65 && curated.length) out = qKwOf(curated[Math.floor(Math.random() * curated.length)], false);
    else if (r < 0.75 && curated.length) out = qKwOf(curated[Math.floor(Math.random() * curated.length)], true);
    else if (r < 0.9) out = qAuto('def');
    else out = qAuto('kw');
    return out || qAuto('def') || qAuto('kw');
  }
  // 정의 문제에서 정답 토픽명이 그대로 보이지 않게 가림
  function mask(t) {
    const terms = new Set();
    [t.title, t.subtitle, t.name, t.en].filter(Boolean).forEach(x => {
      terms.add(x.trim());
      x.split(/[()\[\]_,/·:&]+/).map(y => y.trim()).filter(y => y.length >= 2).forEach(y => terms.add(y));
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
    const done = q.answered >= 0, ok = done && q.answered === q.answer;
    const tag = topicOnly ? ` · ${PE.esc(PE.name(byId(topicOnly)))} 집중` : '';
    quiz.innerHTML = `<div class="qscore">점수 ${score.ok} / ${score.n}${tag}</div>
      <div class="qtype">${PE.esc(q.label)}</div>${q.stem}${q.ask ? `<div class="qask">${q.ask}</div>` : ''}
      <div class="qopts">${q.opts.map((o, i) => {
        let cls = 'qopt'; if (done) { if (i === q.answer) cls += ' right'; else if (i === q.answered) cls += ' wrong'; }
        return `<button type="button" class="${cls}" data-i="${i}" ${done ? 'disabled' : ''}><span class="qn">${'ABCD'[i]}</span><span>${o}</span></button>`;
      }).join('')}</div>
      ${done ? `<div class="qfb ${ok ? 'ok' : 'ng'}">${ok ? '⭕ 정답!' : '❌ 오답'} <b>${PE.esc(PE.name(q.t))}</b>
        <div class="qdef">${q.raw ? PE.esc(q.explain) : PE.gl(q.explain || q.t.definition || '')}</div>
        <a href="${PE.topicUrl(q.t.id)}">자세히 →</a></div>` : ''}`;
    quiz.querySelectorAll('.qopt').forEach(b => b.addEventListener('click', () => {
      if (q.answered >= 0) return; q.answered = +b.dataset.i; score.n++; if (q.answered === q.answer) score.ok++;
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
  PE.quizState = () => q && { type: q.type, topic: q.t.id, answer: q.answer, opts: q.opts };
  Promise.all([PE.load(), PE.loadQuiz()]).then(([data, qb]) => {
    all = data; bank = (qb || []).filter(b => byId(b.topic));
    if (domain !== 'ALL' && !PE.domains(all).includes(domain)) domain = 'ALL';
    PE.domainChips($('domainChips'), all, domain, d => { domain = d; sessionStorage.setItem('pe-domain', d); bankQueue = []; build(); if (view === 'quiz') nextQuestion(); });
    build(params.get('id') || topicOnly || null);
    setView(params.get('view') || view);
  }).catch(() => { $('progress').textContent = '데이터를 불러오지 못했어요.'; });
})();
