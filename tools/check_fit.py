#!/usr/bin/env python3
"""토픽 화면 한 화면 맞춤 검사: 라이브 사이트 레이아웃에 로컬 _data를 주입해 360x740에서 확인.
사용: python3 tools/check_fit.py sw [ID ...]   → 배율(--s) 0.7 미만·tight2·overflow 토픽 출력"""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://dotori1995.github.io/Professional_Engineer'
dom = sys.argv[1].lower(); only = set(sys.argv[2:])
keys = re.findall(r'-\s*key:\s*(\w+)', (ROOT / '_config.yml').read_text())
allt = []
for k in keys:
    p = ROOT / '_data' / f'{k}.json'
    if p.exists(): allt += json.loads(p.read_text())
body = json.dumps(allt, ensure_ascii=False)
ids = [t['id'] for t in json.loads((ROOT / '_data' / f'{dom}.json').read_text()) if not only or t['id'] in only]
bad = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for vw, vh in ((360, 740),):
        ctx = b.new_context(viewport={'width': vw, 'height': vh}, service_workers='block', device_scale_factor=1)
        ctx.route(re.compile(r'.*/data\.json.*'), lambda r: r.fulfill(status=200, content_type='application/json', body=body))
        pg = ctx.new_page()
        for i, tid in enumerate(ids):
            pg.goto(f'{BASE}/topic/?id={tid}', wait_until='domcontentloaded')
            pg.wait_for_selector('[data-fit]', timeout=15000)
            pg.wait_for_timeout(150)
            r = pg.evaluate("""() => { const b = document.querySelector('[data-fit]'); return {fit: b.dataset.fit, s: parseFloat(b.style.getPropertyValue('--s')||'1'), cls: b.className}; }""")
            if '-v' in sys.argv[0:1] or __import__('os').environ.get('V'): print(tid, r)
            flag = r['fit'] != 'ok' or r['s'] < 0.7 or 'tight2' in r['cls']
            if flag: bad.append((tid, r))
        ctx.close()
    b.close()
for tid, r in bad: print('FIT', tid, r)
print(f'-- checked {len(ids)}, {len(bad)} flagged')
