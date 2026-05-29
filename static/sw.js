// v3 — force le rechargement du cache
const CACHE = 'intentions-v3';

self.addEventListener('install', e => {
  // Ne pas précacher — évite de servir du HTML périmé
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  // Supprimer TOUS les anciens caches
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // Toujours réseau en premier, jamais de cache pour le HTML
  if (e.request.url.includes('/api/')) return;
  if (e.request.mode === 'navigate') {
    // Page HTML : toujours depuis le réseau
    e.respondWith(fetch(e.request));
    return;
  }
  // Autres assets : réseau avec fallback cache
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
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
      badge:   payload.badge || '/static/icon-192.png',
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
