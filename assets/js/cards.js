// 카드: 쇼츠처럼 세로로 넘기는 카드 + 자동 넘김 타이머 + 돌발 서술 문제
(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const feed = $('feed'), fill = $('shFill'), shorts = $('shorts'), stateEl = $('shState');
  const params = PE.params();
  const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');

  const TIMES = [0, 3, 5, 8];                 // 0 = 자동 넘김 끔
  let all = [], deck = [], items = [], idx = 0, domain = '';
  let shuffle = params.get('shuffle') === '1' || store('pe-shuffle') === '1';
  let impOnly = store('pe-imp-only') === '1';
  let sec = parseInt(store('pe-card-auto') ?? '5', 10); if (!TIMES.includes(sec)) sec = 5;
  let popOn = store('pe-pop-quiz') !== '0';

  // ---------- 덱 구성 ----------
  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
  const mustList = t => (t.keywords_must || []).length ? t.keywords_must : (t.quiz_terms || []).length ? t.quiz_terms : (t.keywords || []).slice(0, 8);
  function makeItems() {
    items = [];
    let gap = rnd(5, 8), seen = [];
    deck.forEach((t, i) => {
      items.push({ type: 'card', t });
      seen.push(t);
      if (popOn && deck.length >= 4 && --gap === 0 && i < deck.length - 1) {
        // 방금 지나간 카드 중 하나를 다시 물어봄
        const cands = seen.filter(x => x.definition || mustList(x).length);
        if (cands.length) {
          const q = cands[Math.floor(Math.random() * cands.length)];
          let ask = Math.random() < 0.5 ? 'def' : 'kw';
          if (ask === 'def' && !q.definition) ask = 'kw';
          if (ask === 'kw' && !mustList(q).length) ask = 'def';
          items.push({ type: 'quiz', t: q, ask, secs: ask === 'def' ? 40 : 50, notes: '' });
        }
        seen = []; gap = rnd(5, 8);
      }
    });
  }
  function build(keepId) {
    let d = all.filter(t => t.domain === domain);
    if (impOnly) d = d.filter(t => PE.isImportant(t));
    deck = shuffle ? shuffled(d) : d;
    makeItems();
    let start = keepId ? items.findIndex(it => it.type === 'card' && it.t.id === keepId) : 0;
    if (start < 0) start = 0;
    $('shuffleBtn').setAttribute('aria-pressed', String(shuffle)); $('shuffleBtn').classList.toggle('on', shuffle);
    $('impOnly').setAttribute('aria-pressed', String(impOnly)); $('impOnly').classList.toggle('on', impOnly);
    syncChips();
    feed.innerHTML = items.length ? items.map((it, i) => `<section class="slide${it.type === 'quiz' ? ' quiz-slide' : ''}" data-i="${i}"></section>`).join('')
      : '<div class="empty">카드가 없어요</div>';
    rendered.clear();
    idx = -1;
    feed.scrollTop = start * feed.clientHeight;
    setCurrent(start, true);
  }
  function syncChips() {
    $('timerBtn').textContent = sec ? `⏱ ${sec}초` : '⏱ 끔';
    $('timerBtn').classList.toggle('on', !!sec);
    $('popBtn').textContent = popOn ? '🔥 돌발 켬' : '🔥 돌발 끔';
    $('popBtn').classList.toggle('on', popOn); $('popBtn').setAttribute('aria-pressed', String(popOn));
  }

  // ---------- 슬라이드 그리기 (현재 ±2장만) ----------
  const rendered = new Set();
  const badges = t => `${PE.esc(t.id)}${PE.isImportant(t) ? ' <span class="badge star-badge">중요</span>' : ''}${PE.reviewFixed && PE.reviewFixed(t) ? ' <span class="badge fix">검토 수정</span>' : ''}`;
  const sparkles = () => Array.from({ length: 7 }, () => `<i class="spk" style="--x:${rnd(6, 94)}%;--y:${rnd(8, 88)}%;--d:${rnd(0, 45) / 100}s;--s:${rnd(70, 140) / 100}"></i>`).join('');
  function cardHtml(t) {
    PE.glTopic = t;
    const kws = (t.keywords || []);
    return `<div class="sl-card">${sparkles()}
      <div class="code">${badges(t)}</div>
      <h2 class="sl-title">${PE.nameHtml(t)}</h2>
      <div class="sl-tap">길게 눌러 답 보기</div>
      <div class="ans">
        <div class="label">정의</div><p class="def">${PE.esc(t.definition || '-')}</p>
        ${t.dueum ? `<div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
        ${kws.length ? `<div class="label">키워드</div><ul class="kw">${kws.map((k, i) => `<li style="--k:${i}">${PE.gl(k)}</li>`).join('')}</ul>` : ''}
        ${(t.outline || []).length ? `<div class="label">목차</div>${PE.outlineHtml(t.outline, false)}` : ''}
        <a class="more" href="${PE.topicUrl(t.id)}">자세히 보기 →</a>
      </div></div>`;
  }
  function quizHtml(it) {
    const t = it.t; PE.glTopic = t;
    const q = it.ask === 'def' ? '이 토픽의 <b>개념·정의</b>를 서술하세요' : '이 토픽의 <b>핵심 키워드</b>를 적어 보세요';
    return `<div class="sl-card pq">
      <div class="pq-burst" aria-hidden="true"><span>🔥 돌발 문제!</span></div>
      <div class="pq-head"><span class="pq-tag">🔥 돌발 문제!</span><span class="pq-time" data-time>${it.secs}초</span></div>
      <div class="pq-body">
        <div class="wlabel">토픽 · ${PE.esc(t.id)}</div>
        <h2 class="wtitle">${PE.nameHtml(t)}</h2>
        <p class="pq-q">${q}</p>
        <textarea class="wdump" rows="4" placeholder="적어도 되고, 머릿속으로만 떠올려도 돼요">${PE.esc(it.notes)}</textarea>
        <button type="button" class="btn know pq-reveal">답안 보기</button>
      </div>
      <div class="pq-ans"></div></div>`;
  }
  function renderAround(c) {
    for (const i of Array.from(rendered)) if (Math.abs(i - c) > 3) { const s = slideEl(i); if (s) s.innerHTML = ''; rendered.delete(i); }
    for (let i = Math.max(0, c - 2); i <= Math.min(items.length - 1, c + 2); i++) {
      if (rendered.has(i)) continue;
      const s = slideEl(i), it = items[i]; if (!s) continue;
      it.revealed = false; s.classList.remove('open', 'enter');
      s.innerHTML = it.type === 'quiz' ? quizHtml(it) : cardHtml(it.t);
      if (it.type === 'quiz') {
        const ta = s.querySelector('textarea');
        ta.addEventListener('input', () => { it.notes = ta.value; });
        ta.addEventListener('focus', () => { typing = true; });
        ta.addEventListener('blur', () => { typing = false; });
        s.querySelector('.pq-reveal').addEventListener('click', e => { e.stopPropagation(); revealQuiz(i); });
      }
      rendered.add(i);
    }
  }
  const slideEl = i => feed.querySelector(`.slide[data-i="${i}"]`);

  // ---------- 정답 공개 ----------
  function reveal(i, on) {
    const it = items[i], s = slideEl(i); if (!it || !s) return;
    if (it.type === 'quiz') { revealQuiz(i); return; }
    it.revealed = on === undefined ? !it.revealed : on;
    s.classList.toggle('open', it.revealed);
    if (it.revealed) { const a = s.querySelector('.ans'); if (a) a.scrollTop = 0; }
  }
  const norm = x => String(x || '').toLowerCase().replace(/[\s\-\u2010-\u2015_.·]/g, '');
  const kwTokens = k => String(k).split(/[()（）,，/·;:]/).map(x => x.trim()).filter(x => norm(x).length >= 2);
  const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  function markText(text, kws) {
    // 정의 문장 안의 키워드를 형광펜으로
    const toks = Array.from(new Set(kws.flatMap(kwTokens))).sort((a, b) => b.length - a.length).map(PE.esc);
    let h = PE.esc(text);
    if (!toks.length) return h;
    const re = new RegExp('(' + toks.map(reEsc).join('|') + ')', 'gi');
    return h.split(/(<[^>]+>)/).map(p => p.startsWith('<') ? p : p.replace(re, '<mark>$1</mark>')).join('');
  }
  function revealQuiz(i) {
    const it = items[i], s = slideEl(i); if (!it || !s || it.revealed) return;
    it.revealed = true; PE.glTopic = it.t;
    if (i === idx) stopClock();
    const t = it.t, must = mustList(t), n = norm(it.notes);
    const hit = k => n && kwTokens(k).some(x => n.includes(norm(x)));
    const got = must.filter(hit).length;
    s.querySelector('.pq-ans').innerHTML = `
      <div class="pq-head"><span class="pq-tag done">답안</span>${n ? `<span class="wscore">${got}/${must.length} 키워드</span>` : ''}<a class="wtopic" href="${PE.topicUrl(t.id)}">토픽</a></div>
      <div class="wtitle-sm">${PE.nameHtml(t)}</div>
      ${it.notes.trim() ? `<div class="lbl">내가 적은 것</div><div class="wnotes">${PE.esc(it.notes)}</div>` : ''}
      <div class="lbl">개념·정의</div>
      <div class="wdef">${markText(t.definition || '-', must)}</div>
      ${t.dueum ? `<div class="dueum-box">💡 ${PE.esc(t.dueum)}</div>` : ''}
      <div class="lbl must-lbl">★ 필수 키워드${n ? ' <span class="wnote">✓ = 내가 적은 것</span>' : ''}</div>
      <div class="wkws">${must.map((k, j) => `<span class="wkw hl${hit(k) ? ' on' : ''}" style="--k:${j}">${hit(k) ? '✓ ' : ''}${PE.gl(k)}</span>`).join('') || '<span class="meta">없음</span>'}</div>
      <p class="pq-next">위로 밀거나 ▼ 눌러 계속 →</p>`;
    s.classList.add('open');
    const ta = s.querySelector('textarea'); if (ta) ta.blur();
    if (i === idx) setFill(1);
  }

  // ---------- 현재 카드 / 타이머 ----------
  let dur = 0, elapsed = 0, last = 0, raf = 0, paused = false, holding = false, typing = false;
  function setCurrent(i, force) {
    if (!items.length) { $('progress').textContent = '0 / 0'; setFill(0); return; }
    i = Math.max(0, Math.min(items.length - 1, i));
    if (i === idx && !force) return;
    idx = i;
    renderAround(i);
    feed.querySelectorAll('.slide.enter').forEach(s => s.classList.remove('enter'));
    const s = slideEl(i);
    if (s) { void s.offsetWidth; s.classList.add('enter'); }
    const it = items[i];
    const cardNo = items.slice(0, i + 1).filter(x => x.type === 'card').length;
    $('progress').textContent = it.type === 'quiz' ? '🔥 돌발' : `${cardNo} / ${deck.length}`;
    shorts.classList.toggle('is-quiz', it.type === 'quiz');
    paused = false; showState('');
    startClock();
  }
  function startClock() {
    stopClock();
    const it = items[idx];
    dur = it.type === 'quiz' ? (it.revealed ? 0 : it.secs * 1000) : sec * 1000;
    elapsed = 0; last = performance.now();
    shorts.classList.toggle('no-timer', !dur);
    setFill(it.type === 'quiz' && it.revealed ? 1 : 0);
    if (dur) raf = requestAnimationFrame(tick);
  }
  function stopClock() { if (raf) cancelAnimationFrame(raf); raf = 0; }
  function setFill(p) { fill.style.transform = `scaleX(${Math.min(1, p)})`; }
  function tick(now) {
    const dt = now - last; last = now;
    const it = items[idx];
    const quizFrozen = false;
    if (!paused && !(holding && it.type === 'card') && !document.hidden && !quizFrozen) elapsed += dt;
    const p = elapsed / dur;
    setFill(p);
    if (it.type === 'quiz') {
      const el = slideEl(idx) && slideEl(idx).querySelector('[data-time]');
      const left = Math.max(0, Math.ceil((dur - elapsed) / 1000));
      if (el) { el.textContent = left + '초'; el.classList.toggle('hurry', left <= 10); }
      if (p >= 1) { revealQuiz(idx); return; }       // 시간 끝 → 답 공개, 자동 넘김은 멈춤
    } else {
      if (p >= 0.5 && !it.revealed && !it.manual) reveal(idx, true);  // 절반 지나면 답이 톡 튀어나옴
      if (p >= 1) { go(1); return; }
    }
    raf = requestAnimationFrame(tick);
  }
  function showState(txt) {
    stateEl.textContent = txt;
    stateEl.classList.remove('show'); void stateEl.offsetWidth;
    if (txt) stateEl.classList.add('show');
  }
  function togglePause() {
    const it = items[idx]; if (!it) return;
    if (it.type === 'quiz') { revealQuiz(idx); return; }       // 돌발 문제: 탭 = 답 보기
    if (!sec) { it.manual = true; reveal(idx); return; }        // 타이머 꺼짐: 탭 = 답 보기
    paused = !paused;
    showState(paused ? '⏸' : '▶');
    shorts.classList.toggle('paused', paused);
  }

  // ---------- 이동 ----------
  let navTarget = null, navTimer = 0;
  function go(d) {
    if (!items.length) return;
    let n = idx + d;
    if (n < 0) n = items.length - 1;
    if (n >= items.length) n = 0;
    const jump = Math.abs(n - idx) > 1;
    navTarget = n; clearTimeout(navTimer); navTimer = setTimeout(() => { navTarget = null; }, 900);
    feed.scrollTo({ top: n * feed.clientHeight, behavior: reduced.matches || jump ? 'auto' : 'smooth' });
    setCurrent(n);
  }
  let scrollT = 0;
  feed.addEventListener('scroll', () => {
    if (!items.length) return;
    const h = feed.clientHeight || 1;
    if (navTarget !== null) { if (Math.abs(feed.scrollTop - navTarget * h) < 2) navTarget = null; return; }
    clearTimeout(scrollT);
    scrollT = setTimeout(() => setCurrent(Math.round(feed.scrollTop / h)), 90);
  }, { passive: true });
  addEventListener('resize', () => {           // 키보드가 올라와도 같은 카드에 고정
    if (!items.length) return;
    navTarget = idx; clearTimeout(navTimer); navTimer = setTimeout(() => { navTarget = null; }, 400);
    feed.scrollTop = idx * feed.clientHeight;
  });

  // 휠: 한 번에 한 장
  let lastNav = 0, lastWheel = 0;
  const canScroll = (el, dy) => { for (; el && el !== feed; el = el.parentElement) { if (el.scrollHeight > el.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(el).overflowY)) { if (dy > 0 ? el.scrollTop + el.clientHeight < el.scrollHeight - 1 : el.scrollTop > 0) return true; } } return false; };
  feed.addEventListener('wheel', e => {
    if (Math.abs(e.deltaY) < Math.abs(e.deltaX) || canScroll(e.target, e.deltaY)) return;
    e.preventDefault();
    const now = performance.now(), quiet = now - lastWheel > 200; lastWheel = now;
    if (Math.abs(e.deltaY) < 4 || (now - lastNav < 650) || (!quiet && now - lastNav < 1200)) return;
    lastNav = now; go(e.deltaY > 0 ? 1 : -1);
  }, { passive: false });

  // 탭 = 멈춤/재생, 길게 누르기 = 답 보기
  let px = 0, py = 0, pt = 0, lpTimer = 0, lpFired = false, down = false;
  const interactive = el => el.closest('a,button,textarea,input,.pq-ans');
  feed.addEventListener('pointerdown', e => {
    if (e.button > 0 || interactive(e.target)) return;
    down = true; px = e.clientX; py = e.clientY; pt = performance.now(); lpFired = false; holding = true;
    clearTimeout(lpTimer);
    lpTimer = setTimeout(() => {
      if (!down) return;
      lpFired = true; holding = false;
      const it = items[idx]; if (!it) return;
      if (it.type === 'quiz') { revealQuiz(idx); return; }
      it.manual = true; reveal(idx, true);
      if (sec) { paused = true; shorts.classList.add('paused'); showState('👀'); }
      if (navigator.vibrate) try { navigator.vibrate(15); } catch (er) {}
    }, 450);
  });
  feed.addEventListener('pointermove', e => { if (down && Math.hypot(e.clientX - px, e.clientY - py) > 10) { down = false; holding = false; clearTimeout(lpTimer); } });
  const endPress = e => {
    if (!down) { holding = false; return; }
    down = false; holding = false; clearTimeout(lpTimer);
    if (e.type === 'pointerup' && !lpFired && performance.now() - pt < 400) togglePause();
  };
  feed.addEventListener('pointerup', endPress);
  feed.addEventListener('pointercancel', endPress);
  feed.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') endPress({ type: 'leave' }); });
  feed.addEventListener('contextmenu', e => { if (!interactive(e.target)) e.preventDefault(); });

  document.addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('textarea,input')) { if (e.key === 'Escape') e.target.blur(); return; }
    if (['ArrowDown', 'ArrowRight', 'PageDown', 'j'].includes(e.key)) { e.preventDefault(); go(1); }
    else if (['ArrowUp', 'ArrowLeft', 'PageUp', 'k'].includes(e.key)) { e.preventDefault(); go(-1); }
    else if (e.key === ' ') { e.preventDefault(); togglePause(); }
    else if (e.key === 'Enter') { e.preventDefault(); const it = items[idx]; if (it) { it.manual = true; reveal(idx, true); } }
  });
  $('prevBtn').addEventListener('click', () => go(-1));
  $('nextBtn').addEventListener('click', () => go(1));

  // ---------- 옵션 ----------
  const curId = () => { for (let i = idx; i >= 0; i--) if (items[i] && items[i].type === 'card') return items[i].t.id; return null; };
  $('shuffleBtn').addEventListener('click', () => { shuffle = !shuffle; store('pe-shuffle', shuffle ? '1' : '0'); build(curId()); });
  $('impOnly').addEventListener('click', () => { impOnly = !impOnly; store('pe-imp-only', impOnly ? '1' : '0'); build(curId()); });
  $('timerBtn').addEventListener('click', () => {
    sec = TIMES[(TIMES.indexOf(sec) + 1) % TIMES.length]; store('pe-card-auto', String(sec)); syncChips();
    paused = false; shorts.classList.remove('paused'); showState(sec ? `⏱ ${sec}초` : '⏱ 끔');
    if (items[idx] && items[idx].type === 'card') startClock();
  });
  $('popBtn').addEventListener('click', () => { popOn = !popOn; store('pe-pop-quiz', popOn ? '1' : '0'); build(curId()); });
  document.addEventListener('visibilitychange', () => { last = performance.now(); });

  PE.load().then(data => {
    all = data;
    const tid = params.get('topic') || params.get('id'), tt = all.find(t => t.id === tid);
    if (tt && tt.domain !== PE.cur) PE.setDomain(tt.domain);
    domain = PE.cur;
    build(tid);
  }).catch(() => { $('progress').textContent = '데이터를 불러오지 못했어요.'; });
})();
