// v4 — icônes servies en fichiers, icône notification monochrome
const CACHE = 'intentions-v4';
const STATIC_ASSETS = [
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/icon-notif-96.png',
];

self.addEventListener('install', e => {
  // Précacher les icônes statiques (pas le HTML)
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.url.includes('/api/')) return;
  // HTML : toujours réseau
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request));
    return;
  }
  // Assets statiques : cache d'abord
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});

// Notifications push
self.addEventListener('push', e => {
  if (!e.data) return;
  let payload;
  try { payload = e.data.json(); }
  catch { payload = { title: 'Intentions de Messes', body: e.data.text() }; }
  e.waitUntil(
    self.registration.showNotification(payload.title, {
      body:    payload.body,
      icon:    payload.icon  || '/static/icon-192.png',
      badge:   payload.badge || '/static/icon-notif-96.png',
      vibrate: [200, 100, 200],
      tag:     'intentions-matin',
      renotify: false,
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes(self.location.origin) && 'focus' in c) return c.focus();
      }
      return clients.openWindow('/');
    })
  );
});
