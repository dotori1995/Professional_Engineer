---
layout: null
permalink: /sw.js
---
// 간단한 서비스 워커: 정적 파일은 캐시 우선, data.json·페이지는 네트워크 우선(오프라인이면 캐시)
const VERSION = 'pe-{{ site.time | date: "%Y%m%d%H%M%S" }}';
const BASE = '{{ site.baseurl }}';
const PRECACHE = [
  BASE + '/', BASE + '/cards/', BASE + '/quiz/', BASE + '/topic/', BASE + '/data.json', BASE + '/glossary.json', BASE + '/quiz.json',
  BASE + '/assets/css/style.css', BASE + '/assets/js/app.js', BASE + '/assets/js/list.js',
  BASE + '/assets/js/cards.js', BASE + '/assets/js/quiz.js', BASE + '/assets/js/topic.js',
  BASE + '/assets/icons/icon-192.png', BASE + '/manifest.webmanifest'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const url = new URL(req.url);
  const networkFirst = req.mode === 'navigate' || (url.pathname.endsWith('/data.json') || url.pathname.endsWith('/glossary.json') || url.pathname.endsWith('/quiz.json'));
  if (networkFirst) {
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); return res;
    }).catch(() => caches.match(req, { ignoreSearch: true })));
  } else {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); return res;
    })));
  }
});
