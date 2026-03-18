const CACHE_NAME = 'base-v1';

self.addEventListener('install', (event) => {
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((names) =>
			Promise.all(
				names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
			)
		).then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Never cache API calls
	if (url.pathname.startsWith('/api')) {
		return;
	}

	// Network-first for HTML, cache-first for assets
	if (event.request.mode === 'navigate') {
		event.respondWith(
			fetch(event.request)
				.then((response) => {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
					return response;
				})
				.catch(() => caches.match(event.request))
		);
	} else {
		event.respondWith(
			caches.match(event.request).then((cached) => {
				if (cached) return cached;
				return fetch(event.request).then((response) => {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
					return response;
				});
			})
		);
	}
});

self.addEventListener('push', (event) => {
	const data = event.data ? event.data.json() : { title: 'Base', body: 'Timer complete!' };
	event.waitUntil(
		self.registration.showNotification(data.title, {
			body: data.body,
			icon: '/icon-192.png'
		})
	);
});
