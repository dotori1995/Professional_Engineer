(function () {
  const PE = window.PE;
  const $ = id => document.getElementById(id);
  const params = PE.params();
  const STORE = 'pe-write-v1';

  let all = [], domain = '', topicOnly = params.get('topic') || '';
  let mode = 'write';
  let pool = [], idx = 0, t = null;
  let phase = 'prompt'; // prompt | reveal | result
  let secs = 0, timerId = 0;
  let checked = new Set(), notes = '';

  const loadStore = () => { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; } };
  const saveStore = s => { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch (e) {} };
  const resultOf = id => (loadStore()[id] || null);

  function shuffled(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }

  function buildPool() {
    const curated = all.filter(x => x.domain === domain && (x.keywords_must || []).length);
    let list = curated.length ? curated : all.filter(x => x.domain === domain && (x.keywords || []).length);
    if (topicOnly) {
      const one = all.find(x => x.id === topicOnly);
      if (one) list = [one];
    }
    // missed 필수 first
    const st = loadStore();
    list = list.slice().sort((a, b) => {
      const ra = st[a.id], rb = st[b.id];
      const ma = ra && ra.missed && ra.missed.length ? 0 : 1;
      const mb = rb && rb.missed && rb.missed.length ? 0 : 1;
      if (ma !== mb) return ma - mb;
      return (ra && ra.at || 0) - (rb && rb.at || 0);
    });
    // preview: prefer NW_185
    const pref = list.find(x => x.id === 'NW_185');
    if (pref && !topicOnly) list = [pref].concat(list.filter(x => x.id !== 'NW_185'));
    return list;
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
    // fallback: quiz_terms or flat keywords
    if ((topic.quiz_terms || []).length) return topic.quiz_terms;
    return (topic.keywords || []).slice(0, 8);
  }
  function refList(topic) {
    if ((topic.keywords_ref || []).length) return topic.keywords_ref;
    return [];
  }

  function render() {
    const quiz = $('quiz');
    const primary = $('quizPrimary');
    const skip = $('quizSkip');
    if (!t) {
      quiz.innerHTML = '<div class="empty">서술 연습할 토픽이 없어요.<br>필수 키워드가 있는 토픽부터 열어 주세요.</div>';
      primary.disabled = true; skip.hidden = true;
      return;
    }
    const name = PE.esc(PE.name(t));
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
      PE.fit(quiz);
      return;
    }

    if (phase === 'reveal') {
      const must = mustList(t), ref = refList(t);
      const mustHtml = must.map((k, i) => kwChip('m', i, k)).join('');
      const refHtml = ref.map((k, i) => kwChip('r', i, k)).join('');
      const got = must.filter((_, i) => checked.has('m' + i)).length;
      quiz.innerHTML = `
        <div class="wbar"><span class="wtype">답안</span><span class="wscore" id="wScore">${got}/${must.length} 필수</span></div>
        <div class="wtitle-sm">${name}</div>
        <div class="lbl">개념·정의</div>
        <div class="wdef">${PE.gl(t.definition || '')}</div>
        <div class="lbl">목차</div>
        ${PE.outlineHtml(t.outline, true)}
        <div class="lbl must-lbl">★ 필수 키워드 <span class="wnote">비슷한 표현이면 체크</span></div>
        <div class="wkws" id="wMust">${mustHtml || '<span class="meta">없음</span>'}</div>
        ${ref.length ? `<div class="lbl">참고 키워드</div><div class="wkws" id="wRef">${refHtml}</div>` : ''}
        ${notes.trim() ? `<div class="lbl">내가 적은 것</div><div class="wnotes">${PE.esc(notes)}</div>` : ''}`;
      quiz.querySelectorAll('.wkw').forEach(b => b.addEventListener('click', () => {
        const id = b.dataset.id;
        if (checked.has(id)) checked.delete(id); else checked.add(id);
        b.classList.toggle('on', checked.has(id));
        const got2 = must.filter((_, i) => checked.has('m' + i)).length;
        const el = $('wScore'); if (el) el.textContent = got2 + '/' + must.length + ' 필수';
      }));
      primary.textContent = '결과 저장'; primary.disabled = false;
      skip.hidden = false; skip.textContent = '다시';
      PE.fit(quiz);
      return;
    }

    // result
    const must = mustList(t);
    const got = must.filter((_, i) => checked.has('m' + i));
    const missed = must.filter((_, i) => !checked.has('m' + i));
    quiz.innerHTML = `
      <div class="wbar"><span class="wtype">결과</span></div>
      <div class="wresult">
        <div class="wbig">${got.length}<span>/${must.length}</span></div>
        <div class="wbig-l">필수 키워드</div>
        <div class="wtitle-sm">${name}</div>
      </div>
      ${missed.length ? `<div class="lbl">놓친 필수</div><ul class="wmiss">${missed.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : `<div class="wok">필수 키워드를 모두 떠올렸습니다</div>`}
      ${got.length ? `<div class="lbl">맞힌 필수</div><ul class="whit">${got.map(k => `<li>${PE.gl(k)}</li>`).join('')}</ul>` : ''}`;
    primary.textContent = '다음 토픽'; primary.disabled = false;
    skip.hidden = false; skip.textContent = '같은 토픽 다시';
    PE.fit(quiz);
  }

  function kwChip(prefix, i, text) {
    const id = prefix + i;
    return `<button type="button" class="wkw${checked.has(id) ? ' on' : ''}" data-id="${id}">${PE.gl(text)}</button>`;
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
    stopTimer();
    idx = ((i % pool.length) + pool.length) % pool.length;
    t = pool[idx];
    phase = 'prompt';
    checked = new Set();
    notes = '';
    startTimer();
    render();
  }

  $('quizPrimary').addEventListener('click', () => {
    if (!t) return;
    if (phase === 'prompt') {
      const dump = $('wDump'); if (dump) notes = dump.value;
      phase = 'reveal'; render();
    } else if (phase === 'reveal') {
      saveResult(); phase = 'result'; render();
    } else {
      openTopic(idx + 1);
    }
  });
  $('quizSkip').addEventListener('click', () => {
    if (phase === 'reveal') { phase = 'prompt'; checked = new Set(); startTimer(); render(); return; }
    if (phase === 'result') { openTopic(idx); return; }
    openTopic(idx + 1);
  });

  addEventListener('resize', () => PE.fit($('quiz')));
  PE.load().then(data => {
    all = data;
    const tt = topicOnly && all.find(x => x.id === topicOnly);
    if (tt && tt.domain !== PE.cur) PE.setDomain(tt.domain);
    domain = PE.cur;
    // drawer label
    document.querySelectorAll('.dr-links a[href*="/quiz/"]').forEach(a => { a.textContent = '서술'; });
    pool = buildPool();
    openTopic(0);
  }).catch(() => { $('quiz').innerHTML = '<div class="empty">데이터를 불러오지 못했어요.</div>'; });
})();
