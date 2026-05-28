self.addEventListener('install', (event) => {
    // Força a ativação imediata (não espera outras abas fecharem)
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    // Pega o controle imediatamente
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Apenas repassa a requisição para a rede (não faz cache de nada)
    event.respondWith(fetch(event.request));
});
