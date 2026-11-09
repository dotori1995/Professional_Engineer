(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const params = PE.params();
  const STORE = 'pe-write-v1';

  let all = [], domain = '', topicOnly = params.get('topic') || '';
  let pool = [], idx = 0, t = null;
  let phase = 'prompt'; // prompt | reveal | result
  let secs = 0, timerId = 0;
  let checked = new Set(), notes = '';
  let shuffle = params.get('shuffle') === '1' || localStorage.getItem('pe-quiz-shuffle') === '1';
  let impOnly = false;
  try { impOnly = localStorage.getItem('pe-imp-only') === '1'; } catch (e) {}

  const loadStore = () => { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; } };
  const saveStore = s => { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch (e) {} };
  const resultOf = id => (loadStore()[id] || null);

  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }

  function baseList() {
    const curated = all.filter(x => x.domain === domain && (x.keywords_must || []).length);
    let list = curated.length ? curated : all.filter(x => x.domain === domain && (x.keywords || []).length);
    // 토픽에서 들어와도 도메인 전체를 넘겨 볼 수 있게 하고, 그 토픽부터 시작
    if (topicOnly && !list.some(x => x.id === topicOnly)) {
      const one = all.find(x => x.id === topicOnly);
      if (one) list = [one].concat(list);
    }
    return list;
  }

  function buildPool(keepId) {
    let list = baseList();
    if (impOnly) list = list.filter(x => PE.isImportant(x));
    pool = shuffle ? shuffled(list) : list.slice();
    idx = keepId ? Math.max(0, pool.findIndex(x => x.id === keepId)) : 0;
    if (keepId && idx < 0) idx = 0;
    const btn = $('shuffleBtn');
    if (btn) btn.setAttribute('aria-pressed', String(shuffle));
    const ib = $('impOnly'); if (ib) { ib.setAttribute('aria-pressed', String(impOnly)); ib.classList.toggle('on', impOnly); }
    updateProgress();
  }

  function updateProgress() {
    const n = pool.length;
    const bar = $('bar'), prog = $('progress');
    if (bar) bar.style.width = (n ? Math.round((idx + 1) / n * 100) : 0) + '%';
    if (prog) prog.textContent = n ? `${idx + 1} / ${n}` : '0 / 0';
  }

  function stopTimer() { if (timerId) { clearInterval(timerId); timerId = 0; } }
  function startTimer() {
    stopTimer();
    secs = 0;
    timerId = setInterval(() => {
      secs += 1;
      const el = document.getElementById('wTimer');
      if (el) el.textContent = fmt(secs);
    }, 1000);
  }
  function fmt(s) {
    const m = Math.floor(s / 60), r = s % 60;
    return String(m).padStart(2, '0') + ':' + String(r).padStart(2, '0');
  }

  function mustList(topic) {
    if ((topic.keywords_must || []).length) return topic.keywords_must;
    if ((topic.quiz_terms || []).length) return topic.quiz_terms;
    return (topic.keywords || []).slice(0, 8);
  }
  function refList(topic) {
    if ((topic.keywords_ref || []).length) return topic.keywords_ref;
    return [];
  }

  // 내가 적은 것과 키워드 자동 비교: 한글/영문/약어 중 하나라도 적었으면 체크
  const norm = x => String(x || '').toLowerCase().replace(/[\s\-\u2010-\u2015_.·]/g, '');
  function kwTokens(k) {
    return String(k).split(/[()（）,，/·;]/).map(norm).filter(x => x.length >= 2);
  }
  function autoCheck(list, prefix) {
    const n = norm(notes);
    if (!n) return;
    // 1) 정규화 후 부분 일치  2) Fuse.js 유사도(오타·띄어쓰기·조금 다른 표현)
    const segs = String(notes).split(/[\n,，·;/]+/).map(norm).filter(x => x.length >= 2);
    const fuse = window.Fuse && segs.length ? new window.Fuse(segs, { includeScore: true, threshold: 0.34, ignoreLocation: true, minMatchCharLength: 2 }) : null;
    const fuzzy = tok => tok.length >= 3 && fuse && fuse.search(tok).some(r => r.score <= 0.34);
    list.forEach((k, i) => {
      const toks = kwTokens(k);
      if (toks.some(tok => n.includes(tok)) || toks.some(fuzzy)) { checked.add(prefix + i); autoIds.add(prefix + i); }
    });
  }
  let autoIds = new Set();

  function render() {
    const quiz = $('quiz');
    const primary = $('quizPrimary');
    const skip = $('quizSkip');
    updateProgress();
    if (!t) {
      quiz.innerHTML = '<div class="empty">서술 연습할 토픽이 없어요.<br>필수 키워드가 있는 토픽부터 열어 주세요.</div>';
      primary.disabled = true; skip.hidden = true;
      return;
    }
    const name = PE.nameHtml(t);
    const prev = resultOf(t.id);
    const prevHtml = prev ? `<div class="wmeta">이전 ${prev.score}/${prev.total} · 놓친 ${prev.missed.length}개</div>` : '';

    if (phase === 'prompt') {
      quiz.innerHTML = `
        <div class="wbar"><span class="wtype">서술 연습</span><span class="wtimer" id="wTimer">${fmt(secs)}</span></div>
        <div class="wprompt">
          <div class="wlabel">토픽</div>
          <h2 class="wtitle">${name}</h2>
          <p class="whint">키워드를 떠올려 쏟아내 보세요</p>
        </div>
        <textarea class="wdump" id="wDump" rows="8" placeholder="떠오르는 키워드를 여기에 적어도 됩니다 (선택)">${PE.esc(notes)}</textarea>
        ${prevHtml}`;
      primary.textContent = '답안 보기'; primary.disabled = false;
      skip.hidden = false; skip.textContent = '다른 토픽';
      const dump = $('wDump');
      dump && dump.addEventListener('input', () => { notes = dump.value; });
      quiz.classList.remove('scroll'); PE.fit(quiz);
      return;
    }

    if (phase === 'reveal') {
      const must = mustList(t), ref = refList(t);
      const mustHtml = must.map((k, i) => kwChip('m', i, k)).join('');
      const refHtml = ref.map((k, i) => kwChip('r', i, k)).join('');
      const got = must.filter((_, i) => checked.has('m' + i)).length;
      quiz.innerHTML = `
        <div class="wbar"><span class="wtype">답안</span><span class="wscore" id="wScore">${got}/${must.length} 필수</span><a class="wtopic" href="${PE.topicUrl(t.id)}">토픽</a></div>
        ${notes.trim() ? `<div class="lbl">내가 적은 것 <span class="wnote">${autoIds.size ? '적은 키워드는 자동 체크됨' : '자동 일치 없음'}</span></div><div class="wnotes">${PE.esc(notes)}</div>` : ''}
        <div class="wtitle-sm">${name}</div>
        <div class="lbl">개념·정의</div>
        <div class="wdef">${PE.gl(t.definition || '')}</div>
        <div class="lbl">목차</div>
        ${PE.outlineHtml(t.outline, true)}
        <div class="lbl must-lbl">★ 필수 키워드 <span class="wnote">비슷한 표현이면 체크</span></div>
        <div class="wkws" id="wMust">${mustHtml || '<span class="meta">없음</span>'}</div>
        ${ref.length ? `<div class="lbl">참고 키워드</div><div class="wkws" id="wRef">${refHtml}</div>` : ''}`;
      quiz.querySelectorAll('.wkw').forEach(b => b.addEventListener('click', () => {
        const id = b.dataset.id;
        if (checked.has(id)) checked.delete(id); else checked.add(id);
        b.classList.toggle('on', checked.has(id));
        const got2 = must.filter((_, i) => checked.has('m' + i)).length;
        const el = $('wScore'); if (el) el.textContent = got2 + '/' + must.length + ' 필수';
      }));
      primary.textContent = '결과 저장'; primary.disabled = false;
      skip.hidden = false; skip.textContent = '다시';
      PE.scrollFit(quiz);
      return;
    }

    // result
    const must = mustList(t);
    const got = must.filter((_, i) => checked.has('m' + i));
    const missed = must.filter((_, i) => !checked.has('m' + i));
    quiz.innerHTML = `
      <div class="wbar"><span class="wtype">결과</span><a class="wtopic" href="${PE.topicUrl(t.id)}">토픽</a></div>
      <div class="wresult">
        <div class="wbig">${got.length}<span>/${must.length}</span></div>
        <div class="wbig-l">필수 키워드</div>
        <div class="wtitle-sm">${name}</div>
      </div>
      ${missed.length ? `<div class="lbl">놓친 필수</div><ul class="wmiss">${missed.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : `<div class="wok">필수 키워드를 모두 떠올렸습니다</div>`}
      ${got.length ? `<div class="lbl">맞힌 필수</div><ul class="whit">${got.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : ''}`;
    primary.textContent = '다음 토픽'; primary.disabled = false;
    skip.hidden = false; skip.textContent = '같은 토픽 다시';
    PE.scrollFit(quiz);
  }

  function kwChip(prefix, i, text) {
    const id = prefix + i;
    return `<button type="button" class="wkw${checked.has(id) ? ' on' : ''}${autoIds.has(id) ? ' auto' : ''}" data-id="${id}">${PE.gl(text)}</button>`;
  }

  function saveResult() {
    const must = mustList(t);
    const got = must.filter((_, i) => checked.has('m' + i));
    const missed = must.filter((_, i) => !checked.has('m' + i));
    const st = loadStore();
    st[t.id] = { score: got.length, total: must.length, missed, at: Date.now(), notes: notes.slice(0, 500) };
    saveStore(st);
  }

  function openTopic(i) {
    if (!pool.length) {
      t = null; phase = 'prompt'; checked = new Set(); notes = '';
      stopTimer(); render(); return;
    }
    stopTimer();
    idx = ((i % pool.length) + pool.length) % pool.length;
    t = pool[idx];
    phase = 'prompt';
    checked = new Set();
    notes = '';
    startTimer();
    render();
  }

  function go(d) {
    if (!pool.length) return;
    let n = idx + d;
    if (n < 0) n = pool.length - 1;
    if (n >= pool.length) { n = 0; if (shuffle) pool = shuffled(pool); }
    openTopic(n);
  }

  function typingOrSelecting() {
    const a = document.activeElement;
    if (!a) return false;
    const tag = (a.tagName || '').toLowerCase();
    if (tag === 'textarea' || tag === 'input') return true;
    const sel = window.getSelection && window.getSelection();
    if (sel && !sel.isCollapsed && String(sel).length) return true;
    return false;
  }

  $('quizPrimary').addEventListener('click', () => {
    if (!t) return;
    if (phase === 'prompt') {
      const dump = $('wDump'); if (dump) notes = dump.value;
      autoIds = new Set();
      autoCheck(mustList(t), 'm'); autoCheck(refList(t), 'r');
      phase = 'reveal'; render();
    } else if (phase === 'reveal') {
      saveResult(); phase = 'result'; render();
    } else {
      go(1);
    }
  });
  $('quizSkip').addEventListener('click', () => {
    if (phase === 'reveal') { phase = 'prompt'; checked = new Set(); autoIds = new Set(); startTimer(); render(); return; }
    if (phase === 'result') { openTopic(idx); return; }
    go(1);
  });
  $('shuffleBtn').addEventListener('click', () => {
    shuffle = !shuffle;
    localStorage.setItem('pe-quiz-shuffle', shuffle ? '1' : '0');
    const keep = t && t.id;
    buildPool(keep);
    openTopic(idx);
  });
  $('impOnly') && $('impOnly').addEventListener('click', () => {
    impOnly = !impOnly;
    try { localStorage.setItem('pe-imp-only', impOnly ? '1' : '0'); } catch (e) {}
    const keep = t && t.id;
    buildPool(keep);
    openTopic(idx);
  });

  // 스와이프 (textarea 입력·텍스트 선택 중에는 무시)
  const stage = document.querySelector('.page-quiz .stage') || $('quiz');
  let sx = 0, sy = 0, moved = false;
  stage.addEventListener('touchstart', e => {
    if (typingOrSelecting()) { sx = 0; return; }
    sx = e.touches[0].clientX; sy = e.touches[0].clientY; moved = false;
  }, { passive: true });
  stage.addEventListener('touchend', e => {
    if (!sx) return;
    if (typingOrSelecting()) { sx = 0; return; }
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    sx = 0;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) { moved = true; go(dx < 0 ? 1 : -1); }
  });
  document.addEventListener('keydown', e => {
    if (typingOrSelecting()) return;
    if (e.key === 'ArrowRight') go(1);
    if (e.key === 'ArrowLeft') go(-1);
  });

  addEventListener('resize', () => PE.fit($('quiz')));
  PE.load().then(data => {
    all = data;
    const tt = topicOnly && all.find(x => x.id === topicOnly);
    if (tt && tt.domain !== PE.cur) PE.setDomain(tt.domain);
    domain = PE.cur;
    document.querySelectorAll('.dr-links a[href*="/quiz/"]').forEach(a => { a.textContent = '서술'; });
    buildPool(topicOnly || null);
    openTopic(idx);
  }).catch(() => {
    $('quiz').innerHTML = '<div class="empty">데이터를 불러오지 못했어요.</div>';
    if ($('progress')) $('progress').textContent = '오류';
  });
})();
