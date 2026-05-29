self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // PWA sem cache! Tudo passa direto para a rede.
    // Como roda localmente, o cache não é necessário e previne dores de cabeça.
    event.respondWith(fetch(event.request));
});
