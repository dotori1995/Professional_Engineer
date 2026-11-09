(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const params = PE.params();
  let all = [];
  let domain = '';
  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  // ===== 객관식 =====
  // 문제 유형: bank(검수한 문제은행 _data/quiz) · kwOf(토픽의 키워드 찾기) · notKwOf(키워드가 아닌 것) · def(정의→토픽) · kw(토픽→키워드)
  const quiz = $('quiz');
  let score = { ok: 0, n: 0 }, q = null, bank = [], bankQueue = [], topicOnly = params.get('topic') || '', topicSeq = 0;
  const pick = (arr, k) => shuffled(arr).slice(0, k);
  const kwSet = t => (t.keywords || []).slice(0, 3).join(' · ');
  const norm = s => String(s || '').replace(/\s|\(.*?\)/g, '').toLowerCase();
  const byId = id => all.find(t => t.id === id);
  const inDomain = t => t.domain === domain;
  const topicText = t => norm([t.title, t.name, t.definition, (t.keywords || []).join(' '), JSON.stringify(t.sections || [])].join(' '));
  // 다른 토픽 키워드가 이 토픽에도 해당될 수 있으면 오답 보기로 쓰지 않음(quiz_avoid 양방향 + 본문 포함 여부 검사)
  function foreignTerms(t) {
    const txt = topicText(t), own = new Set((t.quiz_terms || []).map(norm));
    const out = [];
    all.filter(o => o.id !== t.id && (o.quiz_terms || []).length && inDomain(o)
      && !(t.quiz_avoid || []).includes(o.id) && !(o.quiz_avoid || []).includes(t.id)
      && !(t.quiz_groups || []).some(g => (o.quiz_groups || []).includes(g)))
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
    const tag = topicOnly ? ` · ${PE.esc(PE.name(byId(topicOnly)))} 집중 <a href="${PE.url('/quiz/')}?d=${encodeURIComponent(domain)}">전체 문제로</a>` : '';
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
  $('quizNext').addEventListener('click', nextQuestion);
  $('quizReset').addEventListener('click', () => { score = { ok: 0, n: 0 }; nextQuestion(); });
  PE.quizNext = nextQuestion;
  PE.quizState = () => q && { type: q.type, topic: q.t.id, answer: q.answer, opts: q.opts };
  addEventListener('resize', () => PE.fit(quiz));
  Promise.all([PE.load(), PE.loadQuiz()]).then(([data, qb]) => {
    all = data; bank = (qb || []).filter(b => byId(b.topic));
    const tt = topicOnly && byId(topicOnly); if (tt && tt.domain !== PE.cur) PE.setDomain(tt.domain);
    domain = PE.cur;
    nextQuestion();
  }).catch(() => { quiz.innerHTML = '<div class="empty">데이터를 불러오지 못했어요.</div>'; });
})();
