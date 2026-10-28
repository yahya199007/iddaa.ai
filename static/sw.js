// Kendini silen Service Worker: eski önbelleği temizler ve kaydını kaldırır.
// Eski sürümden kalan bozuk/eski sayfa görünümünü ve takılan uygulamayı düzeltir.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach((c) => c.navigate(c.url));
  })());
});
// Fetch'i yakalamıyoruz: her istek doğrudan sunucudan gelir (güncel veri).
